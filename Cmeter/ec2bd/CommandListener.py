import sys
import socket 
import time
import threading

import JobSubmitter
import StatsUpdater
from PersistentStatistics import *
from Queue import Queue

class CommandListener:
    def __init__(self, port, poolManager,resourceManager, configurationManager, databaseStatistics, Cmeter):
        self.port = int(port)
        self.poolManager = poolManager
        self.resourceManager = resourceManager
        self.configurationManager = configurationManager
        self.stats = databaseStatistics
        self.listenerStatus = True
        self.globalVars = { 'statsReceived':0, 'filesReceived':0, 'awaitingResults':0}
        self.timeout = 10
        self.waitingQueue = Queue()
        self.Cmeter = Cmeter
        self.lock = threading.Lock()
    def stopListener(self):
            self.listenerStatus = False
            self.socket.close()
            
    def startListener(self):
        print 'Listening on port %d...' % self.port,
        host=''
        backlog = 10000
        size = 1024*2
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host,int(self.port)))
        self.socket.listen(backlog)
        self.socket.settimeout(self.timeout)
        print "DONE"
        self.Cmeter.setStatus("ready")
        while self.listenerStatus:
            try:
                client, address = self.socket.accept()
            except:
                continue
            
            data = client.recv(size)
            data=data.split()
            
            s = serveRequest(self.poolManager, self.resourceManager, self.configurationManager,\
                             self.stats, self.Cmeter, self.waitingQueue, self.globalVars, self.lock,\
                             data, address)
            s.start()
    
class serveRequest(threading.Thread):
    def __init__(self, poolManager,resourceManager,configManager,stats,Cmeter, waitingQueue, globalVars, lock, data, address):
        threading.Thread.__init__(self)
        self.poolManager = poolManager
        self.resourceManager = resourceManager
        self.configurationManager = configManager
        self.stats = stats
        self.Cmeter = Cmeter
        self.waitingQueue = waitingQueue
        self.globalVars = globalVars
        self.lock = lock
        self.data = data
        self.address = address
        
    def run(self):
        
        if not self.data[0].startswith("cmd:"): 
            self.lock.acquire()
            try:
                self.globalVars['filesReceived'] += 1
            finally:
                self.lock.release()
                
            fileName = self.data[0]
            dedicatedMode = self.isDedicated(self.data)
            jobSubmissionTime = time.time()
            jobSubmitter = JobSubmitter.JobSubmitter(fileName, self.resourceManager, self.configurationManager,\
                                                     self.stats, jobSubmissionTime,dedicatedMode)
            self.printIncomingRequest(jobSubmitter.getJobDescription(),dedicatedMode)
            if dedicatedMode:
                self.processDedicatedRequest(jobSubmitter)
            else:
                self.poolManager.processJob(jobSubmitter)
                self.lock.acquire()
                try:
                    self.globalVars['awaitingResults'] += 1
                    self.Cmeter.setStatus("busy")
                finally:
                    self.lock.release()
                
        else: # a command is received
            cmd = self.data[0].split("cmd:")[1]
            cmd = cmd.split(',')[0]
            if cmd == "stop":
                self.Cmeter.stopDaemon()
            elif cmd == "dump":
                print "Store command received."
                self.resourceManager.submitStatistics()
                self.stats.dumpStatisticsToDb()
            else:
                self.receiveStatistics(self.data[0])
                
    def printIncomingRequest(self,jobDescription,isDedicated):
        suffix = ""
        if isDedicated:
            suffix = "(Dedicated)"
            
        print "{0}: Received request {1}: {2} {3} {4}".format(time.strftime(" %H:%M:%S"),self.globalVars['filesReceived'],\
                                                             jobDescription.applicationName,jobDescription.executableName,"".join(jobDescription.arguments),suffix)
                        
    def stringToDic(self,data):
        dataDic = {}
        
        keyValuepairs = data.split(',')
        for pair in keyValuepairs:
            keyValue = pair.split('=')
            if len(keyValue) == 1:
                continue
            dataDic[keyValue[0]] = keyValue[1]
            
        return dataDic
                        
    def receiveStatistics(self,data=None,dataDict=None):
        
        if dataDict == None:
            dataDic = self.stringToDic(data)
        else:
            dataDic = dataDict
            
        statsUpdateThread = StatsUpdater.StatsUpdater(dataDic, self.stats, self.resourceManager)
        self.poolManager.processJob(statsUpdateThread)

        lockReleased = False
        self.lock.acquire()
        try:
            self.globalVars['statsReceived'] += 1
            self.globalVars['awaitingResults']-=1
            print "{0}: Received Statistics: {1}".format(time.strftime(" %H:%M:%S"),self.globalVars['statsReceived'])
            try:
                instanceID = dataDic['instance']
                awaitingJobs = self.resourceManager.decreaseAwaitingJobs(self.address[0])
            except:
                # The job was not actually executed on an instance
                awaitingJobs = 0
                
            if awaitingJobs == 0 and not self.waitingQueue.empty():
                jobSubmitter = self.waitingQueue.get()
                self.lock.release()
                lockReleased = True
                self.processDedicatedRequest(jobSubmitter)
            
            if self.globalVars['awaitingResults'] == 0:
                self.Cmeter.setStatus("ready")
                
        finally:
            if not lockReleased:
                self.lock.release()
                
        
                    
        
    def processDedicatedRequest(self,jobSubmitter):
        
        jobHashValue = jobSubmitter.getJobHashValue()
        jobName = jobSubmitter.getJobName()
        knownStats = self.stats.getKnownStats(jobHashValue)
        if knownStats != None:
            print "\n\n\n\n\t\t\t\tREUSING\n\n\n\n"
            dataDic = {'jobName':jobName,'ded':'True','hashValue':jobHashValue}
            dataDic.update(knownStats)
            self.lock.acquire()
            try:
                self.globalVars['awaitingResults']+=1
            finally:
                self.lock.release()
                
            self.receiveStatistics(dataDict = dataDic)
        else:
            # if there is available resource
            self.lock.acquire()
            try:
                idleInstance = self.resourceManager.getIdleInstance()
                if idleInstance is None:
                    #put the job in waiting queue
                    self.waitingQueue.put(jobSubmitter)
                else:
                    self.sendDedicatedRequest( jobSubmitter, idleInstance)
            finally:
                self.lock.release()
                
    def sendDedicatedRequest(self,job,instance):
        job.setInstance(instance)
        # put the job in the queue for processing
        self.poolManager.processJob(job)
#        self.resourceManager.increaseAwaitingJobs(instance.id)
        self.globalVars['awaitingResults'] += 1
        self.Cmeter.setStatus("busy")
        
    def isDedicated(self,data):
        dedicated = False
        try:
            if data[1]=="dedicated":
                dedicated = True
        except:
            #data[1] does not exist
            pass
        return dedicated