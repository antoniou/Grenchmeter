import time
import threading

import boto.ec2
import SshUtils


instanceComputingUnitsDic = { 'm1.small':1, 'c1.medium':2,'m1.large':2,'m1.xlarge':4,'c1.xlarge':2 }

class VMInstance:
    def __init__(self,EC2Instance, configurationManager, id = None,imageID = None ,ipAddress = None,dnsName = None,type = "m1.small"):
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
        self.instanceUser = configurationManager.getVmInstanceUser()
        self.keypairFile = configurationManager.getKeyPairFile()
        self.sshUtils = None 
        self.jobsInInstance = 0
        self.lock = threading.Lock()

    def getNumberOfComputingUnits(self):
        return self.numberOfComputingUnits
            
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
        
    def connect(self):
        
        if self.ec2Instance.state != 'running' or self.ec2Instance.dns_name=="0.0.0.0":
            self.ec2Instance.update()
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
            
    def disconnect(self):
        self.sshUtils.disconnect()
        
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
