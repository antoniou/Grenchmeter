import sys
import time
import os
import operator

import xmlrpclib
import Timing
import boto.ec2
from boto.ec2.connection import EC2Connection
from SequentialResourceSelectionPolicy import SequentialResourceSelectionPolicy
from PredictiveResourceSelectionPolicy import PredictiveResourceSelectionPolicy
from LoadBalancingResourceSelectionPolicy  import LoadBalancingResourceSelectionPolicy
import logging
import paramiko
import ConfigurationManager
import VMInstance


class ResourceManager:
#===============================================================================
#    BIG: c1.xlarge, c1.medium, m1.large, m1.xlarge
# 
# IMAGE    ami-36ff1a5f 
# ec2-public-images/fedora-core6-base-x86_64.manifest.xml     amazon 
# available    public        x86_64    machine
# 
# 
# non-64 bit: m1.small
# 
# IMAGE    ami-2bb65342    ec2-public-images/getting-started.manifest.xml     
# amazon     available    public        i386    machine
#===============================================================================

    INSTANCE_FILE_NAME = './instances.in' 
    def __init__(self, resourceSpec, configurationManager, stats):
        
        self.initialization()     
        self.connectToCloud()
        if self.instancesFileExists():
            self.loadInstancesFromFile(self.runningInstancesFile)
                
        image = self.buildAmiList()
        self.profiler.mark("wait_for_all_instances_to_get_running")

        # Run this specific image
        self.runInstances(image, configurationManager.getKeyPairFile())
        self.profiler.elapsed("wait_for_all_instances_to_get_running")
        
        self.calcNumOfComputingUnits()
        
        print "NUMBER OF INSTANCES=",len(self.vmInstances.values())
        self.resourceSelectionPolicy = SequentialResourceSelectionPolicy(self.vmInstances.values())
#        self.resourceSelectionPolicy = LoadBalancingResourceSelectionPolicy(self.vmInstances.values())
#        self.resourceSelectionPolicy = PredictiveResourceSelectionPolicy(self.instances)
        print "Using policy " + self.resourceSelectionPolicy.getName()
        self.stats = stats
        
    def initialization(self):
        self.profiler = Timing.timeprofile()
        self.profiler.mark("resource_mng_connect")
        self.configurationManager =configurationManager
        
        self.keyPairFile = configurationManager.getKeyPairFile()
        self.VmInstanceUser = configurationManager.getVmInstanceUser()
        logging.debug("Private key file is %s" % self.keyPairFile)
        self.buildResourceSpec(resourceSpec)
        
        # Connect to Amazon EC2
        self.AWS_ACCESS_KEY_ID = configurationManager.getEC2AccessKeyId()
        self.AWS_SECRET_ACCESS_KEY = configurationManager.getEC2SecretAccessKey()
        
        logging.debug("Checking validity of private key %s." % self.keyPairFile)
        key= paramiko.RSAKey(None, None,self.keyPairFile,'', None, None)
        
        self.instances = []
        self.vmInstancesList = []
        self.vmInstances = {}
        self.runningInstancesDic = { 'm1.small':0, 'c1.medium':0,'m1.large':0,'m1.xlarge':0,'c1.xlarge':0 }
        self.runningInstancesFile = configurationManager.getRunningInstancesFile()
        self.instanceWriteCount = 1
        
    def instancesFileExists(self):
        if self.runningInstancesFile is None:
            return False
        if not os.path.exists(self.runningInstancesFile):
            return False
        
        return True
    
    def calcNumOfComputingUnits(self):
        self._totalComputingUnits = 0
        for vm in self.vmInstances.values():
            self._totalComputingUnits += vm.getNumberOfComputingUnits()
            
    def getNumberOfComputingUnits(self):
        return self._totalComputingUnits
        
    def connectToCloud(self):
        cloudName = self.configurationManager.getCloudName()
        if cloudName == 'Amazon':
            connectToAmazonEC2()
        elif cloudName == "Eucalyptus":
            connectToEucalyptus()
        elif cloudName == "OpenNebula":
            connectToOpenNebula()
        else:
            print "ERROR: Wrong Cloud name: {0}".format(cloudName)
            
        self.profiler.elapsed("resource_mng_connect")
        self.profiler.mark("resource_mng_change_region")
        self.profiler.mark("resource_mng_get_images")     
        
    def connectToAmazonEC2(self):
        print "Connecting to Amazon EC2:"
        self.EC2Connection = boto.ec2.connect_to_region(self.configurationManager.getCloudRegion(),
                                                            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
                                                            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY)
    def connectToEucalyptus(self):
        region=boto.ec2.regioninfo.RegionInfo(name=self.configurationManager.getCloudRegion(),endpoint=self.configurationManager.getCloudUrl())
        print "Connecting to Eucalyptus Cloud: "
        self.EC2Connection = EC2Connection(aws_access_key_id=self.AWS_ACCESS_KEY_ID, 
                                               aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                                               is_secure=False,
                                               region=region,
                                               port=self.configurationManager.getCloudPort(),
                                               path="/services/Eucalyptus")
            
    def connectToOpenNebula(self):
        self.EC2Connection = xmlrpclib.ServerProxy('http://localhost:2633/RPC2')
        
    ###########################################
    # Construct specification of resources, based on a 
    # comma-separated list of "attribute=value"
    ###########################################      
    def buildResourceSpec(self, resSpecString):
        listOfStrings = resSpecString.split(',')
        self.resourceList = []
        for rspec in listOfStrings:
            instanceType, instanceCount = rspec.split('=')
            self.resourceList.append((instanceType,int(instanceCount)))
    
    ##########################################
    # Build a DICTIONARY (not a list) of all the
    # available images on Amazon EC2
    ###########################################
    def buildAmiList(self):
        """ Build a dictionary of all the available images on EC2 """
        print "\tRetrieving all available images..."
        images = self.EC2Connection.get_all_images()
        self.profiler.elapsed("resource_mng_get_images")
        amiDict={}
        for image in images:
            if image.id.count("emi") > 0 or image.id.count("ami") > 0:         
                amiDict[image.id] = image
                     
        return amiDict[self.configurationManager.getVMImage()]
                    
    ###########################################
    # Run "image" on all the resources  that 
    # are described in the resource list        
    ###########################################     
    def runInstances(self, image,keypair):
        self.reservations = []
        
        # keep only the basename, remove absolute path
        keypair_basename=os.path.basename(keypair)
        
        # The keypair name without the ".private" extension 
        if '.priv' in keypair_basename or '.pem' in keypair_basename:
            keypair_basename=keypair_basename.split('.')[0]
        
        for instanceType,instanceCount in self.resourceList:
            if instanceCount > self.runningInstancesDic[instanceType]:
                instanceCount -= self.runningInstancesDic[instanceType]
                if instanceCount > 0:
                    print "\tRunning image ",image," on ", instanceCount," instances of type ",instanceType
                    instancesReserved = image.run(instanceCount, instanceCount, key_name = keypair_basename, instance_type=instanceType)
                    self.instances += instancesReserved.instances # merge all instances into self.instances
                    self.reservations.append(instancesReserved)

        for instance in self.instances:
            vmInstance = VMInstance.VMInstance(instance, self.configurationManager)
            self.vmInstancesList.append(vmInstance)
           
        self.waitUntilAllInstancesAreRunning()
        
        for instance in self.vmInstancesList:
            print "Adding INSTANCE:",instance.getDNSName()
            self.vmInstances[instance.getDNSName()] = instance
        
        
    def waitUntilAllInstancesAreRunning(self):
        print "\tWaiting for instances to boot:"
        sshOverhead = self.connectToInstances()
        print "\tDone booting"
        
        self.profiler.timedict["wait_for_all_instances_to_get_running_ssh_overhead"]= sshOverhead
        
    def connectToInstances(self):
        connected = [False for i in range(len(self.vmInstancesList))]
        sshOverhead = 0
        while True:
            instanceList = self.vmInstancesList
            for i in range(len(instanceList)):
                if connected[i] is True:
                    continue
                
                start = time.time()
                connected[i] = instanceList[i].connect()
                end = time.time()
                sshOverhead += (end-start)
                 
            if reduce(operator.and_, connected) is True:
                break
            
        return sshOverhead
    
    def terminateAllInstances(self):
        self.profiler.mark("wait_for_all_instances_to_get_terminated")
        print "!STATUS: Terminating all instances...",
        for resv in self.reservations:
            resv.stop_all()
        self.waitUntilAllInstancesAreStopped()
        print "DONE"
        self.profiler.elapsed("wait_for_all_instances_to_get_terminated")
        
    def waitUntilAllInstancesAreStopped(self):
        allInstances = len(self.instances)
        boolList = [] # holds the flags whether the instances are running
        for i in range(allInstances):
            boolList.append(False)
        while True:
            for j in range(allInstances):
                instance = self.instances[j]
                if instance.state != 'terminated':
                    instance.update()
                    time.sleep(0.2)
                else: # running
                    boolList[j] = True
            if self.allTrue(boolList) == True:
                break
                             
        
    def loadInstancesFromFile(self,fileName):
        instanceFileReader = ConfigurationManager.InstanceFileReader(self.configurationManager)
        vmInstances = instanceFileReader.getVMInstancesFromFile(fileName)
        for instance in vmInstances:
            self.runningInstancesDic[instance.getType()] += 1 
            self.instances.append(instance.toEC2Instance())
            self.vmInstancesList.append(instance)
            
        print "Created {0} instances from file...".format(len(self.vmInstancesList))
            
    def dumpAllInstances(self):
        allReservations = self.EC2Connection.get_all_instances()
        for reservation in allReservations:
            for instance in reservation.instances:
                print instance.id + " -> " +instance.state
                
    def getNextAvailableInstance(self):
#        return (nextInstance.dns_name, nextInstance.id)
        return self.resourceSelectionPolicy.getNextResource()

    def getIdleInstance(self):
        for instance in self.vmInstances.values():
            print "Number of jobs in instance {0} : {1}".format(instance.getID(),instance.getNumExecutingJobs())
            if instance.getNumExecutingJobs() == 0:
                return instance
        return None 
    
    def decreaseAwaitingJobs(self,instanceDNS):
        instance = self.vmInstances[instanceDNS]
        instance.decreaseNumExecutingJobs()
        return instance.getNumExecutingJobs()
        
    def updateResourcePolicyStatus(self, instanceId, status):
        try:
            self.resourceSelectionPolicy.updateResourceState(instanceId,status)
        except:
            #The updateResourcePolicyStatus is not made available with the chosen ResourcePolicy
            pass
    
    def submitStatistics(self):
        self.stats.addToTotalResourceManagerConnectTime(self.profiler.getValue('resource_mng_connect'))
        self.stats.addToTotalResourceManagerGetListOfImagesTime(self.profiler.getValue('resource_mng_get_images'))
        self.stats.addToTotalResourceReservationTime(self.profiler.getValue('wait_for_all_instances_to_get_running'))
        self.stats.addTotalSshOverheadWhilePollingIfResourcesAreRunning(self.profiler.getValue('wait_for_all_instances_to_get_running_ssh_overhead'))
#        self.stats.addToTotalResourceReleaseTime(self.profiler.getValue('wait_for_all_instances_to_get_terminated'))


    def writeInstancesToFile(self):
        fileName = self.runningInstancesFile
        if fileName is None:
            fileName = ResourceManager.INSTANCE_FILE_NAME
        inFile = open(fileName,'w')
        for instance in self.vmInstances.values():
            self.writeInstance(instance,inFile)
        inFile.close()
        
        
    def writeInstance(self,instance,file):
        file.write("[Instance{0}]\n".format(self.instanceWriteCount))
        file.write("ip_address = {0}\n".format(instance.getIPAddress()))
        file.write("dns_name = {0}\n".format(instance.getDNSName()))
        file.write("id = {0}\n".format(instance.getID()))
        file.write("image_id = {0}\n".format(instance.getImageID()))
        file.write("type = {0}\n\n".format(instance.getType()))
        self.instanceWriteCount += 1
        