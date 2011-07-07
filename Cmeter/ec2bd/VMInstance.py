import time
import threading

import boto.ec2
import SshUtils
import OneInfo

instanceComputingUnitsDic = { 'm1.small':1, 'c1.medium':2,'m1.large':2,'m1.xlarge':4,'c1.xlarge':2 }
class VMInstance:
    def __init__(self, configurationManager):
        self.instanceUser = configurationManager.getVmInstanceUser()
        self.keypairFile = configurationManager.getKeyPairFile()
        self.sshUtils = None 
        self.jobsInInstance = 0
        self.lock = threading.Lock()

    def connect(self):
        pass
    
    def execute(self,command, resultsExpected):
        pass
    
    def getNumberOfComputingUnits(self):
        pass
    
    def getID(self):
        pass
    
    def getIPAddress(self):
        pass
    
    def getDNSName(self):
        pass
    
    def getType(self):
        pass
    
    def getImageID(self):
        pass
    
    def getState(self):
        pass 
    
    def update(self):
        pass
    
    def increaseNumExecutingJobs(self):
        self.lock.acquire()
        try:
            self.jobsInInstance += 1
        finally:
            self.lock.release()
    
    def decreaseNumExecutingJobs(self):
        self.lock.acquire()
        try:
            self.jobsInInstance -= 1
        finally:
            self.lock.release()
            
    def getNumExecutingJobs(self):
        return self.jobsInInstance
    
    def execute(self, command, resultsExpected = True):
        commandSent = self.sshUtils.executeCommand(command)
        MAX_RESETS = 1
        reset = 0
        while not commandSent and reset <= MAX_RESETS:
            self.sshUtils.reset()
            reset += 1
            commandSent = self.sshUtils.executeCommand(command)
        
        if resultsExpected is True and commandSent is True:
            self.increaseNumExecutingJobs()
                
        return commandSent
    
    def disconnect(self):
        self.sshUtils.disconnect()
        
class EC2Instance(VMInstance):
    def __init__(self,EC2Instance, configurationManager, id = None,imageID = None ,ipAddress = None,dnsName = None,type = "m1.small"):
        VMInstance.__init__(self, configurationManager)
        if EC2Instance is None:
            self.ec2Instance = boto.ec2.instance.Instance()
            self.ec2Instance.id = id
            self.ec2Instance.image_id = imageID
            self.ec2Instance.ip_address = ipAddress
            self.ec2Instance.dns_name = dnsName
            self.ec2Instance.state = "running"
            self.ec2Instance.instance_type = type
        else:
            self.ec2Instance = EC2Instance
        
        self.numberOfComputingUnits = instanceComputingUnitsDic[self.ec2Instance.instance_type]

            
    def getState(self):
        return self.ec2Instance.state
    
    def getDNSName(self):
        return self.ec2Instance.dns_name
    
    def getIPAddress(self):
        return self.ec2Instance.ip_address
    
    def getID(self):
        return self.ec2Instance.id
    
    def getImageID(self):
        return self.ec2Instance.image_id
        
    def getType(self):
        return self.ec2Instance.instance_type 
    
    def toEC2Instance(self):
        return self.ec2Instance
    
    def update(self):
        self.ec2Instance.update()
        
    def connect(self):
        
        if self.ec2Instance.state != 'running' or self.ec2Instance.dns_name=="0.0.0.0":
            self.update()
            time.sleep(0.2)
        else:
            print "\t\tConnecting to instance {0}...".format(self.ec2Instance.dns_name),
            self.sshUtils = SshUtils.SshUtils(self.ec2Instance.dns_name, self.instanceUser,'amazon',self.keypairFile) 
            connected = self.sshUtils.doConnect()
            if connected:
                print "Done"
                executed = self.execute('uname -a', False)
                return executed
            else:
                print "Unsuccessful"
                
        return False
    
    def getNumberOfComputingUnits(self):
        return self.numberOfComputingUnits
    
class OneInstance(VMInstance):
    def __init__(self, configurationManager, oneConnection,type= "m1.small"):
        VMInstance.__init__(self, configurationManager)
        self.oneConnection = oneConnection
        self.credentials="antoniou:43115424d464f14c6c68b79074531f71d51bdf9c"
        self.oneParser = OneInfo.OneInfoParser(self.oneConnection,self.credentials)
        #TODO state 3---> "running"?
        self.state = None
        self.ipAddress = None
        self.dnsName = None
        self.imageID = None
        self.type = type
        self.numberOfComputingUnits = instanceComputingUnitsDic[self.type]
    def update(self):
        self.state, self.ipAddress, self.id = self.oneParser.getOneInfo(self.imageID) 
        # TODO : dns name?
        self.dnsName = self.ipAddress
        
    def run(self, imageTemplate):
        s=open(imageTemplate,'r').read()
        print s
        vm=self.oneConnection.one.vm.allocate(self.credentials,s)
        self.imageID = vm[1]
        
    def connect(self):
        if self.state != 3:
            self.update()
            time.sleep(0.2)
        else:
            print "\t\tConnecting to instance {0}...".format(self.dnsName),
            self.sshUtils = SshUtils.SshUtils(self.dnsName, self.instanceUser,'amazon',self.keypairFile) 
            connected = self.sshUtils.doConnect()
            if connected:
                print "Done"
                executed = self.execute('uname -a', False)
                return executed
            else:
                print "Unsuccessful"
                
        return False
    
    def getState(self):
        self.update()
        return self.state
    
    def getID(self):
        return self.id
    
    def getIPAddress(self):
        return self.ipAddress
    
    def getDNSName(self):
        return self.dnsName
    
    def getImageID(self):
        return self.imageID
       
    def getType(self):
        return self.type   
    
    def getNumberOfComputingUnits(self):
        return self.numberOfComputingUnits     
        
