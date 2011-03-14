#####################################################
# Reads the configuration file for the EC2 cloud
# (located at config/ec2bd.config)  and creates 
# several getter methods to retrieve the configuration
#####################################################
import ConfigParser

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
