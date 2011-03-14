import sys
import os
import subprocess

import time

import JsdlParser
import workerpool
import SshUtils
import Timing
from PersistentStatistics import *

class JobSubmitter(workerpool.Job):
    def __init__(self,fileName, resourceManager, configurationManager, stats, jobSubmissionTime): # job2Submit of type JsdlParser.Job
        self.jsdlFile = fileName
        self.profiler = Timing.timeprofile()
        self.resourceManager = resourceManager
        self.configurationManager = configurationManager
        self.stats = stats
        self.jobSubmissionTime = jobSubmissionTime

    def run(self):
        self.job_removed_from_queue = time.time()
        
        try:
            self.jobToSubmit = JsdlParser.Job(self.jsdlFile)
        except:
            print "Error while parsing file %s:" % self.jsdlFile, sys.exc_info()[0]
            
        #!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Workaround for race condition of job submission thread and status update thread
        self.stats.updateStatistics(self.jobToSubmit.applicationName,
                                    self.jobSubmissionTime,
                                    None,None,None,None,
                                    None,None,None,None,
                                    None,None,None,None, 
                                    None,None,None)  
                    
        # Copy the binary file to the web server directory        
        source = self.jobToSubmit.executableName
        if(sys.platform.find("linux")>-1):
            # For linux distributions
            dest = self.configurationManager.getHttpServerBase() + "/" + self.jobToSubmit.applicationName 
            os.system("mkdir " + dest)
            finalName = source.split('/');
            exeName = finalName[len(finalName)-1]
            os.system ("cp %s %s/%s.bin" % (source, dest, exeName))
        else:
            #Windows OS        
            dest = self.configurationManager.getHttpServerBase() + "\\" + self.jobToSubmit.applicationName 
            os.system("mkdir " + dest)
            os.system ("copy %s %s" % (source, dest))        
            
        # Debug: Added a '.bin' extension so that the files are downloadable from the webserver
        commandToExecuteTheJob = os.path.basename(self.jobToSubmit.executableName)+".bin"
        filesToDownload = os.path.basename(self.jobToSubmit.executableName)+".bin"
        
        numOfFiles = len(self.jobToSubmit.dataStaging)
        for i in range(0,numOfFiles):
            ds = self.jobToSubmit.dataStaging[i]
            if ds.source != '':
                if(sys.platform.find("linux")>-1):
                    os.system ("cp %s %s" % (ds.source, dest))
                else:
                    os.system ("copy %s %s" % (ds.source, dest))
                filesToDownload = filesToDownload +  ',' + os.path.basename(ds.source)
        for arg in self.jobToSubmit.arguments:
            commandToExecuteTheJob = commandToExecuteTheJob + ' ' + arg
        
        #commandToExecuteTheJob = commandToExecuteTheJob + ' 1> ' + self.jobToSubmit.posixConstraints['Output']
        #commandToExecuteTheJob = commandToExecuteTheJob + ' 2> ' + self.jobToSubmit.posixConstraints['Error']
        
        
        self.profiler.mark('resource_selection_algorithm')
        
        #Debug by using local machine, not VM instance
        (host,instanceId) = self.resourceManager.getNextAvailableInstance()
#        host = "dutihl"
        self.profiler.elapsed('resource_selection_algorithm')

#        self.profiler.mark('ssh_overall')
        self.ssh_session_begin = time.time()
        
        baseUrl  = self.configurationManager.getHttpServerBaseUrl()
        cmeterDaemonUrl = self.configurationManager.getCmeterDaemonUrl();
        cmeterDaemonPort = self.configurationManager.getEc2BdPort();
        vmInstanceUser = self.configurationManager.getVmInstanceUser()
        jobUrl = baseUrl + self.jobToSubmit.applicationName

        # will create the directory named 'self.jobToSubmit.applicationName'
        wgetCommand = "wget "+ baseUrl +"ExecuteJob.py " + " -t 9999 -w 15 -P " + self.jobToSubmit.applicationName
        
        # Command to be executed on the VM instance, to retrieve the appropriate job files and consequently run the job
        commandToExecute = 'python ' + self.jobToSubmit.applicationName +'/ExecuteJob.py -u "'+jobUrl + '" -e "'+ commandToExecuteTheJob + '" -f "'\
                                     + filesToDownload + '" -j "'  + self.jobToSubmit.applicationName + '" -i "' + str(instanceId) + '"'
        commandToExecute = commandToExecute + '\n'
        
        allCommand = wgetCommand + ';' + commandToExecute
        print "Command is:", allCommand
        
        #self.profiler.mark('ssh_begin')
        self.ssh_open_conn_begin = time.time()
        print "Connecting to instance...",
        
        sshUtils = SshUtils.SshUtils(host,vmInstanceUser,'',self.configurationManager.getKeyPairFile())

        sshUtils.waitUntilConnected()
        self.ssh_open_conn_end = time.time()
        print "DONE"
        
        #self.profiler.elapsed('ssh_begin')

        self.ssh_execute_begin = time.time()
        executed = sshUtils.executeCommand(allCommand)
        while not executed:
            sshUtils.disconnect()
            sshUtils.waitUntilConnected()
            executed = sshUtils.executeCommand(allCommand)
        self.ssh_execute_end = time.time()
        
        
#        self.profiler.mark('ssh_end')
    
        self.ssh_close_conn_begin = time.time()
        sshUtils.disconnect()
        self.ssh_close_conn_end = time.time()
        self.ssh_session_end = time.time()
        
#        self.profiler.elapsed('ssh_end')
#        self.profiler.elapsed('ssh_overall')
        
#        job_name, job_arrival, 
#                                job_removed_from_queue, 
#                                resource_scheduling_algorithm_overhead, 
#                                ssh_session_begin, 
#                                ssh_open_conn_begin, 
#                                ssh_open_conn_end,
#                                ssh_execute_begin,
#                                ssh_execute_end,
#                                ssh_close_conn_begin,
#                                ssh_close_conn_end,
#                                ssh_session_end,
#                                job_statistics_received,
#                                overall_execution_time,
#                                job_execution_time,
#                                file_transfer_time,
#                                execution_machine
        
        self.stats.updateStatistics(self.jobToSubmit.applicationName,
                                    self.jobSubmissionTime,
                                    self.job_removed_from_queue,
                                     self.profiler.getValue('resource_selection_algorithm'),
                                      self.ssh_session_begin,
                                      self.ssh_open_conn_begin,
                                      self.ssh_open_conn_end,
                                      self.ssh_execute_begin,
                                      self.ssh_execute_end,
                                      self.ssh_close_conn_begin,
                                      self.ssh_close_conn_end,
                                      self.ssh_session_end,
                                      None,
                                      None,
                                      None,
                                      None,
                                     host)
