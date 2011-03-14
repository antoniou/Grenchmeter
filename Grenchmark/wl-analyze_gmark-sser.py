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

"""

__proggy = "wl-analyze";
__rev = "0.15";
__proggy_stamp__ = "%s v%s" % (__proggy, __rev);
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'wl-parse.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:14:45 $"
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
import AIStorageUtils 
import AISystemUtil
import WLDocHandlers

ListOfApps = {}

def parseKOALASubmissionFile( FileName ):
    # looking for a file containing lines of type:
    # (1) <Time>,...:...  [timestamped event]
    # (2) #GM  <Time x 1000> <KOALA Job ID>&<ComponentID> <Globus message name> [Globus message]
    # (3) #END <Time x 1000> <KOALA Job ID>&<ComponentID> <SUCCESS|FAILED> [Globus message]
    
    FirstIdentifiedTime = None
    StartTime = None
    EndTime = None
    
    JobID = None
    GlobusMessages = {}
    JobResult = 'UNDEFINED'
    
    LineNo = 0
    InFile = open( FileName )
    while 1:
        lines = InFile.readlines(100000) # buffered read
        if not lines:
            break
        #-- process lines
        for line in lines: 
            LineNo = LineNo + 1
            if len(line) == 0:
                continue #-- empty line
                
            if line.find('#GM') >= 0:
                try:
                    prefix, timex1000, kjid, gmsg = line.strip().split(' ', 3)
                except Exception, e:
                    print e
                    print "WARNING!", "Cannot parse line", LineNo, "(", line, ")", "in file", FileName
                    
                try:
                    TimeStamp = int(timex1000) / 1000
                except:
                    print "WARNING!", "Wrong timestamp (", timex1000, ") in file", FileName, "on line", LineNo
                    
                if not StartTime or StartTime > TimeStamp: StartTime = TimeStamp
                if not EndTime or EndTime < TimeStamp: EndTime = TimeStamp
                    
                try:
                    KOALAJobID, ComponentID = kjid.strip().split('&', 1)
                    KOALAJobID = int(KOALAJobID)
                    ComponentID = int(ComponentID)
                except:
                    print "WARNING!", "Wrong JobID/Component number (", kjid, ") in file", FileName, "on line", LineNo
                    
                GlobusMessage = gmsg.strip()
                
                if GlobusMessage not in GlobusMessages.keys():
                    GlobusMessages[GlobusMessage] = []
                GlobusMessages[GlobusMessage].append({'TimeStamp':TimeStamp, 'JobID':KOALAJobID, 'ComponentID': ComponentID})
                
                if JobID and JobID != KOALAJobID:
                    print "WARNING!", "Wrong JobID number (", KOALAJobID, "instead of", JobID, ") in file", FileName, "on line", LineNo
                JobID = KOALAJobID
                    
            elif line.find('#END') >= 0:
                try:
                    prefix, timex1000, KOALAJobID, result = line.strip().split(' ', 3)
                except Exception, e:
                    print e
                    print "WARNING!", "Cannot parse line", LineNo, "(", line, ")", "in file", FileName
                    
                try:
                    TimeStamp = int(timex1000) / 1000
                except:
                    print "WARNING!", "Wrong timestamp (", timex1000, ") in file", FileName, "on line", LineNo
                    
                if not StartTime or StartTime > TimeStamp: StartTime = TimeStamp
                if not EndTime or EndTime < TimeStamp: EndTime = TimeStamp
                    
                try:
                    KOALAJobID = int(KOALAJobID.strip())
                except:
                    print "WARNING!", "Wrong JobID number (", KOALAJobID, ") in file", FileName, "on line", LineNo
                    
                JobResult = result.strip()
                
                if JobID and JobID != KOALAJobID:
                    print "WARNING!", "Wrong JobID number (", KOALAJobID, "instead of", JobID, ") in file", FileName, "on line", LineNo
                JobID = KOALAJobID
                
            else:
                try:
                    # scan for HH:MM:SS strings 07:55:53
                    Hour = int(line[0:2])
                    Minute = int(line[3:5])
                    Second = int(line[6:8])
                    TimePrefix = int (line[0:8])
                except:
                    continue
                
                TimeStamp = Hour * 3600 + Minute * 60 + Second
                if not FirstIdentifiedTime or FirstIdentifiedTime > TimePrefix:
                    # next day's results
                    TimeStamp = TimeStamp + Hour * 3600
                if not StartTime or StartTime > TimeStamp: StartTime = TimeStamp
                if not EndTime or EndTime < TimeStamp: EndTime = TimeStamp
                    
    # close the WL desc file
    InFile.close()
    
    if not StartTime or not EndTime:
        TurnAroundTime = None
    else:
        TurnAroundTime = EndTime - StartTime
    
    return (TurnAroundTime, JobID, JobResult, GlobusMessages)
    
def getOutputFiles( JDFFile ):
    ListOfFiles = []
    LineNo = 0
    InFileName = JDFFile
    InFile = open( InFileName )
    while 1:
        lines = InFile.readlines(100000) # buffered read
        if not lines:
            break
        #-- process lines
        for line in lines: 
            LineNo = LineNo + 1
            if len(line) == 0:
                continue #-- empty line
                
            if line.find('stdout') >= 0 or line.find('stderr') >= 0:
                pos1 = line.find('"')
                if pos1 < 0: continue
                pos2 = line[pos1+1:].find('"')
                if pos2 < 0: continue
                FileName = line[pos1+1:pos1+1+pos2]
                if FileName.find('jdfs/') >= 0:
                    FileName = FileName[FileName.find('jdfs/') + len('jdfs/'):]
                ListOfFiles.append(FileName)
    return ListOfFiles
    
def parseSSEROutputFile( FileName ):
    
    RunTime = None
    LineNo = 0
    InFileName = FileName
    InFile = open( InFileName )
    SummaryLines = 0
    while 1:
        lines = InFile.readlines(100000) # buffered read
        if not lines:
            break
        #-- process lines
        for line in lines: 
            LineNo = LineNo + 1
            if len(line) == 0:
                continue #-- empty line
                
            if line.find('SUMMARY') >= 0:
                SummaryLines = 1
                ##print "Found SUMMARY"
                continue
                
            if SummaryLines == 0: continue
            
            if line.find('Runtime') >= 0:
                ##print "Found Runtime"
                # Runtime    : 18.602 (s) 
                pos1 = line.find(':')
                if pos1 < 0: continue
                pos2 = line[pos1+1:].find('(')
                if pos2 < 0: continue
                try:
                    RunTime = int(float(line[pos1+1:pos1+1+pos2].strip()) + 1.0)
                except:
                    print '>>>', line[pos1+1:pos1+1+pos2].strip()
                    pass
                
    return RunTime
    
class ItemTimer:
    def __init__(self):
        self.reset()
    def reset(self):
        self.Min = None
        self.Max = None
        self.Total = 0.0
        self.NItems = 0
    def addValue(self, value):
        if not self.Min or self.Min > value: self.Min = value
        if not self.Max or self.Max < value: self.Max = value
        self.Total = self.Total + value
        self.NItems = self.NItems + 1
    def getAverage(self):
        if self.NItems > 0: return float(self.Total) / self.NItems
        return 0.0
    def getInfo(self):
        if self.NItems > 0:
            return (self.getAverage(), self.Min, self.Max, self.NItems)
        else:
            return (self.getAverage(), 0, 0, self.NItems)

def parseWL( MainDir, XMLhandler ):
    
    DictionaryOfApps = XMLhandler.getDictionaryOfApplications()
    ListOfApps = AIStorageUtils.dict_sortbyvalue_dict( DictionaryOfApps, 'runTime', 
                                                       AIStorageUtils.SORT_TYPE_FLOAT, 
                                                       AIStorageUtils.SORT_ASCENDING )
    NTotalJobs = len( ListOfApps )
    print "Found", NTotalJobs, "apps. Sorting...done."
    
    RunDir = os.path.join( MainDir, "run" )
    JDFsDir = os.path.join( MainDir, "jdfs" )
    
    Timers = {}
    Timers['TurnAround'] = ItemTimer()
    Timers['SuccessfulTurnAround'] = ItemTimer()
    Timers['SuccessfulRun'] = ItemTimer()
    
    DataList = []
    for (id, App) in ListOfApps: 
        #-- generate item
        DataItem = {}
        DataItem['id'] = id
        DataItem['name'] = App['name']
        DataItem['jdf'] = App['jdf']
        DataItem['SubmitStdOut'] = os.path.join( RunDir, "%s.out" % id ).replace(':', '-')
        DataItem['SubmitStdErr'] = os.path.join( RunDir, "%s.out" % id ).replace(':', '-')
        TurnAroundTime, RunnerJobID, JobResult, GlobusMessages = parseKOALASubmissionFile( DataItem['SubmitStdOut'] )
        #print RunnerJobID, JobResult, TurnAroundTime
        if RunnerJobID:
            DataItem['RunnerJobID'] = RunnerJobID
            DataItem['JobResult'] = JobResult
            DataItem['TurnAroundTime'] = TurnAroundTime
            DataItem['GlobusMessages'] = GlobusMessages
            DataList.append( DataItem )
            if TurnAroundTime:
                Timers['TurnAround'].addValue(TurnAroundTime)
                if JobResult == 'SUCCESS': 
                    Timers['SuccessfulTurnAround'].addValue(TurnAroundTime)
                    if os.path.exists(DataItem['jdf']):
                        OutputFilesList = getOutputFiles(DataItem['jdf'])
                        for FileName in OutputFilesList:
                            DirFileName = os.path.join(JDFsDir, FileName)
                            RunTime = parseSSEROutputFile( DirFileName )
                            if RunTime:
                                Timers['SuccessfulRun'].addValue(RunTime)
                            ##else:
                            ##    print "RunTime", RunTime, "RunTimes", RunTimes
                
    print "All     TurnAround time [s]: avg=%8.3f | min=%8d | max=%8d | #=%8d" % Timers['TurnAround'].getInfo()
    print "SUCCESS TurnAround time [s]: avg=%8.3f | min=%8d | max=%8d | #=%8d" % Timers['SuccessfulTurnAround'].getInfo()
    print "SUCCESS Run time        [s]: avg=%8.3f | min=%8d | max=%8d | #=%8d" % Timers['SuccessfulRun'].getInfo()
##        #-- append item
##        if os.path.exists(App['jdf']):
##            CommandLinesList.append(CommandLineItem)
##        else:
##            print "Could not locate JDF", App['jdf'], "... skipping job"
        
    

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
        opts, args = getopt.getopt(argv, "ht:", ["help", "threads=", "version", "nosubmit", "nobackground", "onefile"])
    except getopt.GetoptError:
        print "Error while converting options: unknown option(s) encountered.\n\n"
        usage(os.path.basename(sys.argv[0]))
        sys.exit(2)
    
    NThreads = 5
    NoSubmit = 0
    OneFile = 0
    NoBackground = 0
    
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
            except ValueError:
                NThreads = 5
        elif opt in ["--nosubmit"]:
            NoSubmit = 1
        elif opt in ["--nobackground"]:
            NoBackground = 1
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
        
    parseWL( os.path.dirname(WorkloadFileName), handlerXML )
    
    print "%s All done" % time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))
    

if __name__ == "__main__":

    main(sys.argv[1:]) 
    
    
    
