import sys
import getopt
import os
import threading
import time
import pickle

if "Cmeter/rm" not in sys.path:
    sys.path.append('Cmeter/rm/')    
if "Cmeter/utils" not in sys.path:
    sys.path.append("Cmeter/utils")
if "Cmeter/jsdl" not in sys.path:
    sys.path.append("Cmeter/jsdl")
if "Cmeter/workerpool" not in sys.path:
    sys.path.append("Cmeter")
          
import logging
import ConfigurationManager
import ResourceManager
import ThreadPoolManager
import CommandListener
import Statistics
import PersistentStatistics

class Cmeter(threading.Thread):
    def __init__(self,configFile):
        threading.Thread.__init__(self)
        self.configFile = configFile
        print "Cmeter configuration file: %s" % configFile
        self.status = "init"
        # Read the configuration file/ create getters to retrieve the conf. options
        self.configurationManager = ConfigurationManager.ConfigurationManager(self.configFile)
    
        # Start logging
        # logging.basicConfig(filename=configurationManager.getLogFileName(),level=logging.DEBUG)
        # Initialize statistic gathering
        self.stats = Statistics.Statistics()
        
        self.databaseStatistics = PersistentStatistics.DatabaseStatistics()
        self.databaseStatistics.init_statistics_tables()
        
        self.poolManager = ThreadPoolManager.ThreadPoolManager(self.configurationManager.getNumberOfThreadsInPool())
        
        # Specifies the type of machines that will be allocated on the cloud (e.g. m1.small)    
        self.resourceSpec = self.configurationManager.getResourceSpec()
        
    def run(self):
        
        # Acquire VM instances on host cloud
        self.resourceManager = ResourceManager.ResourceManager(self.resourceSpec, self.configurationManager, self.stats)
                                          
        self.commandListener = CommandListener.CommandListener(self.configurationManager.getEc2BdPort(),\
                                                          self.poolManager,self.resourceManager,\
                                                          self.configurationManager, self.databaseStatistics,self)
    
        self.commandListener.startListener()
        
        sys.exit(0)
        
    def initDaemon(self):
        self.start()
        while not self.isStatus("ready"):
            time.sleep(1)
            
    def getStatus(self):
        return self.status
    
    def setStatus(self,status):
        self.status = status
        
    def isStatus(self,status):
        return self.getStatus() == status
    
    def stopDaemon(self):
        print "Terminate command received. Stopping daemon..."
        self.setStatus("stopping")
        self.poolManager.shutdown()
        if self.configurationManager.terminateVMInstances():
            self.resourceManager.terminateAllInstances()
        else:
            self.resourceManager.writeInstancesToFile()
        time.sleep(1)
        #self.resourceManager.dumpAllInstances()
        self.resourceManager.submitStatistics()
        #self.stats.printStatistics()
        #  self.databaseStatistics.dumpStatisticsToDb(dedicatedMode)
        self.commandListener.stopListener()
        os.system('pkill -9 -u antoniou  python')
        sys.exit(0)
        
    def storeStatsToDB(self, databaseName = None):
        print "Store command received."
        self.resourceManager.submitStatistics()
        dbName = self.databaseStatistics.dumpStatisticsToDb(databaseName)
        self.databaseStatistics.clearStats()
        return dbName
    
    def storeDedStatsToDB(self, databaseName = None):
        print "Store Dedicated Stats command received."
        dbName = self.databaseStatistics.dumpDedStatisticsToDb(databaseName)
        return dbName
            
def main(argv):
    configFile = "config/default.config"  
    opts, args = getopt.getopt(argv, "c:", ["config="])
    for opt, arg in opts:   
        if opt in ("-c", "--config"):
            configFile = arg
    
    cmeter = Cmeter(configFile)
    cmeter.start()
    
if __name__ == "__main__":
    main(sys.argv[1:])
