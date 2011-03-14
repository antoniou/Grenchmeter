import sys
import socket 
import time

import JobSubmitter
import StatsUpdater
from PersistentStatistics import *

class CommandListener:
    def __init__(self, port, poolManager,resourceManager, configurationManager, databaseStatistics):
        self.port = int(port)
        self.poolManager = poolManager
        self.resourceManager = resourceManager
        self.configurationManager = configurationManager
        self.stats = databaseStatistics
        self.statsReceived = 0
        self.filesReceived = 0

    def startListener(self):
        print 'Listening on port %d...' % self.port,
        host=''
        backlog = 10000
        size = 1024*2
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host,int(self.port)))
        self.socket.listen(backlog)
        print "DONE"
        while 1:
            client, address = self.socket.accept()
            data = client.recv(size)
            jobSubmissionTime = time.time()
            if not data.startswith("cmd:"): 
                self.filesReceived += 1
                fileName = data
                jobSubmitter = JobSubmitter.JobSubmitter(fileName, self.resourceManager, self.configurationManager, self.stats,jobSubmissionTime) # new submitter 
                self.poolManager.processJob(jobSubmitter)
                print " Received files <%d>" % self.filesReceived
            else: # a command is received
                print "Received: ", data
                cmd = data.split("cmd:")[1]
                cmd = cmd.split(',')[0]
                if cmd == "stop":
                    print "Terminate command received. Stopping daemon..."
                    self.poolManager.shutdown()
                    self.resourceManager.terminateAllInstances()
                    time.sleep(2)
                    #self.resourceManager.dumpAllInstances()
                    self.resourceManager.submitStatistics()
#                    self.stats.printStatistics()
                    self.stats.dumpStatisticsToDb()
                    self.socket.close()
                    sys.exit(0)
                else:
                    self.statsReceived += 1
                    statsUpdateThread = StatsUpdater.StatsUpdater(data, self.stats, self.resourceManager)
                    self.poolManager.processJob(statsUpdateThread)
                    print "stats <%d>" % self.statsReceived
