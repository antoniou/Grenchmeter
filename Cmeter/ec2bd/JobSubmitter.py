import sys
import os
import subprocess
import hashlib
import time

import JsdlParser
import workerpool
import Timing
from PersistentStatistics import *

class JobSubmitter(workerpool.Job):
    def __init__(self,fileName, resourceManager, configurationManager, stats, jobSubmissionTime,dedicatedMode): # job2Submit of type JsdlParser.Job
        self.jsdlFile = fileName
        self.profiler = Timing.timeprofile()
        self.resourceManager = resourceManager
        self.configurationManager = configurationManager
        self.stats = stats
        self.jobSubmissionTime = jobSubmissionTime
        self.dedicatedMode = dedicatedMode
        self.runOnInstance = None
        self.jobHashValue = None
        
        try:
            self.jobToSubmit = JsdlParser.Job(self.jsdlFile)
        except:
            print "Error while parsing file %s:" % self.jsdlFile, sys.exc_info()[0]
        
        hashKey = "{0}{1}{2}".format(self.jobToSubmit.executableName,self.jobToSubmit.dataStaging,self.jobToSubmit.arguments)
        self.jobHashValue = hashlib.sha1(hashKey).hexdigest()
        
        
    def run(self):
        self.job_removed_from_queue = time.time()
        
        #!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Workaround for race condition of job submission thread and status update thread\
        if not self.dedicatedMode:
            self.stats.updateStatistics(self.jobToSubmit.applicationName,
                                        job_arrival = self.jobSubmissionTime)
                                      
        instance = self.getInstanceToExecuteOn()
        
        command = self.getCommandToExecute(instance.getID())
        
        print "Command: ",command
        self.executeOnInstance(instance, command)
                    
        if not self.dedicatedMode:
            self.stats.updateStatistics(self.jobToSubmit.applicationName,
                                    self.jobSubmissionTime,
                                    self.job_removed_from_queue,
                                     self.profiler.getValue('resource_selection_algorithm'),
                                      0,
                                      0,
                                      0,
                                      0,
                                      0,
                                      0,
                                      0,
                                      0,
                                      None,
                                      None,
                                      None,
                                      None,
                                      None,
                                      None,
                                     instance.getDNSName())
            
            
    def executeOnInstance(self,instance,command):
        print "{0}: Executing job {1} on instance {2} ({3})".format(time.strftime(" %H:%M:%S"),self.jobToSubmit.applicationName,instance.getID(),instance.getDNSName())
        executed = instance.execute(command)
            
    def getInstanceToExecuteOn(self):
        self.profiler.mark('resource_selection_algorithm')

        # If an instance is dictated (in dedicated mode)
        if self.runOnInstance is not None:
#            (host,instanceId) = (self.runOnInstance.dns_name,self.runOnInstance.id)
            instance = self.runOnInstance
        else:
            instance = self.resourceManager.getNextAvailableInstance()
#            self.resourceManager.increaseAwaitingJobs(instance.getID())
            
        self.profiler.elapsed('resource_selection_algorithm')
        return instance
            
    def getCommandToExecute(self,instanceId):
        commandToExecuteTheJob = os.path.basename(self.jobToSubmit.executableName)
        self.buildWebServerDestinationFolder()
        filesToDownload = self.copyFilesToWebserver()
        
        for arg in self.jobToSubmit.arguments:
            commandToExecuteTheJob = commandToExecuteTheJob + ' ' + arg
            
        baseUrl  = self.configurationManager.getHttpServerBaseUrl()
        cmeterDaemonUrl = self.configurationManager.getCmeterDaemonUrl();
        cmeterDaemonPort = self.configurationManager.getEc2BdPort();
        jobUrl = baseUrl + self.jobToSubmit.applicationName

        # will create the directory named 'self.jobToSubmit.applicationName'
        wgetCommand = "wget "+ baseUrl +"ExecuteJob.py " + " -t 9999 -w 15 -P " + self.jobToSubmit.applicationName
        
        # Command to be executed on the VM instance, to retrieve the appropriate job files and consequently run the job
        commandToExecute = 'python ' + self.jobToSubmit.applicationName +'/ExecuteJob.py -u "'+jobUrl + '" -e "'+ commandToExecuteTheJob + '" -f "'\
                                     + filesToDownload + '" -j "'  + self.jobToSubmit.applicationName + '" -i "' + str(instanceId) \
                                     + '" -c "' + cmeterDaemonUrl + '" -p "' + cmeterDaemonPort + '" -h "' + self.jobHashValue + '"'
        if self.dedicatedMode==True:
            commandToExecute+=" --dedicated"
        commandToExecute = commandToExecute + '\n'
        
        allCommand = wgetCommand + ';' + commandToExecute
        
        return allCommand
        
    def buildWebServerDestinationFolder(self):
        if(sys.platform.find("linux")>-1):
            self.destinationFolder = self.configurationManager.getHttpServerBase() + "/" + self.jobToSubmit.applicationName 
            os.system("mkdir " + self.destinationFolder)
        else:
            #Windows OS        
            self.destinationFolder = self.configurationManager.getHttpServerBase() + "\\" + self.jobToSubmit.applicationName 
            os.system("mkdir " + self.destinationFolder)
    
    def copyFilesToWebserver(self):
        source = self.jobToSubmit.executableName
        
        # Copy the binary file to the web server directory        
        if(sys.platform.find("linux")>-1):
            # For linux distributions
            finalName = source.split('/');
            exeName = finalName[len(finalName)-1]
            os.system ("cp %s %s/%s" % (source, self.destinationFolder, exeName))
        else:
            #Windows OS        
            os.system ("copy %s %s" % (source, self.destinationFolder))
    
        filesToDownload = os.path.basename(self.jobToSubmit.executableName)
        
        numOfFiles = len(self.jobToSubmit.dataStaging)
        for i in range(numOfFiles):
            ds = self.jobToSubmit.dataStaging[i]
            if ds.source != '':
                if(sys.platform.find("linux")>-1):
                    os.system ("cp %s %s" % (ds.source, self.destinationFolder))
                else:
                    os.system ("copy %s %s" % (ds.source, self.destinationFolder))
                filesToDownload = filesToDownload +  ',' + os.path.basename(ds.source)
                
        return filesToDownload
    
    def getJobDescription(self):
        return self.jobToSubmit
    
    def getJobName(self):
        return self.jobToSubmit.applicationName
    
    def getJobHashValue(self):
        return self.jobHashValue
    
    def setInstance(self,instance):
#        print "THIS JOB SUBMITTER will run on instance", instance.id
        self.runOnInstance=instance
