import sys
import time
import os

import Timing
import SshUtils
import boto.ec2
from boto.ec2.connection import EC2Connection
from SequentialResourceSelectionPolicy import SequentialResourceSelectionPolicy
from PredictiveResourceSelectionPolicy import PredictiveResourceSelectionPolicy
import logging
import paramiko

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

    def __init__(self, resourceSpec, configurationManager, stats):
        self.profiler = Timing.timeprofile()
        self.profiler.mark("resource_mng_connect")
        #self.numOfMachines = numOfMachines
        self.keyPairFile = configurationManager.getKeyPairFile()

        #print 'Will reserve %s machines from EC2' % numOfMachines
        logging.debug("Private key file is %s" % self.keyPairFile)
        self.buildResourceSpec(resourceSpec)
        
        # Connect to Amazon EC2
        self.AWS_ACCESS_KEY_ID = configurationManager.getEC2AccessKeyId()
        self.AWS_SECRET_ACCESS_KEY = configurationManager.getEC2SecretAccessKey()
        
        logging.debug("Checking validity of private key %s." % self.keyPairFile)
        key= paramiko.RSAKey(None, None,self.keyPairFile,'', None, None)
        
	    # DAS4 endpoint
        region=boto.ec2.regioninfo.RegionInfo(name=configurationManager.getCloudRegion(),endpoint=configurationManager.getCloudUrl())
        
        # Connect to cloud
        if configurationManager.getCloudName()=='Amazon':
            print "Connecting to Amazon EC2..."
            self.EC2Connection = EC2Connection(aws_access_key_id=self.AWS_ACCESS_KEY_ID, 
                       aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                       region=region)
        else:
            print "Connecting to Eucalyptus Cloud...",
            self.EC2Connection = EC2Connection(aws_access_key_id=self.AWS_ACCESS_KEY_ID, 
                                               aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
                                               is_secure=False,
                                               region=region,
                                               port=configurationManager.getCloudPort(),
                                               path="/services/Eucalyptus")
        print "DONE"
        self.profiler.elapsed("resource_mng_connect")
       
        self.profiler.mark("resource_mng_change_region")
	
#        print "Connecting to Region ",regions[0],"...",
#        self.EC2Connection =regions[0].connect()
#        print "Done"
        # Retrieve available images from EC2
        self.profiler.mark("resource_mng_get_images")
        print "Retrieving all available images...",
        self.images = self.EC2Connection.get_all_images()
        print "DONE"
        self.profiler.elapsed("resource_mng_get_images")
	print "images are",self.images
        # Build a dictionary of all the available images on EC2
        self.buildAmiList()
        image = self.amiDict[configurationManager.getVMImage()]
        self.profiler.mark("wait_for_all_instances_to_get_running")

        # Run this specific image
        self.runInstances(image,configurationManager.getKeyPairFile())
        self.profiler.elapsed("wait_for_all_instances_to_get_running")
        self.resourceSelectionPolicy = SequentialResourceSelectionPolicy(self.instances)
#        self.resourceSelectionPolicy = PredictiveResourceSelectionPolicy(self.instances)
        print "Using policy " + self.resourceSelectionPolicy.getName()
        self.stats = stats
    
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
        self.amiDict={}
        for image in self.images:
            if image.id.count("emi") > 0:         
                self.amiDict[image.id] = image     
                    
    ###########################################
    # Run "image" on all the resources  that 
    # are described in the resource list        
    ###########################################     
    def runInstances(self, image,keypair):
        self.instances = []
        self.reservations = []
        
        # keep only the basename, remove absolute path
        keypair_basename=os.path.basename(keypair)
        
        # The keypair name without the ".private" extension 
        if '.private' in keypair_basename:
            keypair_basename=keypair_basename.split('.')[0]
            
        for instanceType,instanceCount in self.resourceList:
            print "Running image ",image," on ", instanceCount," instances of type ",instanceType
            instancesReserved = image.run(instanceCount, instanceCount, key_name=keypair_basename, instance_type=instanceType)
            self.instances = self.instances + instancesReserved.instances # merge all instances into self.instances
            self.reservations.append(instancesReserved)
        self.waitUntilAllInstancesAreRunning()
                        
                      
    def waitUntilAllInstancesAreRunning(self):
        print "Waiting for instances to boot..."
        sshOverhead = 0
        allInstances = len(self.instances)
        boolList = [] # holds the flags whether the instances are running
        for i in range(allInstances):
            boolList.append(False)
        while True:
            for j in range(allInstances):
                instance = self.instances[j]
                if instance.state != 'running' or instance.dns_name=="0.0.0.0":
                    instance.update()
                    time.sleep(0.2)
                    #print instance.id + " -> " +instance.state
                else: # running
#                    try:
#                        self.profiler.timedict["wait_for_all_instances_to_get_running_ssh_overhead"]
#                    except KeyError:
#                        self.profiler.mark("wait_for_all_instances_to_get_running_ssh_overhead")
                    start = time.time()
                    print "Connecting to instance ", instance.dns_name,
                    sshUtils = SshUtils.SshUtils(instance.dns_name,'root','amazon',self.keyPairFile)
                    connected = sshUtils.doConnect()
                    if connected:
                        print "DONE"
                    else:
                        print "Unsuccessful"
                    # Connect to SSH to all machines , execute a 
                    # simple command to see if they are working
                    # and then exit
                    if connected:
                        executed = sshUtils.executeCommand('uname -a')
                        sshUtils.disconnect()
                        boolList[j] = executed
#                    self.profiler.elapsed("wait_for_all_instances_to_get_running_ssh_overhead")      
                    end = time.time()
                    sshOverhead += (end-start)
            if self.allTrue(boolList) == True:
                break
        print "All instances are running"
        # !
        self.profiler.timedict["wait_for_all_instances_to_get_running_ssh_overhead"]= sshOverhead

    def allTrue(self,boolList):
        flag = boolList[0];
        for b in boolList:
            flag = flag and b
        return flag

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
                    #print instance.id + " -> " +instance.state
                else: # running
                    boolList[j] = True
            if self.allTrue(boolList) == True:
                break
                             
    def terminateAllInstances(self):
        self.profiler.mark("wait_for_all_instances_to_get_terminated")
        print "Terminating all instances...",
        for resv in self.reservations:
            resv.stop_all()
        self.waitUntilAllInstancesAreStopped()
        print "DONE"
        self.profiler.elapsed("wait_for_all_instances_to_get_terminated")
        
# def forceTerminationOfAllInstances(self):
#     allReservations = self.EC2Connection.get_all_instances()
#    for reservation in allReservations:
#       for instance in reservation.instances:
#          print instance.id + " -> " +instance.state
#         instance.stop()
                
    def dumpAllInstances(self):
        allReservations = self.EC2Connection.get_all_instances()
        for reservation in allReservations:
            for instance in reservation.instances:
                print instance.id + " -> " +instance.state
                
    def getResourcePolicyName(self):
        return self.resourceSelectionPolicy.getName()
                
    def getNextAvailableInstance(self):
        nextInstance = self.resourceSelectionPolicy.getNextResource()
        return (nextInstance.dns_name, nextInstance.id)

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
        self.stats.addToTotalResourceReleaseTime(self.profiler.getValue('wait_for_all_instances_to_get_terminated'))
        self.stats.addTotalSshOverheadWhilePollingIfResourcesAreRunning(self.profiler.getValue('wait_for_all_instances_to_get_running_ssh_overhead'))
