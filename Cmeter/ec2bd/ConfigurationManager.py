#####################################################
# Reads the configuration file for the EC2 cloud
# (located at config/ec2bd.config)  and creates 
# several getter methods to retrieve the configuration
#####################################################
import ConfigParser
import VMInstance

import operator
import time

class ConfigurationManager:
    def __init__(self, configFile):
        self.configSection = 'Configuration'
        self.config = ConfigParser.ConfigParser()
        self.config.read(configFile)
        
    def getHttpServerBase(self):
        return self.config.get(self.configSection, "Http_Server_Base")
    
    def getHttpServerBaseUrl(self):
        return self.config.get(self.configSection, "Http_Server_Base_Url")
    
    def getNumberOfThreadsInPool(self):
        return self.config.get(self.configSection, "Num_Of_Threads_In_Pool")
    
#    def getNumberOfMachinesToAllocate(self):
#        return self.config.get(self.configSection, "Num_Of_Machines_To_Allocate")
    
    def getEC2AccessKeyId(self):
        return self.config.get(self.configSection, "EC2_Access_Key_Id")
    
    def getEC2SecretAccessKey(self):
        return self.config.get(self.configSection, "EC2_Secret_Access_Key")
       
    def getEc2BdPort(self):
        return self.config.get(self.configSection, "Port")
    
    def getKeyPairFile(self):
        return self.config.get(self.configSection, "KEYPAIR_File")
    
    def getResourceSpec(self):
        return self.config.get(self.configSection, "Resource_Specification")
              
    def getCmeterDaemonUrl(self):
        return self.config.get(self.configSection, "Cmeter_Daemon_Url")
    
    def getVmInstanceUser(self):
        return self.config.get(self.configSection, "VM_Instance_User")
    
    def getLogFileName(self):
        return self.config.get(self.configSection, "Log_File_Name")
    
    def getCloudUrl(self):
        return self.config.get(self.configSection, "Cloud_Url")
    
    def getCloudPort(self):
        return int(self.config.get(self.configSection, "Cloud_Port"))
    
    def getVMImage(self):
        return self.config.get(self.configSection, "VM_Image")
    
    def getCloudRegion(self):
        return self.config.get(self.configSection, "Cloud_Region")
    
    def getCloudName(self):
        return self.config.get(self.configSection, "Cloud_Name")
    
    def getEmail(self):
        return self.config.get(self.configSection, "Email")
    
    def getRunningInstancesFile(self):
        try:
            return self.config.get(self.configSection, "Running_Instances_File")
        except:
            return None
    
    def terminateVMInstances(self):
        try:
            value = self.config.get(self.configSection,"Terminate_VM_Instances").lower()
        except:
            return True
            
        if value == 'false':
            return False
        elif value == 'true':
            return True
        else:
            print "Invalid value for TerminateVMInstances configuration. Setting to default:True"
            return True
        
class InstanceFileReader:
    def __init__(self,configurationManager):
        self.config = ConfigParser.ConfigParser()
        self.instanceCount = 1
        self.configurationManager = configurationManager
        
    def getID(self,section):
        return self.config.get(section, "id")

    def getImageID(self,section):
        return self.config.get(section, "image_id")
    
    def getIPAddress(self,section):
        return self.config.get(section, "ip_address")
    
    def getType(self,section):
        try:
            return self.config.get(section, "type")
        except:
            return None
    
    def getDNSName(self,section):
        return self.config.get(section, "dns_name")

    def getVMInstancesFromFile(self,fileName):
        self.config.read(fileName)
        instances = []
        while True:
            try:
                instances.append(self.getNextInstance())
            except :
                break
        return instances
    
    def getNextInstance(self):
        section = "Instance{0}".format(self.instanceCount)
        id = self.getID(section)
        imageID = self.getImageID(section)
        ipAddress = self.getIPAddress(section)
        dnsName = self.getDNSName(section)
        type = self.getType(section)
        if type == None:
            instance = VMInstance.VMInstance(None,self.configurationManager,id, imageID, ipAddress, dnsName)
        else:
            instance = VMInstance.VMInstance(None,self.configurationManager,id, imageID, ipAddress, dnsName, type)

        self.instanceCount+=1
        return instance
