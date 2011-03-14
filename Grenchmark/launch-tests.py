#!/usr/bin/python
"""
NAME

    launch-pisa-tests -- Grenchmark workload generator

SYNOPSIS
    %(progname)s [OPTIONS] [Test 1 name,...,Test n name|all]
    
DESCRIPTION
    launch-pisa-tests is part of the Grenchmark project. For more information, please
    visit the Grenchmark web-page at http://www.pds.ewi.tudelft.nl/~iosup/index.html.
             
OPTIONS:
    Arguments:
    --help 
      Print a summary of the wl-gen-simple options and exit.
    
    --delay=<int>, -d <int>
      the delay time between tests, in s [default=600 (=600s=10m)]
    
    --key=<string>, -k <string>
      a prefix key for your test [default=600 (=600s=10m)]
    
    --threads=<int>, -t <int>
      number of submitter threads [default=5]
    
    --ntimes=<int>, -n <int>
      number of times to run the requested tests [default=1]
    
    Flags:
    --nogenerate
      do not generate tests
    
    --nosubmit
      do not submit the generated tests
    
    --noarchive
      do not archive generated/submitted tests 
      (after finishing genrating/submitting)
      The archive names are 
          <TestName>_gen.tgz, for generated tests
          <TestName>_res.tgz, for submitted tests
    
    Other:
    --version
      Display wl-gen-simple version and copyright.
    

SAMPLE RUNS:

Example 1. TODO

AVAILABLE TESTS:
    %(AvailableTests)s

AUTHOR:
    Alexandru Iosup 
    A.Iosup@ewi.tudelft.nl
    http://www.pds.ewi.tudelft.nl/~iosup/index.html

"""

__proggy = "launch-pisa-tests";
__rev = "1.0";
__proggy_stamp__ = "%s v%s" % (__proggy, __rev);
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'launch-pisa-tests.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:14:45 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python" 


#---------------------------------------------------
# Log:
# 15/09/2005 A.I. 0.1  Started this app
#---------------------------------------------------


import os
import os.path
import time
import getopt
import string 

import sys
if "utils" not in sys.path: sys.path.append("utils")
import AIStorageUtils 

class Defaults:
    DelayBetweenTests = 600
    NThreads = 5
    NTimes = 1

class TestDataFields:
    WL_DESC_FILE_NAME = 0
    WL_DURATION = 1
    WL_DIR = 2
    WL_DESC = 3
    WL_PRE_SETUP = 4
    WL_POST_SETUP = 5

TestData = {
   'swf1' : ['swf_das2-fs3_1x.in', 10000000, 'swf1x', 'das2-fs3 workload jobs, 1x', 
            '', './swf_post.sh'],
   'swf10' : ['swf_das2-fs3_10x.in', 10000000, 'swf10x', 'das2-fs3 workload jobs, 10x', 
            '', './swf_post.sh'], 
   'swf50' : ['swf_das2-fs3_50x.in', 10000000, 'swf50x', 'das2-fs3 workload jobs, 50x', 
            '', './swf_post.sh'],  
   'swf100' : ['swf_das2-fs3_100x.in', 10000000, 'swf100x', 'das2-fs3 workload jobs, 100x', 
            '', './swf_post.sh'],
   'swfmix2_das2_ctc' : ['swf_mix2_das2_ctc.in', 10000000, 'swfmix2_das2_ctc', 'das2-fs3 and ctc workloads', 
            '', './swf_post.sh'],
   'swfmix2_das2_osc' : ['swf_mix2_das2_osc.in', 10000000, 'swfmix2_das2_osc', 'das2-fs3 and osc workloads', 
            '', './swf_post.sh'],
   'swfmix2_das2_sdsc96' : ['swf_mix2_das2_sdsc96.in', 10000000, 'swfmix2_das2_sdsc96', 'das2-fs3 and sdsc96 workloads', 
            '', './swf_post.sh']
   }

def LaunchCommand( Command, StdOutFile = None, StdErrFile = None, Launch = 1 ):
    if StdOutFile:
        Command = Command + ' >' + StdOutFile
    if StdErrFile:
        Command = Command + ' 2>' + StdErrFile
    print "Executing command:"
    print Command
    
    if Launch > 0:
        os.system( Command )


def usage(progname):
    global Defaults
    
    ReplaceDic = {}
    VarsDic = vars();
    for Key in VarsDic.keys():
        ReplaceDic[Key] = VarsDic[Key]
    ListOfTestsData = AIStorageUtils.dict_sortbykey( TestData, AIStorageUtils.SORT_ASCENDING )
    ListOfSortedNames = []
    for Name, Dummy in ListOfTestsData:
        ListOfSortedNames.append(Name)
    ReplaceDic['AvailableTests'] = ','.join(ListOfSortedNames)
    
    print __doc__ % ReplaceDic

def version():
    print "Version: ", __version__
    print "Date: ", __date__
    print __copyright__, "(", __email__, ")"

def main(argv):                  

    global Defaults
           
    OneCharOpts = "hd:t:n:k:"
    MultiCharList = [
        "help", "delay=", "threads=", "ntimes=", "key=", 
        # here the params with no one char version
        "version", "nogenerate", "ng", "nosubmit", "ns"
        ]
        
    try:                                
        opts, args = getopt.getopt( argv, OneCharOpts, MultiCharList )
    except getopt.GetoptError:
        usage(os.path.basename(sys.argv[0]))
        sys.exit(2)
    
    
    DoSubmit = 1
    DoGenerate = 1
    DoArchive = 1
    DelayBetweenTests = Defaults.DelayBetweenTests
    NThreads = Defaults.NThreads
    NTimes = Defaults.NTimes
    Key = None

    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            usage(os.path.basename(sys.argv[0]))
            sys.exit()
        elif opt in ["--version"]:
            version()
            sys.exit()
        elif opt in ["--nosubmit"]: 
            DoSubmit = 0
        elif opt in ["--nogenerate"]: 
            DoGenerate = 0
        elif opt in ["--noarchive"]: 
            DoArchive = 0
        elif opt in ["-k", "--key"]: 
            Key = arg.strip()
        elif opt in ["-d", "--delay"]: 
            try:
                DelayBetweenTests = int(arg.strip())
                print "Delay between tests set to %ds.\n" % DelayBetweenTests
            except ValueError, e:
                print e
                DelayBetweenTests = Defaults.DelayBetweenTests
                print "Delay between tests set to default value (%d).\n" % DelayBetweenTests
        elif opt in ["-t", "--threads"]:
            try:
                NThreads = int(arg.strip())
                print "Number of submit threads set to %ds.\n" % NThreads
            except ValueError, e:
                print e
                NThreads = Defaults.NThreads
                print "Number of submit threads set to default value (%d).\n" % NThreads
        elif opt in ["-n", "--ntimes"]:
            try:
                NTimes = int(arg.strip())
                print "Number of times to repeat tests set to %ds.\n" % NTimes
            except ValueError, e:
                print e
                NTimes = Defaults.NTimes
                print "Number of times to repeat tests set to default value (%d).\n" % NTimes
    
    if len(args) != 1:
        print "--------------------------"
        print "ERROR!", "Incorrect test names field possible", "Needed len=1, current", len(args), args
        print
        usage(os.path.basename(sys.argv[0]))
        sys.exit()
        
    ListOfTests = []
    if args[0] == 'all':
        for TestName in TestData:
            ListOfTests.append(TestName)
    else:
        try:
            ListOfTests = args[0].split(',')
        except:
            print "ERROR!", 'Malformed test names list field', "'"+args[0]+"'"
            usage(os.path.basename(sys.argv[0]))
            sys.exit()
    
    #ListOfTestsData = AIStorageUtils.dict_sortbykey( TestData, AIStorageUtils.SORT_DESCENDING )
    
    #--- run all tests NTimes, in the order specified by the user
    for currentRun in xrange(NTimes):
        print "# RUN %d at %d" % (currentRun, time.time())
        index = 0
        for TestName in ListOfTests:
            try:
                Test = TestData[TestName.lower()]
            except: 
                print 'WARNING!', 'Cannot find ', "'"+TestName+"'", '...skipping test'
                continue
            print '#TLaunch %d' % time.time()
            print time.strftime('%a, %d %b %Y %H:%M:%S', time.gmtime()), ':', 
            print 'Launching test', TestName, 'comprising', Test[TestDataFields.WL_DESC]
            
            Dummy, WLDescFileName = os.path.split(Test[TestDataFields.WL_DESC_FILE_NAME])
            
            #--- generate test, if needed
            print '#TGenStart %d' % time.time()
            GenerateOutputDir = "%d-%s" % (currentRun, Test[TestDataFields.WL_DIR])
            if Key: GenerateOutputDir = Key+"-"+GenerateOutputDir
                
            GenerateCommandLine = "./wl-gen.py -w %s -d %s -o %s" % \
                      (Test[TestDataFields.WL_DESC_FILE_NAME],
                       str(Test[TestDataFields.WL_DURATION]),
                       GenerateOutputDir)
            #--- mod!!! currentRun becomes the first prefix
            GenerateOutputFileName = '%d-pisa-%d_%s' % (currentRun, index, WLDescFileName + '.out')
            if Key: GenerateOutputFileName = Key+"-"+GenerateOutputFileName
            LaunchCommand( GenerateCommandLine, GenerateOutputFileName, '&1', DoGenerate )
            print '#TGenEnd %d' % time.time()
                    
            #--- archive test directory, if needed
            if DoGenerate > 0 and DoArchive > 0:
                ArchiveFileName = "%d-%s_gen.tgz" % (currentRun, TestName)
                if Key: ArchiveFileName = Key+"-"+ ArchiveFileName
                LaunchCommand( "tar zcf %s %s %s %s/*" % \
                      (ArchiveFileName, Test[TestDataFields.WL_DESC_FILE_NAME], 
                       GenerateOutputFileName, GenerateOutputDir),
                      "/dev/null", "&1" )
                    
            #--- launch test, if needed
            print '#TSubStart %d' % time.time()
            
            #--- perform the pre setup
            if DoSubmit > 0 :
                if len(Test[TestDataFields.WL_PRE_SETUP]) > 0:
                    print '#TSubPreSetupStart %d' % time.time()
                    LaunchCommand( Test[TestDataFields.WL_PRE_SETUP] )
                    print '#TSubPreSetupEnd %d' % time.time()
                    
            SubmitOutputFileName = '%s/submit.out' % GenerateOutputDir
            SubmitErrorFileName = '%s/submit.err' % GenerateOutputDir
            LaunchCommand( \
                    "./wl-submit.py -t %s %s/wl-to-submit.wl" % (str(NThreads), GenerateOutputDir),
                    SubmitOutputFileName, SubmitErrorFileName, DoSubmit)
            print '#TSubEnd %d' % time.time()
                    
            #--- sleep between tests, if needed
            if DelayBetweenTests > 0:
                print "Sleeping for %d seconds..." % DelayBetweenTests
                print "Press (Ctrl+C) to skip sleeping"
                try:
                    time.sleep( DelayBetweenTests )
                except:
                    pass
                    
            #--- perform the post setup
            if DoSubmit > 0 :
                if len(Test[TestDataFields.WL_PRE_SETUP]) > 0:
                    print '#TSubPostSetupStart %d' % time.time()
                    LaunchCommand( Test[TestDataFields.WL_POST_SETUP] )
                    try:
                        time.sleep(10)
                    except:
                        pass
                    print '#TSubPostSetupEnd %d' % time.time()
                
            #--- archive output directory, if needed
            #    NOTE! This is done after the sleep time, so that all things
            #          submitted nonblocking have time to finish
            if DoSubmit > 0 and DoArchive > 0:
                # Note: the Submit*FileName files are placed in the 
                #       GenerateOutputDir dir, so they *do* get archived
                ArchiveFileName = "%d-%s_res.tgz" % (currentRun, TestName)
                if Key: ArchiveFileName = Key+"-"+ ArchiveFileName
                LaunchCommand( "tar zcf %s %s %s %s/*" % \
                      (ArchiveFileName, Test[TestDataFields.WL_DESC_FILE_NAME], 
                       GenerateOutputFileName, GenerateOutputDir),
                      "/dev/null", "&1" )
                
            print '#TEnd %d' % time.time()
            print time.strftime('%a, %d %b %Y %H:%M:%S', time.gmtime()),':', 'Test', TestName, ' ended'
            print
            index = index + 1

if __name__ == "__main__":

    main(sys.argv[1:]) 
    



