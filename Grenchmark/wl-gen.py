#!/usr/bin/python

"""
NAME

    wl-gen -- Grenchmark workload generator

SYNOPSIS
    %(progname)s [OPTIONS]

DESCRIPTION
    wl-gen generates a set of job description files (JDF) for testing 
    Grid schedulers. It supports natively the KOALA scheduler 
    (http://www.st.ewi.tudelft.nl/koala/index.html) JDF.
    
    wl-gen is part of the Grenchmark project. For more information, please
    visit the Grenchmark web-page at http://www.pds.ewi.tudelft.nl/~iosup/index.html.
             
OPTIONS:
    Arguments:
    --help 
      Print a summary of the wl-gen-simple options and exit.
    
    --outdir=<string>, -o <string>
      use as the program output directory [default=out/]
      
    --jdfgen=<string>, -j <string>
      the JDF generator name [default=koala-jdf]
      This name has to correspond to a python file jdfprint/name.py, 
      so that the file is loaded at run-time, and its generateJDF function
      used to produce the JDF output.
    
    --duration=<string>, -d <string>
      the total submit time, in ms [default=100,000 (100s)]
    
    Flags:
    --force, -f
      force writing into output directory even if it exists
       
    Other:
    --version
      Display wl-gen-simple version and copyright.
    

SAMPLE RUNS:

Example 1. Generate a workload depending on the workload description file, 
           with all other parameters ser to default values:
Step1. Verify the workload description file
    $ cat wl-desc.in
    # File-type: text/wl-spec
    # WL Unit ID<tab>Total # of jobs<tab>Job Type<Tab>Site structure type<Tab>Detailed Site structure<Tab>Other info
    #ID    Total    AppType    SiteType    SiteInfo    OtherInfo
    0    2    sser    single    *:?    -
    1    4    sser    unordered    -    NSites=2,DifferentSites=false
    ?    ?    sser    ordered    fs3:2,fs2:1,fs1:1    -
    ?    5    sser    semi-ordered    fs3:2,*:1    NSites=3,DifferentSites=true
    ?    5    fake    semi-ordered    fs3:2,*:1    NSites=3,DifferentSites=true

Step2. Run the workload generator
    $ wl-gen
    STATUS! Load workload unit generators.
    ...
    Got 1 generators!

    STATUS! Load JDF generators.
    ...
    Got 1 generators!

    STATUS! Load site file.
    Got 4 sites from 'grid-sites.xml'.

    STATUS! Load workload description.
    Start getting a workload decription from wl-desc.in
    Identified wl-desc.in as text workload description file
    Line 7 New ID 2 generated for this unit.
    Line 7 Total amount of jobs is computed to be 4
    Line 8 New ID 3 generated for this unit.
    Line 9 New ID 4 generated for this unit.
    Unknown App Type 'fake' on line 9 ...skipping line
    Got 4 workload units from 'wl-desc.in'.

    STATUS! Starting workload generation!
    STATUS! Writing workload JDFs
    STATUS! Write JDF file out\jdfs\jdf-0\wl-unit-0.jdf ...done
    STATUS! Write JDF file out\jdfs\jdf-1\wl-unit-1.jdf ...done
    STATUS! Write JDF file out\jdfs\jdf-2\wl-unit-2.jdf ...done
    STATUS! Write JDF file out\jdfs\jdf-3\wl-unit-3.jdf ...done
    STATUS! Writing workload to 'out\wl-to-submit.wl'.
    
    SUCCESS! Workload generation complete!

Example 2. Generate a workload depending on the workload description file, 
           with total workload submission time set to 1 second, and
           all other parameters ser to default values:
Step1. Verify the workload description file
    $ cat wl-desc.in
    [see Example 1 / Step 1]

Step2. Run the workload generator, with workload submission time parameter set:
    $ wl-gen -d 1000
    [see Example 1 / Step 2]
    Note that the parameter is given in miliseconds, so 1000 for 1 second.
    
Step 3. Verify generated workload:
    $ cat out/wl-tosubmit.wl
    <!-- File-type: xml/wl-submit-desc -->
    <!-- Generated by Grenchmark/WLMain v0.01 on 2005-08-12_12-31-->
    <workload name="WL-2005-08-12_12-31-943">
        <app 
            id="0" 
            name="0_sser" 
            description="Workload unit 0, comprising only applications of type sser." 
            jdf="out\jdfs\jdf-0\wl-unit-0.jdf" 
            runTime="411" 
            submitCommand="krunner -g -e -o -f out\jdfs\jdf-0\wl-unit-0.jdf" 
        />
    ...
    
    Note how the 'runTime' attributes of each job are below or equal to 1000.


AUTHOR:
    Alexandru Iosup 
    A.Iosup@ewi.tudelft.nl
    http://www.pds.ewi.tudelft.nl/~iosup/index.html

"""

__proggy = "wl-gen";
__rev = "0.31";
__proggy_stamp__ = "%s v%s" % (__proggy, __rev);
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'wl-gen.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:12:39 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python" 


#---------------------------------------------------
# Log:
# 11/08/2005 A.I. 0.1  Started this app
#---------------------------------------------------

import sys
import os
import getopt
import string 
import time

#---Import files from the utils directory
if "utils" not in sys.path:
    sys.path.append("utils")
import AIFinalVersion
import AIRandomUtils
import WLDocHandlers
import WLLoader
import WLMain
import FixedUtil

# TODO : change this to 0 in final version
if AIFinalVersion.IsFinalVersion == 0:
    DefaultForce = 1 # force overwriting the output directory
else:
    DefaultForce = 0 # don't force overwriting the output directory


def FileOrExit( FileName, FileDesc = "this" ):
    if not os.path.isfile( FileName ):
        if os.path.exists( FileName ):
            print "\n\n****\nError: Cannot locate %s file (%s is not a file)!\n****\n" % \
                ( FileDesc, FileName )
        else:
            print "\n\n****\nError: Cannot locate %s file (%s does not exist)!\n****\n" % \
                ( FileDesc, FileName )
        usage(os.path.basename(sys.argv[0]))
        sys.exit(3)


def usage(progname):
    print __doc__ % vars() 

def version():
    print "Version: ", __version__
    print "Date: ", __date__
    print __copyright__, "(", __email__, ")"

def main(argv):                  

    OneCharOpts = "hfo:r:s:w:j:d"
    MultiCharList = [
        "help", "force", "outdir=", 
        "workload=", "sitesfile=", "jdfgen=", "duration=", 
        # here the params with no one char version
        "version","arrival=",'useIDs='
        ]
        
    try:                                
        opts, args = getopt.getopt( argv, OneCharOpts, MultiCharList )
    except getopt.GetoptError:
        usage(os.path.basename(sys.argv[0]))
        sys.exit(2)
    
    OutDir = 'out' ## os.path.join(os.path.abspath('./'), 'out') 
    DoGenerateFull = 0
    DoGenerateRandom = 1
    NRandomTests = 5
    NComponents = 3
    TestTypes = ["sser"]
    WorkloadDescriptionFileName = "wl-desc.in"
    arrivalDistr = None
    jobIDsFile = None
    
    SitesFileName = "grid-sites.xml"
    JDFGenName = "koala-jdf"
    
    DeafultSubmitDurationMS = 100000
    SubmitDurationMS = DeafultSubmitDurationMS # 100 seconds = 100000 ms
    
    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            usage(os.path.basename(sys.argv[0]))
            sys.exit()
        elif opt in ["--version"]:
            version()
            sys.exit()
        elif opt in ["-o", "--outdir"]: 
            OutDir = arg.strip() 
        elif opt in ["-d", "--duration"]: 
            try:
                SubmitDurationMS = int(arg.strip())
                print "Submit duration set to %d.\n" % SubmitDurationMS
            except ValueError, e:
                print e
                SubmitDurationMS = DeafultSubmitDurationMS
                print "Submit duration set to default value (%d).\n" % SubmitDurationMS
                
        elif opt in ["-j", "--jdfgen"]: 
            JDFGenNames = arg.strip() 
            JDFGenNamesList = JDFGenNames.split(',')
            FileOrExit( os.path.join("jdfprint", "%s.py" % JDFGenName), 
                        "JDF generator (%s) " % JDFGenName )
            print "JDF Generator set to %s.\n" % JDFGenName
        elif opt in ["-s", "--sitesfile"]: 
            SitesFileName = arg.strip()
            FileOrExit( SitesFileName, "site description" )
        elif opt in ["-w", "--workload"]: 
            WorkloadDescriptionFileName = arg.strip() 
            FileOrExit( WorkloadDescriptionFileName, "workload description" )
        elif opt in ["--arrival"]:
            arrivalDistr = WLDocHandlers.getArrivalTimeDistribution(arg)
        else:
            print "Unknown parameter", opt
    
    #--- Load workload generators
    print "STATUS! Load workload generators."
    AWLGenLoader = WLLoader.GeneratorsLoader( ModulesPath = "apps", 
                                                  AppGenSig = "WLGenerator", 
                                                  AppGenFuncName = "generateWorkload",
                                                  ErrPrefix = "Workload Generator:"  )
    try:
        AWLGenLoader.loadGenerators()
    except WLLoader.GeneratorLoaderError, e:
        print e
        sys.exit(4)
    
    #--- Load workload unit generators
    print "STATUS! Load workload unit generators."
    AWLUnitGenLoader = WLLoader.GeneratorsLoader()
    try:
        AWLUnitGenLoader.loadGenerators()
    except WLLoader.GeneratorLoaderError, e:
        print e
        sys.exit(4)
        
    #--- Load JDF generators
    print "STATUS! Load JDF generators."
    AJDFGenLoader = WLLoader.GeneratorsLoader( ModulesPath = "jdfprint", 
                                               AppGenSig = "JDFGenerator", 
                                               AppGenFuncName = "generateJDF",
                                               ErrPrefix = "JDF Generator:"  )
    try:
        AJDFGenLoader.loadGenerators()
    except WLLoader.GeneratorLoaderError, e:
        print e
        sys.exit(5)
    
    #--- Load site file
    print "STATUS! Load site file."
    handlerXML = WLDocHandlers.readSiteFile(SitesFileName)
    DictionaryOfSites = handlerXML.getDictionaryOfSites()
    print "Got", len(DictionaryOfSites), "sites from '%s'.\n" % SitesFileName
    
    #--- Load workload description
    print "STATUS! Load workload description."
    KnownJobNamesList = AWLUnitGenLoader.getKnownGenerators()
    KnownWorkloadJobNamesList = AWLGenLoader.getKnownGenerators()
    KnownSiteNamesList = DictionaryOfSites.keys()
    print "Start getting a workload decription from", WorkloadDescriptionFileName
    ListOfDefs = WLDocHandlers.readWorkloadDescriptionFile( 
                            WorkloadDescriptionFileName, 
                            KnownJobNamesList, KnownWorkloadJobNamesList, 
                            KnownSiteNamesList)
    
    
    if ListOfDefs:
        print "Got", len(ListOfDefs), "workload units from '%s'.\n" % WorkloadDescriptionFileName
        #print ListOfDefs
        
#    for workloadDef in ListOfDefs:
#        print ": ", workloadDef['arrivaltimeinfo'][1]
        
    #--- Generate workload
    WLFileName = os.path.join( OutDir, "wl-to-submit.wl" ) 
    try:
        
        StartTime = time.time()
        outInfo = WLMain.generateWorkload( OutDir, WLFileName, ListOfDefs, SubmitDurationMS,
                             AWLUnitGenLoader, AWLGenLoader, AJDFGenLoader, JDFGenNamesList, 
                             DictionaryOfSites, arrivalDistr)
        EndTime = time.time()
        
        tstart = time.strftime('%H:%M:%S', time.gmtime(StartTime))
        tend = time.strftime('%H:%M:%S', time.gmtime(EndTime))
        print "\n------ TIMING SUMMARY ---------\n"
        print "Started %s / Ended %s / Duration %.1fs" % (tstart, tend, float(EndTime - StartTime) )
        
        print "\n\n------ LAST-MINUTE NOTES ---------"
        print "\nTo submit this workload, please run:\n"
        print "\t./wl-submit.py %s" % WLFileName
    except:
        raise
    
    print "\n\nThank you for using Grenchmark!\n"
    
    
    #lumpy.object_diagram()
    #lumpy.class_diagram()

if __name__ == "__main__":

    main(sys.argv[1:]) 
    
