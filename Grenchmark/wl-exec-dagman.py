#!/usr/bin/python

"""
NAME

    wl-exec-dagman -- execute workflow (composite) applications; similar with wl-exec, with 
    slight modifications 

SYNOPSIS
    %(progname)s [OPTIONS] <Workload File Name>

DESCRIPTION
    wl-exec submits a composite application to a Grid scheduler. 
    All stdout and stderr messages of the submission command 
    are redirected to files in the run/ subdirectory, created in 
    the workload definition file directory (e.g.,
    for workload definition file out/wl-to-submit.wl, the output files will
    be placed in out/run/)
    
    wl-exec is part of the Grenchmark project. For more information, please
    visit the Grenchmark web-page at http://www.pds.ewi.tudelft.nl/~iosup/index.html.
             
OPTIONS:
    Arguments:
    --help 
      Print a summary of the wl-gen-simple options and exit.
    
    --threads=<string>, -t <string>
      use that many submission threads [default=5]
    
    --nosubmit
      don't submit, just print what would be done
    
    --background
      run the scheduler submit commands in the background [default=nobackground]
    
    --onefile
      output all submit tool's (e.g., krunner or condor-submit) to 
      one file for standard output (WLDir/out/onefile.out) and 
      one file for standard error (WLDir/out/onefile.err)
    
    --version
      Display wl-gen-simple version and copyright.
    

SAMPLE RUN:

    Run the random jobs WL with 5 submission threads. 
    
    $ ./wl-psubmit.py test.wl -t 5 --nosubmit
    2005-08-08 14:58:11 Parsing workload file
    ...
    2005-08-08 14:58:16 Workload file processed, proceeding to submission
    Found  9 due to start at 19182
    ...
    Found  0 due to start at 59257
    Found 20 apps. Sorting...done.
    App 14 starts in  0 seconds.
    App 4 starts in  6 seconds.
    ...
    App 16 starts in  98 seconds.
    Work request #13868608 added (id=14, start time=0.0).
    Work request #13868568 added (id=4, start time=6.8).
    ...
    #13868608 (14): 14:58:30/14:58:30/14:58:30/14:58:31
    #13868488 (17): 14:58:31/14:58:38/14:58:38/14:58:38
    #13868568 (4): 14:58:30/14:58:37/14:58:37/14:58:38
    #13868528 (9): 14:58:38/14:58:48/14:58:48/14:58:49
    ...
    2005-08-08 15:04:21 All done
"""

__proggy = "wl-parse";
__rev = "0.1";
__proggy_stamp__ = "%s v%s" % (__proggy, __rev);
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'wl-parse.py';
__version__ = '$Revision: %s$' % __rev;
__date__ = "$Date: 2005/08/15 17:10:00 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python"  

#---------------------------------------------------
# Log:
# 15/10/2007 C.S. 0.1 	Started this app based on wl-exec.py. Modifications to wl-exec:
#			all the tasks in the composite job have the starting time 0,
#			unlike in wl-exec; slight modification to the way jobs are
#			inserted in the pool 
#---------------------------------------------------

#---------------------------------------------------
# Log for wl-exec (old):
# 15/09/2005 A.I. 0.16 Added the nobackground flag, so that threads could
#                      be blocked with long running jobs
# 16/08/2005 A.I. 0.15 Changed the time to be a float
# 08/08/2005 A.I. 0.13 Fixed minor bug: when the file was not valid, 
#                      the error was incorrectly displayed
# 08/08/2005 A.I. 0.1  Started this app
#---------------------------------------------------


import sys, string
import getopt
import os
from xml.sax import saxlib, saxexts
import time
import sys
if "utils" not in sys.path: sys.path.append("utils")
import AIStorageUtils 
import AISystemUtil
import AIRandomUtils
import ASPNThreadPool
import WLDocHandlers
import thread
import threading
import traceback

ListOfApps = {}

StdOutLock = threading.Lock()
class CompositeApplicationData:
    """ a thread-safe composite application data set """
    
    def __init__(self, MaxFailures = 5):
        self.JobsWithDeps = {}
        self.lock = thread.allocate_lock()
        self.MaxFailures = MaxFailures # how many failures before a job is considered FAILED
        self.TotalJobs = 0
        self.TotalSuccessful = 0
        self.TotalFailed = 0
        
    def isCompositeApplicationFinished(self):
        """ thread-safe """
        self.lock.acquire()
        try:
            self.TotalSuccessful, self.TotalFailed, self.TotalJobs = 0, 0, 0
            for JobID in self.JobsWithDeps:
                self.TotalJobs = self.TotalJobs + 1
                if self.JobsWithDeps[JobID]['finished']:
                    self.TotalSuccessful = self.TotalSuccessful + 1
                elif self._isFailed(JobID):
                    self.TotalFailed = self.TotalFailed + 1
            return self.TotalSuccessful + self.TotalFailed == self.TotalJobs
        finally:
            self.lock.release()
        
    def addJob(self, JobID, JobData):
        """ thread-safe """
        # JobData must be a dictionary and contain a 'dependsOn' key
        # JobData['dependsOn'] must be a list of dependencies
        if 'dependsOn' not in JobData:
            raise Exception, "CompositeApplicationData: the JobData given for " + str(JobID) + "does not contain the dependsOn key"
            
        self.lock.acquire()
        try:
            self.JobsWithDeps[JobID] = JobData
            self.JobsWithDeps[JobID]['finished'] = False # mark as 'not finished'
            self.JobsWithDeps[JobID]['canRun'] = False   # mark as 'cannot run'
            self.JobsWithDeps[JobID]['failed'] = 0       # no failures so far
        finally:
            self.lock.release()
            ##print '>>> CompositeApplicationData >>>', "Job", JobID, "added", time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
            
    def buildEnablesRelations(self):
        """ not thread-safe """
	self.lock.acquire()
        try:
    	    for JobID in self.JobsWithDeps:
        	self.JobsWithDeps[JobID]['enables'] = []
        	for DependencyID in self.JobsWithDeps:
            	    if JobID in self.JobsWithDeps[DependencyID]['dependsOn']:
                	# DependencyID depends on JobID -> create the reverse relation (enable)
                	self.JobsWithDeps[JobID]['enables'].append(DependencyID)
	finally:
	    self.lock.release()
            
    def delJob(self, JobID, returnJob = False):
        """ thread-safe """
        if JobID in self.JobsWithDeps:
            self.lock.acquire()
            try:
                OneJob = self.JobsWithDeps[JobID]
                del self.JobsWithDeps[JobID]
                if returnJob: return OneJob
            finally:
                self.lock.release()
                
    def _triggerCanRunCheck(self, JobID):
        """ not thread-safe, not checking whether JobIDs exist """
        if self.JobsWithDeps[JobID]['canRun']: 
            return # already decided
            
        self.JobsWithDeps[JobID]['canRun'] = True   # mark as 'can run'
        for DependencyID in self.JobsWithDeps[JobID]['dependsOn']:
            if not self.JobsWithDeps[DependencyID]['finished']: 
                # one dependency failed -> mark as 'cannot run'
                self.JobsWithDeps[JobID]['canRun'] = False   
                return
        ##
        print '>>> CompositeApplicationData >>>', "Job", JobID, "was marked as 'can run'", time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
        
    def triggerCanRunCheck(self, JobID):
        """ thread-safe """
        if JobID in self.JobsWithDeps:
            self.lock.acquire()
            try:
                self._triggerCanRunCheck(JobID)
            finally:
                self.lock.release()
        
    def triggerJobFinished(self, JobID):
        """ thread-safe """
        if JobID in self.JobsWithDeps:
            self.lock.acquire()
            try:
                self.JobsWithDeps[JobID]['finished'] = True
                ##
                print '>>> CompositeApplicationData >>>', "Job", JobID, "has finished at", time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
                for DependencyID in self.JobsWithDeps[JobID]['enables']:
                    if DependencyID in self.JobsWithDeps:
                        self._triggerCanRunCheck(DependencyID)
            finally:
                self.lock.release()
                
    def triggerJobFailure(self, JobID):
        """ thread-safe """
        if JobID in self.JobsWithDeps:
            self.lock.acquire()
            try:
                self.JobsWithDeps[JobID]['failed'] = self.JobsWithDeps[JobID]['failed'] + 1
            finally:
                self.lock.release()
                
    def _isFailed(self, JobID):
        """ not thread-safe """
        return self.JobsWithDeps[JobID]['failed'] >= self.MaxFailures
        
    def _makeFailed(self, JobID):
        """ not thread-safe """
        self.JobsWithDeps[JobID]['failed'] = self.MaxFailures
        
    def isFailed(self, JobID):
        """ thread-safe """
        if JobID in self.JobsWithDeps:
            self.lock.acquire()
            try:
                return self._isFailed(JobID)
            finally:
                self.lock.release()
        return False
    
    def isRunnable(self, JobID):
        """ thread-safe """
        if JobID in self.JobsWithDeps:
            self.lock.acquire()
            try:
                if self.JobsWithDeps[JobID]['canRun']:
                    return not self._isFailed(JobID)
                else:
                    return False
            finally:
                self.lock.release()
            
        return True
        
    def isSuccessful(self, JobID):
        """ thread-safe """
        if JobID in self.JobsWithDeps:
            self.lock.acquire()
            try:
                return self.JobsWithDeps[JobID]['finished']
            finally:
                self.lock.release()
            
        return False
        
    def propagateFailure(self, JobID):
        """ thread safe """
        if self.isFailed(JobID):
            self.lock.acquire()
            try:
                ##print '>>> CompositeApplicationData >>>', "Propagate failure for Job", JobID
                ListOfFailedJobs = [JobID]
                while len(ListOfFailedJobs) > 0:
                    JobID = ListOfFailedJobs[0]
                    del ListOfFailedJobs[0]
                    # every job that this failed job enabled is now failed as well
                    for DependencyID in self.JobsWithDeps[JobID]['enables']:
                        if DependencyID in self.JobsWithDeps:
                            if not self._isFailed(DependencyID):
                                self._makeFailed(DependencyID) # force failed
                                ListOfFailedJobs.append(DependencyID)
                                ##print '>>> CompositeApplicationData >>>', "Propagate failure for Job", JobID, ":", "job", DependencyID, "is now marked as failed"
            finally:
                self.lock.release()
                
        
        
TheCompositeApplicationData = None

def runJob(data):
    # 1. check if the job can be run (deps & time)
    # 1.1. yes: run the job
    # 1.1.1.    if job run successfully
    # 1.1.1.1.  yes: mark job as correct
    # 1.1.1.2.  no: put the job back into the pool, if not failed (too many failures)
    # 1.2. no: put the job back into the pool
    
    #-- compute due sleep time - modified (corina): sleep time will always be 0
    #sleepDuration = max( 0, data['firstSubmission'] + data['startTime'] - time.time())
    sleepDuration = 0
        
    # 1. check if the job can be run (time)
    if  sleepDuration <= 0: # job is due to run
        #-- start timers
        result={}
        result['start'] = time.time()
        result['wakeup'] = time.time()
        result['submit'] = time.time()
        # 1. check if the job can be run (time)
        JobID = data['id']
	#print "##### [runJob] job is due to run: %s " % JobID
	
        CurrentCompositeApplicationData = data['.CompositeApplicationData']
        if CurrentCompositeApplicationData.isRunnable(JobID): # job can run
            # 1.1. yes: run the job
            patchSleepDuration = AIRandomUtils.getRandomInt(0, 10)
            time.sleep(patchSleepDuration) 
            Command = data['commandLine']
            outputString = "(" + data['id'] + ") runs command:\n    " + Command
            print outputString
            if data['NoSubmit'] != 1:
                try:
                    cmdOutput = AISystemUtil.getCommandOutput2( Command );
                    result['status'] = 'SUCCEEDED'
                    CurrentCompositeApplicationData.triggerJobFinished(JobID)
                    
                except RuntimeError, e:
                    print "Job", JobID, "returned:", e
                    cmdOutput =''
                    # job failed ?
                    CurrentCompositeApplicationData.triggerJobFailure(JobID)
                    if CurrentCompositeApplicationData.isFailed(JobID):
                        result['status'] = 'FAILED'
                        CurrentCompositeApplicationData.propagateFailure(JobID)
                        print "Job", JobID, "was declared failed (too many failures)"
                        
                    else:
                        result['status'] = 'RETRY'
                        print "Job", JobID, "failed... rescheduling"
                        return None
                        
                outputString = "Output (" + JobID + "): '" + cmdOutput + "'"
                print outputString
            else: # no submit -> just mark as succeessful
                result['status'] = 'SUCCEEDED'
                
            result['exit'] = time.time()
            #-- return all the times
            ##print "Job", JobID, "Send good result", result['status']
            return result
            
        elif CurrentCompositeApplicationData.isFailed(JobID):
            result['exit'] = time.time()
            result['status'] = 'FAILED'
            #-- return all the times
            ##print "Job", JobID, "Send good result", result['status']
            return result
            
    # NOTE: the redo case (return None) happens when a non-failed job crashes, or 
    #       when a job must still wait until its requested start time
    print "#### Job sent None result"
    return None # cannot run, reschedule (ASPNThreadPool enhancement)
    
def printJobResults(request, result):
    tstart = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(result['start']))
    tstart = time.strftime('%H:%M:%S', time.gmtime(result['start']))
    twakeup = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(result['wakeup']))
    twakeup = time.strftime('%H:%M:%S', time.gmtime(result['wakeup']))
    tsubmit = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(result['submit']))
    tsubmit = time.strftime('%H:%M:%S', time.gmtime(result['submit']))
    texit = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(result['exit']))
    
    print "#%s(%s): S %s/SUB %.3fs(%.3fs)/E %s)" % \
          (request.requestID, request.args[0]['id'], 
           tstart, float(result['submit'] - request.args[0]['firstSubmission']), 
           float(result['submit'] - request.args[0]['firstSubmission'] - request.args[0]['startTime']),
           texit)

    print "#SUBMITTIME %d" % result['submit']
    print "#STATUS %s %s" % (request.args[0]['id'], result['status'])
    

def runWL( OutputDir, XMLhandler, NPoolThreads, NoSubmit=0, Background=0, OneFile=0 ):
    
    #--- get applications
    DictionaryOfApps = XMLhandler.getDictionaryOfApplications()
    
    #--- create composite structure manager
    TheCompositeApplicationData = CompositeApplicationData()
    
    ##    ListOfApps = AIStorageUtils.dict_sortbykey( DictionaryOfApps, AIStorageUtils.SORT_DESCENDING )
    ##    for (id, App) in ListOfApps: 
    ##        print "Found ", App['id'], "due to start at", App['runTime']
    ##        
    #-- sort jobs
    ListOfApps = AIStorageUtils.dict_sortbyvalue_dict( DictionaryOfApps, 'runTime', 
                                                       AIStorageUtils.SORT_TYPE_FLOAT, 
                                                       AIStorageUtils.SORT_ASCENDING )
    NTotalJobs = len( ListOfApps )
    print "Found", NTotalJobs, "apps. Sorting...done."
    
    # Modification - C.S.: make all the tasks have the start time 0                                                
    #startTime = float(ListOfApps[0][1]['runTime'])
    #if startTime < 0.0: startTime = 0.0
    startTime = 0.0;
    
    #-- correct start times and add all applications to the composite structure manager
    for (id, App) in ListOfApps: 
	App['runTime'] = 0;
        #App['runTime'] = float(App['runTime']) - startTime
        #if App['runTime'] < 0.0: App['runTime'] = 0.0
        print "ID", id, "starts in %.3fs." % float(App['runTime']/1000.0)
        # add the 'dependsOn' key if missing
        if 'dependsOn' not in App:
            App['dependsOn'] = []
        TheCompositeApplicationData.addJob(id, App)
	
    #-- create all 'enables' relations
    TheCompositeApplicationData.buildEnablesRelations()
    #-- mark all the starting jobs as 'can run'
    for id in TheCompositeApplicationData.JobsWithDeps:
        TheCompositeApplicationData.triggerCanRunCheck(id)
        
    #--- generate all work units
    try:
        os.mkdir( OutputDir )
    except:
        pass
        
    #--- build a WorkRequest object for each work unit
    FirstSubmission = time.time()
    CommandLinesList = []
    for (id, App) in ListOfApps: 
        #-- generate item
        CommandLineItem = {}
        CommandLineItem['.CompositeApplicationData'] = TheCompositeApplicationData
        CommandLineItem['id'] = id
        CommandLineItem['firstSubmission'] = FirstSubmission
        CommandLineItem['startTime'] = float(App['runTime']/1000.0)
        #CommandLineItem['commandLine'] = "drunner -g -e -o -f %s 1> %s.out 2> %s.err &" % (App['jdf'], id, id)
        
        if OneFile == 0:
            StdOutFile = os.path.join( OutputDir, "%s.out" % id )
            StdErrFile = os.path.join( OutputDir, "%s.err" % id )
            ActualCommand = "%s 1> %s 2> %s" % \
                ( App['submitCommand'], StdOutFile, StdErrFile )
        else:
            StdOutFile = os.path.join( OutputDir, "onefile.out" )
            StdErrFile = os.path.join( OutputDir, "onefile.err" )
            ActualCommand = "%s 1>> %s 2>> %s" % \
                ( App['submitCommand'], StdOutFile, StdErrFile )
        if Background == 1:
            CommandLineItem['commandLine'] = ActualCommand + ' &'
        else:
            CommandLineItem['commandLine'] = ActualCommand
                
        #-- amod v.0.12: just generate commands
        CommandLineItem['NoSubmit'] = NoSubmit
            
        #-- append item
        if os.path.exists(App['jdf']):
            CommandLinesList.append(CommandLineItem)
        else:
            print "Could not locate JDF", App['jdf'], "... skipping job"
        
    
    requests = ASPNThreadPool.makeRequests(runJob, CommandLinesList, printJobResults)
    
    #--- create a pool of NPoolThreads worker threads
    print "[wl-exec-dagman.py] Starting a thread pool with", NPoolThreads, "threads"
    submitThreadPool = ASPNThreadPool.ThreadPool(NPoolThreads, StdOutLock)
    
    StartSubmissionTime = time.time()
    #--- add all work units into the thread pool
    #   NOTE: We expect the thread pool to be based on Queues,
    #         beacause our applications need to be run at specified times
    #         and the submit job waits until the current work unit is done
    #         -> if we are NOT using Queues, it may happen that a work unit
    #         that needs to be submitted at time T will get submitted much 
    #         later, due to other jobs starting the submission before it,
    #         but waiting for their later start time
    
    # Modification - corina: the requests are put in the thread pool only when
    # their dependencies are satisfied
    requestsBkp = requests[:]
    for req in requestsBkp:
	reqId = req.args[0]['id'];
	# take only the runnable jobs
	if TheCompositeApplicationData.isRunnable(reqId):
            submitThreadPool.putRequest(req)
	    # remove the request from the list if it was submitted to the pool
	    requests.remove(req) 
	    #DEBUG:print req.args
    	    print "[Pool] Work request #%s added (id=%s, start time=%.3f)." % \
        	  (req.requestID, req.args[0]['id'], req.args[0]['startTime'])
        
    #--- wait for all submissions to be completed
    # submitThreadPool.wait()
    while 1:
        try:
            submitThreadPool.poll()
            EndSubmissionTime = time.time()
            time.sleep(0.5)
##            if TheCompositeApplicationData.isCompositeApplicationFinished():
##                #submitThreadPool.wait()
##                EndSubmissionTime = time.time()
##                break
##            time.sleep(1)
##            #print "Main thread working..."
            
        except ASPNThreadPool.NoResultsPending:
            #-- check that all jobs have actually finished or failed
            if TheCompositeApplicationData.isCompositeApplicationFinished():
                EndSubmissionTime = time.time()
                break
            else:
		# see if we have some more runnable jobs and add them to the pool
	        requestsBkp2 = requests[:]
		for req in requestsBkp2:
		    reqId = req.args[0]['id'];
		    if TheCompositeApplicationData.isRunnable(reqId):
        		submitThreadPool.putRequest(req)
			requests.remove(req)
			#DEBUG:print req.args
    			print "[Pool] Work request #%s added (id=%s, start time=%.3f)." % \
        		    (req.requestID, req.args[0]['id'], req.args[0]['startTime'])

                print "[wl-exec-dagman] Got ASPNThreadPool.NoResultsPending"
                print "         All:", TheCompositeApplicationData.TotalJobs, \
                      "Done:", TheCompositeApplicationData.TotalSuccessful, \
                      "Failed:", TheCompositeApplicationData.TotalFailed
                time.sleep(2)
        except KeyboardInterrupt:
            break
        except:
            print ">>>" + traceback.print_exc()
            raise Exception, "aaaaaaaaaaaaaaaaaaaaaaa"
    
    NTotalJobsInQueue = len(submitThreadPool.workRequests)
##    print ">>>", "NTotalJobsInQueue:", NTotalJobsInQueue
##    
##    #-- mark all the starting jobs as 'can run'
##    for id in TheCompositeApplicationData.JobsWithDeps:
##        print "ID", id, "isFailed:", TheCompositeApplicationData.isFailed(id), "isSuccessful:", TheCompositeApplicationData.isSuccessful(id)
    
    return StartSubmissionTime, EndSubmissionTime, NTotalJobs, NTotalJobsInQueue

def usage(progname):
    print __doc__ % vars() 

def version():
    print "Version: ", __version__
    print "Date: ", __date__
    print __copyright__, "(", __email__, ")"

def main(argv):                  

    global DirSSER
    global NRandomTests
           
    try:                                
        opts, args = getopt.getopt(argv, "ht:", ["help", "threads=", "version", "nosubmit", "background", "onefile"])
    except getopt.GetoptError:
        print "Error while converting options: unknown option(s) encountered.\n\n"
        usage(os.path.basename(sys.argv[0]))
        sys.exit(2)
    
    NThreads = 30
    NoSubmit = 0
    OneFile = 0
    Background = 0
    
    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            usage(os.path.basename(sys.argv[0]))
            sys.exit()
        elif opt in ["--version"]:
            version()
            sys.exit()
        elif opt in ["-t", "--threads"]: 
            try:
                NThreads = int(arg.strip()) 
		print "[wl-exec-dagman.py] Number of threads set to %s " % NThreads
            except ValueError:
                NThreads = 30
        elif opt in ["--nosubmit"]:
            NoSubmit = 1
        elif opt in ["--background"]:
            Background = 1
        elif opt in ["--onefile"]:
            OneFile = 1
        else:
            print "Unknown parameter", opt
    
    if len(args) < 1:
        print "Error: No workload file given.\n\n"
        usage(os.path.basename(sys.argv[0]))
        sys.exit(3)
        
    WorkloadFileName = args[0];
    if not os.path.isfile( WorkloadFileName ):
        print "Error: %s is not a valid file.\n\n" % WorkloadFileName
        usage(os.path.basename(sys.argv[0]))
        sys.exit(1)
        
    print "%s Parsing workload file %s" % \
          ( time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time())), WorkloadFileName )
    handlerXML = WLDocHandlers.readWorkloadSubmitFile( WorkloadFileName )
    print "%s Workload file processed, proceeding to submission"  % \
          ( time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time())) ) 
        
    WorkloadDir = os.path.join(os.path.dirname(WorkloadFileName),"run")
    print "Workload directory", WorkloadDir
    StartSubmissionTime, EndSubmissionTime, NTotalJobs, NTotalJobsInQueue = \
        runWL( WorkloadDir, handlerXML, NThreads, NoSubmit, Background, OneFile )
    print "%s All done" % time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
    
    tstart = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(StartSubmissionTime))
    tend = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(EndSubmissionTime))
    print "------ SUBMISSION SUMMARY ---------"
    print "Started submission at %s" % tstart
    print "Ended submission at %s" % tend
    print "Submission total time/Total Jobs/submitted/Jobs per second"
    #      0123456789012345678901234567890123456789012345678901234567890123456789
    #      0         1         2         3         4         5         6  
    DeltaTime = float(EndSubmissionTime - StartSubmissionTime)
    if DeltaTime > 0.e-8:
        Avg = float(NTotalJobs - NTotalJobsInQueue) / DeltaTime
    else:
        Avg = 0.0
    print "   %15.3f   /  %6d  / %6d  /  %.3f" % \
       ( DeltaTime, NTotalJobs, NTotalJobs - NTotalJobsInQueue, Avg )

if __name__ == "__main__":

    main(sys.argv[1:]) 
    
    
    