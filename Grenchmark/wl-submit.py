#!/usr/bin/python

"""
NAME

    wl-submit -- Grenchmark workload submitter

SYNOPSIS
    %(progname)s [OPTIONS] <Workload File Name>

DESCRIPTION
    wl-submit submits a workload to a Grid scheduler. All stdout and stderr 
    messages of the submission command are redirected to files in the run/
    subdirectory, created in the workload definition file directory (e.g.,
    for workload definition file out/wl-to-submit.wl, the output files will
    be placed in out/run/)
    
    wl-submit is part of the Grenchmark project. For more information, please
    visit the Grenchmark web-page at http://www.pds.ewi.tudelft.nl/~iosup/index.html.
             
OPTIONS:
    Arguments:
    --help 
      Print a summary of the wl-gen-simple options and exit.
    
    --threads=<string>, -t <string>
      use that many submission threads [default=5]
    
    --nosubmit
      don't submit, just print what would be done
    
    --nobackground
      don't run the command in the background
    
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
__rev = "0.15";
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
if "utils/popen5" not in sys.path: sys.path.append("utils/popen5")

import AIStorageUtils 
import AISystemUtil
import ASPNThreadPool
import WLDocHandlers
import subprocess
import threading

ListOfApps = {}

LOGFILE_PREFIX = "##!#~@$@"
FAILURE_PREFIX = "fff&*2"
StdOutLock = threading.Lock()

def submitJob(data):
    #-- first sleep until it's time to wake up
    app_times={}
    app_times['stdoutfile'] = data['stdout']
    app_times['stderrfile'] = data['stderr']
    app_times['onefile'] = data['onefile']
    app_times['testid'] = data['testid']
    app_times['projectid'] = data['projectid']
    app_times['testerid'] = data['testerid']  
    app_times['timediff'] = data['timediff']

    app_times['start'] = time.time()
    #-- sleep until the due start time
    sleepDuration = max( 0, data['firstSubmission'] + data['startTime'] - time.time())
    ##print "Need to sleep", sleepDuration
    if  sleepDuration > 0:
        time.sleep( sleepDuration )
    app_times['wakeup'] = time.time()
    #-- then run the proper command
    app_times['submit'] = time.time()
    
    Command = data['commandLine']
    outputString = "(" + data['id'] + ") runs command:\n    " + Command
    
    StdOutLock.acquire()
    print outputString
    StdOutLock.release()

    if data['NoSubmit'] != 1:
	#process = subprocess.Popen(["python", "waiter.py", Command], executable = "python", stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        (retcode, output) = data['runningProcess'] (Command, app_times)

	app_times['returncode'] = retcode
	app_times['output'] = output
          
    #-- return all the times
    return app_times
    
def printSubmitJobResults(request, result):

    tstart = time.strftime('%H:%M:%S', time.gmtime(result['start'] + result['timediff']))
    twakeup = time.strftime('%H:%M:%S', time.gmtime(result['wakeup'] + result['timediff']))
    tsubmit = time.strftime('%H:%M:%S', time.gmtime(result['submit'] + result['timediff']))
    texit = time.strftime('%H:%M:%S', time.gmtime(result['exit'] + result['timediff']))

    testid = result['testid']
    projectid = result['projectid']
    testerid = result['testerid']

    sLine = "\n" + LOGFILE_PREFIX + str(testid) + "\1" + str(projectid) + "\1" + str(testerid) + \
           "\1" + "%s\1(%s): S %s/SUB %.3fs(%.3fs)/E %s retcode=%s)\n" % \
           (str(request.requestID), request.args[0]['id'], 
           tstart, float(result['submit'] - request.args[0]['firstSubmission']), 
           float(result['submit'] - request.args[0]['firstSubmission'] - request.args[0]['startTime']),
           texit, str(result['returncode']))

    StdOutLock.acquire()
    sys.stdout.write(sLine)
    StdOutLock.release()

    if (result['returncode'] != 0): # failure
        sLine = "\n" + LOGFILE_PREFIX + FAILURE_PREFIX + "\1" + str(testid) + \
                "\1" + str(projectid) + "\1" + str(testerid) + "\1" + \
                str(result['threadid']) + "\1" + "Failure" + "\1" + \
                str(result['exit']) + "\1" + str(result['returncode']) + "\n"

        StdOutLock.acquire()
        sys.stdout.write(sLine)
        StdOutLock.release()

    #print "#SUBMITTIME %d" % result['submit']
    #print 'returncode=', result['returncode']
    #print "output=", result['output']

    lines = result['output'].split("\n")
    for line in lines:
        if (len(line) > 1):
            sLine = "\n" + LOGFILE_PREFIX + str(testid) + "\1" + str(projectid) + "\1" + str(testerid) + "\1" + str(request.requestID) + "\1" + line + "\n"

            StdOutLock.acquire()
            sys.stdout.write(sLine)
            StdOutLock.release()

    if result['onefile'] == 0:

	try:
		fin = open(result['stdoutfile'])
		lines = (fin.read()).split("\n")

		for line in lines:
			if (len(line) > 1):
				sLine = "\n" + LOGFILE_PREFIX + str(testid) + "\1" + str(projectid) + "\1" + str(testerid) + "\1" + str(request.requestID) + "\1" + line + "\n"

				StdOutLock.acquire()
				sys.stdout.write(sLine)
				StdOutLock.release()

		fin.close()
	except:
		pass

	try:
	        fin = open(result['stderrfile'])
        	lines = (fin.read()).split("\n")

	        for line in lines:
        	        if (len(line) > 1):
                	        sLine = "\n" + LOGFILE_PREFIX + str(testid) + "\1" + str(projectid) + "\1" + str(testerid) + "\1" + str(request.requestID) + "\1" + line + "\n"

				StdOutLock.acquire()
				sys.stdout.write(sLine)       
				StdOutLock.release()

	        fin.close()
	except:
		pass

def runWL( OutputDir, XMLhandler, NPoolThreads, NoSubmit=0, NoBackground=0, OneFile=0, testid=0, projectid = "default", testerid=0, timediff=0.0 ):
    
    DictionaryOfApps = XMLhandler.getDictionaryOfApplications()
    
    ##    ListOfApps = AIStorageUtils.dict_sortbykey( DictionaryOfApps, AIStorageUtils.SORT_DESCENDING )
    ##    for (id, App) in ListOfApps: 
    ##        print "Found ", App['id'], "due to start at", App['runTime']
    ##        
        
    ListOfApps = AIStorageUtils.dict_sortbyvalue_dict( DictionaryOfApps, 'runTime', 
                                                       AIStorageUtils.SORT_TYPE_FLOAT, 
                                                       AIStorageUtils.SORT_ASCENDING )
    NTotalJobs = len( ListOfApps )
    #print "### Found", NTotalJobs, "apps. Sorting...done."
                                                    
    startTime = float(ListOfApps[0][1]['runTime'])
    if startTime < 0.0: startTime = 0.0
    for (id, App) in ListOfApps: 
        App['runTime'] = float(App['runTime']) - startTime
        #print "### runTime:", App['runTime'], "\n"
        if App['runTime'] < 0.0: App['runTime'] = 0.0
        #print "ID", id, "starts in %.3fs." % float(App['runTime']/1000.0)
        
    #-- generate all work units
    try:
        os.mkdir( OutputDir )
    except:
        pass
    FirstSubmission = time.time()
    CommandLinesList = []
    for (id, App) in ListOfApps: 
        #-- generate item
        CommandLineItem = {}
        CommandLineItem['id'] = id
        CommandLineItem['firstSubmission'] = FirstSubmission
        CommandLineItem['startTime'] = float(App['runTime']/1000.0)
        #CommandLineItem['commandLine'] = "drunner -g -e -o -f %s 1> %s.out 2> %s.err &" % (App['jdf'], id, id)
        
        if OneFile == 0:
            StdOutFile = os.path.join( OutputDir, "%s.out" % id )
            StdErrFile = os.path.join( OutputDir, "%s.err" % id )
            ActualCommand = "%s 1> %s 2> %s" % ( App['submitCommand'], StdOutFile, StdErrFile )
            #ActualCommand = "%s 2>%s" % ( App['submitCommand'], StdErrFile )
        else:
            StdOutFile = os.path.join( OutputDir, "onefile.out" )
            StdErrFile = os.path.join( OutputDir, "onefile.err" )
            ActualCommand = "%s 1>> %s 2>> %s" % ( App['submitCommand'], StdOutFile, StdErrFile )
            #ActualCommand = "%s" % ( App['submitCommand'] )

        if NoBackground == 0:
            CommandLineItem['commandLine'] = ActualCommand #+ ' &'
        else:
            CommandLineItem['commandLine'] = ActualCommand
        
	CommandLineItem['stdout'] = StdOutFile
	CommandLineItem['stderr'] = StdErrFile
	CommandLineItem['onefile'] = OneFile        

        #-- amod v.0.12: just generate commands
        CommandLineItem['NoSubmit'] = NoSubmit
        CommandLineItem['testid'] = testid
        CommandLineItem['projectid'] = projectid
        CommandLineItem['testerid'] = testerid
        CommandLineItem['timediff'] = timediff
            
        #-- append item
        #if os.path.exists(App['jdf']):
        CommandLinesList.append(CommandLineItem)
        #else:
        #    print "Could not locate JDF", App['jdf'], "... skipping job"
        
    #-- build a WorkRequest object for each work unit
    requests = ASPNThreadPool.makeRequests(submitJob, CommandLinesList, printSubmitJobResults)
    
    #-- create a pool of NPoolThreads worker threads
    StdOutLock.acquire()
    print "[wl-submit.py] Starting a thread pool with", NPoolThreads, "threads"
    StdOutLock.release()

    submitThreadPool = ASPNThreadPool.ThreadPool(NPoolThreads, StdOutLock)
    
    
    StartSubmissionTime = time.time()
    #-- add all work units into the thread pool
    #   NOTE: We expect the thread pool to be based on Queues,
    #         beacause our applications need to be run at specified times
    #         and the submit job waits until the current work unit is done
    #         -> if we are NOT using Queues, it may happen that a work unit
    #         that needs to be submitted at time T will get submitted much 
    #         later, due to other jobs starting the submission before it,
    #         but waiting for their later start time
    for req in requests:
        submitThreadPool.putRequest(req)
        #DEBUG:print req.args

        StdOutLock.acquire()
        print "[Pool] Work request #%s added (id=%s, start time=%.3f)." % \
              (req.requestID, req.args[0]['id'], req.args[0]['startTime'])
        StdOutLock.release()
    
    #-- wait for all submissions to be completed
    submitThreadPool.wait()
    while 1:
        try:
            submitThreadPool.poll()
            EndSubmissionTime = time.time()
            #print "Main thread working..."
            time.sleep(0.5)
        except (KeyboardInterrupt, ASPNThreadPool.NoResultsPending):
            break
    
    EndSubmissionTime = time.time()
    NTotalJobsInQueue = len(submitThreadPool.workRequests)

    # should send to the database the 'onefile.out' and 'onefile.err' (not tested)

    if OneFile != 0:
        StdOutFile = os.path.join(OutputDir, "onefile.out")
        StdErrFile = os.path.join(OutputDir, "onefile.err")

        try:
            fin = open(StdOutFile)
            lines = (fin.read()).split("\n")

            for line in lines:
                if (len(line) > 1):
                    sLine = "\n" + LOGFILE_PREFIX + str(testid) + "\1" + str(projectid) + "\1" + str(testerid) + "\1" + "0" + "\1" + line + "\n"

                    StdOutLock.acquire()   
                    sys.stdout.write(sLine)
                    StdOutLock.release()

            fin.close()
        except:
                pass

        try:
            fin = open(StdErrFile)          
            lines = (fin.read()).split("\n")

            for line in lines:
                if (len(line) > 1):
                    sLine = "\n" + LOGFILE_PREFIX + str(testid) + "\1" + str(projectid) + "\1" + str(testerid) + "\1" + "0" + "\1" + line + "\n"

                    StdOutLock.acquire()
                    sys.stdout.write(sLine)
                    StdOutLock.release()   

            fin.close()
        except:
                pass

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
        opts, args = getopt.getopt(argv[1:], "ht:", ["help", "threads=", "version", "nosubmit", "nobackground", "onefile", "testid=", "projectid=", "testerid=", "starttime="])
    except getopt.GetoptError:
        print "Error while converting options: unknown option(s) encountered.\n\n"
        usage(os.path.basename(sys.argv[0]))
        sys.exit(2)

    NThreads = 5
    NoSubmit = 0
    OneFile = 0
    NoBackground = 0
    testid = 0
    testerid = 0
    starttime = time.time()
    projectid = "default"

    #print opts
    #print args    

    for opt, arg in opts:
        #print "x", opt, arg

        if opt in ["-h", "--help"]:
            usage(os.path.basename(sys.argv[0]))
            sys.exit()
        elif opt in ["--version"]:
            version()
            sys.exit()
        elif opt in ["-t", "--threads"]: 
            try:
                NThreads = int(arg.strip()) 
            except ValueError:
                NThreads = 5
        elif opt in ["--nosubmit"]:
            NoSubmit = 1
        elif opt in ["--nobackground"]:
            NoBackground = 1
        elif opt in ["--onefile"]:
            OneFile = 1
        elif opt in ["--testid"]:
	    print "#### wl-submit arg: %s \n" % arg
            testid = int(arg.strip())
            #print testid
        elif opt in ["--testerid"]:
            testerid = int(arg.strip())
            #print testerid
        elif opt in ["--starttime"]:
            starttime = float(arg.strip())
            #print starttime
        elif opt in ["--projectid"]:
            projectid = str(arg.strip())
        else:
            print "Unknown parameter", opt

    #sys.exit(0)
    
    if len(argv) < 1:
        print "Error: No workload file given.\n\n"
        usage(os.path.basename(sys.argv[0]))
        sys.exit(3)
        
    WorkloadFileName = argv[0];
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
    StartSubmissionTime, EndSubmissionTime, NTotalJobs, NTotalJobsInQueue = \
        runWL( WorkloadDir, handlerXML, NThreads, NoSubmit, NoBackground, OneFile, testid, projectid, testerid, starttime - time.time() )
    print "%s All done" % time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
    
    tstart = time.strftime('%H:%M:%S', time.gmtime(StartSubmissionTime))
    tend = time.strftime('%H:%M:%S', time.gmtime(EndSubmissionTime))
    
    
    print "------ SUBMISSION SUMMARY ---------"
    print "Started submission at %s" % tstart
    print "Ended submission at %s" % tend
    print "Submission total time/Total Jobs/submitted/Jobs per second"
#          0123456789012345678901234567890123456789012345678901234567890123456789
#          0         1         2         3         4         5         6  
    DeltaTime = float(EndSubmissionTime - StartSubmissionTime)
    if DeltaTime > 0.e-8:
        Avg = float(NTotalJobs - NTotalJobsInQueue) / DeltaTime
    else:
        Avg = 0.0
    #print "   %15.3f   /  %6d  / %6d  /  %.3f" % \
    #   ( DeltaTime, NTotalJobs, NTotalJobs - NTotalJobsInQueue, Avg )

if __name__ == "__main__":

    main(sys.argv[1:]) 
    
    
    