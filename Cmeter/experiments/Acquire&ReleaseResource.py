import sys
import getopt
import time

if "../rm" not in sys.path:
    sys.path.append("../rm")    

if "..//utils" not in sys.path:
    sys.path.append("..//utils")

if "..//ec2bd" not in sys.path:
    sys.path.append("..//ec2bd")

import ConfigurationManager
import ResourceManager
import Statistics
from GnuplotUtils import plotStatistics
from ResourceStatistics import *
    
def main(argv):
    stats = Statistics.Statistics()
    acquireStats = ResourceStatistics('acquire.dat')
    releaseStats = ResourceStatistics('release.dat')
    configurationManager = ConfigurationManager.ConfigurationManager("C:\\workspace\\Ec2Benchmark\\config\\ec2bd.config")
#    resourceAcquireStats = []
#    resourceReleaseStats = []
    for i in range(1,21):
        acquireList = []
        releaseList = []
        try:
            resourceManager = ResourceManager.ResourceManager(str(i), \
                                          configurationManager.getEC2AccessKeyId(),\
                                          configurationManager.getEC2SecretAccessKey(), stats, configurationManager.getKeyPairFile())
        except:
            print "error occured for i = %d " % i
            print sys.exc_info()
            continue
        acquireTime = resourceManager.profiler.getValue('wait_for_all_instances_to_get_running')
        sshOverhead = resourceManager.profiler.getValue('wait_for_all_instances_to_get_running_ssh_overhead')
#        acquireList.append([i,sshOverhead,acquireTime])
        resourceManager.terminateAllInstances()
        releaseTime = resourceManager.profiler.getValue('wait_for_all_instances_to_get_terminated')
#        releaseList.append([i,releaseTime])
        #resourceAcquireStats.append(acquireList)
        #resourceReleaseStats.append(releaseList)
        acquireStats.addStats([i,sshOverhead,acquireTime])
        releaseStats.addStats([i,releaseTime])
    acquireStats()
    releaseStats()
    #plotStatistics(resourceAcquireStats, "Resource Acquisition Time vs Number of Machines", "acquire.ps", "Resource Acquisition Time (s)")
    #plotStatistics(resourceReleaseStats, "Resource Release Time vs Number of Machines", "release.ps", "Resource Release Time (s)")
if __name__ == "__main__":
    main(sys.argv[1:])