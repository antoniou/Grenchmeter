import sys
import getopt
import os

if "./rm" not in sys.path:
    sys.path.append('rm/')    
if "./utils" not in sys.path:
    sys.path.append("./utils")
if "./jsdl" not in sys.path:
    sys.path.append("./jsdl")
if "./workerpool" not in sys.path:
    sys.path.append(".")      
import logging
import ConfigurationManager
import ResourceManager
import ThreadPoolManager
import CommandListener
import Statistics
import PersistentStatistics

#import paramiko
    
def main(argv):  
    opts, args = getopt.getopt(argv, "c:", ["config="])
    for opt, arg in opts:   
        if opt in ("-c", "--config"):
            configFile = arg
            print "Reading configuration %s" % configFile

    #paramiko.util.log_to_file("ssh_logs.txt", paramiko.util.DEBUG)
    
    # Initialize statistic gathering
    stats = Statistics.Statistics()
    PersistentStatistics.init_statistics_tables()
    databaseStatistics = PersistentStatistics.DatabaseStatistics()
    
    # Read the configuration file/ create getters to retrieve the conf. options
    configurationManager = ConfigurationManager.ConfigurationManager(configFile)
    
    logging.basicConfig(filename=configurationManager.getLogFileName(),level=logging.DEBUG)
    
    poolManager = ThreadPoolManager.ThreadPoolManager(configurationManager.getNumberOfThreadsInPool())

    # Specifies the type of machines that will be allocated on the cloud (e.g. m1.small)    
    resourceSpec = configurationManager.getResourceSpec()
    
    # Acquire VM instances on host cloud
    resourceManager = ResourceManager.ResourceManager(resourceSpec, configurationManager, stats)
                                      
    commandListener = CommandListener.CommandListener(configurationManager.getEc2BdPort(),\
                                           poolManager,resourceManager, configurationManager, databaseStatistics)

    commandListener.startListener()
    
if __name__ == "__main__":
    main(sys.argv[1:])
