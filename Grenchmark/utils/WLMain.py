#!/usr/bin/python

""" Grenchmark workload generator main functions """

__proggy = "Grenchmark/WLMain";
__rev = "0.21";
__proggy_stamp__ = "%s v%s" % (__proggy, __rev);
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'WLMain.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:19:35 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python" 
    
#---------------------------------------------------
# Log:
# 25/03/2008 C.S. 0.22 New functionalities:
#                        - generate workload in multiple formats
# 23/02/2008 C.S. 0.21 New functionalities;
#                        - generate Karajan workflows
# 15/10/2007 C.S. 0.2 New functionalities;
#                        - generate Condor DAGMan workflows
#                        - generate non-zero arrival times for composite units
# 18/08/2005 A.I. 0.13 Fixed bug:
#                      when generating unordered jobs with more 
#                      components than sites (e.g., 5/3), each of the 
#                      3 sites got also assigned 1 extra. Fixed with:
#                      ComponentNo = ComponentNo + 1 #-BF:0.13:1
# 12/08/2005 A.I. 0.1  Started this app
#---------------------------------------------------

import sys
import traceback
import os.path
from time import time, gmtime, strftime 

if "utils" not in sys.path:
    sys.path.append("utils")
import AIRandomUtils
import AIParseUtils
import WLDocHandlers
#--- v1.1: composite
import WLComposite
# _v1.1: composite

def getWLName( Prefix = "WL" ):
    return "%s-%s-%3.3d" % \
        ( Prefix, strftime('%Y-%m-%d_%H-%M', gmtime(time()) ), 
          AIRandomUtils.getRandomInt(0,999) )
        
def getWLUnitDir( WLDir, WLUnitID ):
    return os.path.join( WLDir, "jdfs", "jdf-%s" % WLUnitID )
    
def getWLUnitJDFFileName( WLUnitDir, WLUnitID ):
    return os.path.join( WLUnitDir, "wl-unit-%s.jdf" % WLUnitID )
    
def generateWorkload( OutDir, FullWLFileName, ListOfDefs, SubmitDurationMS,
                      AUnitGensLoader, AWLGensLoader, AJDFGeneratorsLoader, JDFGeneratorNames, 
                      DictionaryOfSites ):
    print "STATUS! Starting workload generation!"
    
    # the number of workflow engines for which we generate output files
    NEngines = len(JDFGeneratorNames)
    print "STATUS! Generating %d workload formats \n" % NEngines
    FileFormatsArray = [] 
    
    #DagCommandsFormatsMap = {'condor_dag_wrapper.sh':'dagman', 'karajan_wrapper_remote.sh':'karajan'}
     
    #--- reset random generator
    AIRandomUtils.initRandom()
    
    #--- init arrival time generator
    try:
        ArrivalTimeRandom = AIRandomUtils.AIRandom( time() )
    except Exception, e:
        print "ERROR! Cannot instantiate the ArrivalTime random generator.", e
    
    WLName = getWLName()
    GeneratorName = "%s on %s" % ( __proggy_stamp__, strftime('%Y-%m-%d_%H-%M', gmtime(time()) ) )
    
    #-- create workload's actual applications
    WLComponentList = []
    
    #--- Generate all units
    for WLUnit in ListOfDefs:
        
        WLUnitID = WLUnit['id']
        WLOutDir = getWLUnitDir( OutDir, WLUnitID )
        
        #--- Create output directory, if it does not exist
        if os.path.exists( WLOutDir ):
            if not os.path.isdir( WLOutDir ):
                print "Output for unit", WLUnitID, "("+WLOutDir+")", "exists, but is not a directory", "...skipping unit"
                continue
        else:
            try:
                os.makedirs( WLOutDir )
                # create directories for all the JDF generators:
                for name in JDFGeneratorNames:
                    ResManagerName = name.replace('-jdf', '')
                    DirName = "jdfs-%s" % ResManagerName
                    OutDirName = WLOutDir.replace('jdfs', DirName)
		    if not os.path.exists(OutDirName):
                	os.makedirs(OutDirName)
                
            except OSError, e:
                print "Cannot create output directory for unit", WLUnitID, "...skipping unit"
                print '\tOS returned:', e
                continue
                
        if 'RandomWorkload' in WLUnit['otherinfo'].keys():
            try:
                ##print "Getting random info from", WLUnit['otherinfo']['RandomWorkload']
                bGenerateRandom = AIParseUtils.readBoolean(WLUnit['otherinfo']['RandomWorkload'], 1)
            except Exception, e:
                print "Wrong value for RandomWorkload", "("+WLUnit['otherinfo']['RandomWorkload'].lower()+"). Expected true/false. Setting to default (true)"
                bGenerateRandom = 1
        else:
            print "No value for RandomWorkload", "Setting to default (true)."
            bGenerateRandom = 1
            
        WLUnit['arrivaltimefunc'] = ArrivalTimeRandom.randomVariable
         
        #--- get appropriate generator function
        #--- v1.1: composite
        # composite?
        if WLUnit['composite'] == 1:
            
            bGenerateRandom = 1 ### composite apps are always randomly generated
            
            #-- the composite types manager is simply an instance of composite types
            CompositeTypesManager = WLComposite.CompositeTypes()
                
            # 1. generate composite structures
            try:
                # give all params, let the generator select its own
                WLUnit['composite.structures'] = CompositeTypesManager.generateComposite( WLOutDir, WLUnitID, WLUnit, SubmitDurationMS, bGenerateRandom ) 
                if (WLUnit['composite.structures'] is not None) and (len(WLUnit['composite.structures'])>0):
                    WLUnit['status.composite.structures'] = 1
            except Exception, e:
                print "The generator for unit", WLUnit['id'], "/ AppType=", WLUnit['apptype'], "is incorrect...skipping unit"
                print "\tReason:", e
                print "TRACEBACK::COMPOSITE::GENERATOR>>>\n", traceback.print_exc()
                print "\n<<<\n"
                continue
                
            # 2. generate applications components: random seq/mpi jobs
            
            try:
                AppTypesWithWeights = \
                    AIParseUtils.readStringWithWeightsList( 
                        WLUnit['otherinfo']['AppsWithWeights'],
                        DefaultWeight = 1.0, ItemSeparator = ';' 
                        )
                ##print ">>>", "AppTypesWithWeights=", AppTypesWithWeights
                ##print ">>>", "AUnitGensLoader.GeneratorsDictionary=", AUnitGensLoader.GeneratorsDictionary.keys()
                # TODO: allow the generator to be a workload generator?
                #       currently: NO, as wl generators are for workloads, not for individual jobs
                for AppType in AppTypesWithWeights[AIParseUtils.VALUES]:
                    AppTypeName = AppType[0]
                    if AUnitGensLoader.hasGeneratorFunc(AppTypeName) == AUnitGensLoader.UNKNOWN_GENERATOR:
                        raise Exception, "Unknown application type %s [in WLMain::generateWorkload]" % AppType
            except Exception, e:
                print "ERROR! Wrong or undefined AppsWithWeights entry in other info... skipping unit"
                print "\tReason:", e
                continue
                
            #--- convert global parameters to 'otherinfo' data, for each composite structure
            try:
                DicSubUnits = []
                NCompositeStructures = len(WLUnit['composite.structures'])
                for CompositeStructureIndex in xrange(NCompositeStructures):
                    
                    CompositeStructure = WLUnit['composite.structures'][CompositeStructureIndex]
                    
                    #--- save to file
                    FullDirName = os.path.join(OutDir, "test")
                    try:
                        os.makedirs( FullDirName )
                    except OSError, e:
                        pass
                    
                    try:
                        FullFileName = os.path.join(FullDirName, "%s.dot" % CompositeStructure.getID())
                        CompositeStructure.saveToFile( FullFileName, FileFormat = 'dot' )
                    except:
                        print traceback.print_exc()
                        
                    try:
                        FullFileName = os.path.join(FullDirName, "%s.graph" % CompositeStructure.getID())
                        CompositeStructure.saveToFile( FullFileName,  )
                    except:
                        print traceback.print_exc()
                   
                    
                    #--- create subunits, one per composite structure
                    SubUnit = {}
                    SubUnit['.CompositeStructureIndex'] = CompositeStructureIndex
                    SubUnit['.CompositeStructureID'] = CompositeStructure.getID()
                    SubUnit['.NJobsToGenerate'] = CompositeStructure.getNNodes()
                    SubUnit['id'] = "%s" % CompositeStructure.getID()
                    SubUnit['IsWorkload'] = 0
                    SubUnit['composite'] = 0
                    SubUnit['multiplicity'] = 1 
                    
                    # NOTE: all workload units need to use this information to generate correctly
                    #       their JDF names...
                    #SubUnit['FirstJobIndex'] = JobIndex
                    
                    CurrentAppType = AIRandomUtils.getRandomWeightedListElement(
                                        AppTypesWithWeights,
                                        ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                                        )
                    SubUnit['apptype'] = CurrentAppType
                    #SubUnit['arrivaltimeinfo'] = ('Zero', []) # all jobs in the same composite application arrive at the same time, 0
                    SubUnit['arrivaltimeinfo'] = WLUnit['arrivaltimeinfo'] 
                    SubUnit['arrivaltimefunc'] = WLUnit['arrivaltimefunc']
                    
                    SubUnit['otherinfo'] = {}
                    for item in WLUnit['otherinfo']:
                        CurrentAppStamp = CurrentAppType + '.'
                        if item.find(CurrentAppStamp) == 0: # this other info item pertains the current application type
                            EntryInternalName = item[len(CurrentAppStamp):]
                            SubUnit['otherinfo'][EntryInternalName] = WLUnit['otherinfo'][item]
                        
                    # TODO: composite apps site info quick-hack fix !!!
                    #       also support the case where multi-component apps with no support provided
                    #       by the user in the generator module, e.g.: the smpi1-unit.py unit
                    #       has automatic generation of multi-component jobs (see the smpi1-unit.py::PreComponentsList variable 
                    #       in the generateWorkloadUnit function)
                    #
                    SubUnit['components'] = {}
                    ## quick-hack: add one component of size 1 for the case this info is needed
                    SubUnit['components'][0] = { 'location':'*', 'amount':1 }
                    
                    DicSubUnits.append(SubUnit)
                    
                   
                    
                    
                WLUnit['composite.subunits'] = DicSubUnits
                        
            except Exception, e:
                print "ERROR! ... skipping unit"
                print "\tReason:", e
                print traceback.print_exc()
                continue
                
        else:
                
            if bGenerateRandom == 1:
                
                if WLUnit['IsWorkload'] == 0: #-- if not a self-standing workload
                    #-- unpack the ambiguous definitions -- TBF means To Be Fixed
                    ComponentsAmountTBF = []
                    ###NOTE: do not replace ambiguous locations -- let them remain unspecified
                    #ComponentsLocationTBF = []
                    NAssignedJobs = 0
                    for ComponentID in WLUnit['components'].keys():
                        Component = WLUnit['components'][ComponentID]
                        if Component['amount'] == '?':
                            ComponentsAmountTBF.append( ComponentID )
                        else:
                            NAssignedJobs = NAssignedJobs + int(Component['amount'])
                    
                        if Component['location'] in DictionaryOfSites.keys():
                            Component['location'] = DictionaryOfSites[Component['location']]['location']
                        #elif Component['location'] == '*':
                        #    ComponentsLocationTBF.append( ComponentID )
                    
                    NRemainingJobs = WLUnit['totaljobs'] - NAssignedJobs
                    if NRemainingJobs > 0:
                        ComponentNo = 0
                        ##-- assign policy: load levelling
                        NToAssign = NRemainingJobs / len(ComponentsAmountTBF)
                        #-- extra jobs
                        NRemainingJobs = NRemainingJobs - NToAssign * len(ComponentsAmountTBF)
                        for ComponentID in ComponentsAmountTBF:
                            ToAssignHere = NToAssign
                            if ComponentNo < NRemainingJobs: # assign the extra jobs
                                ToAssignHere = ToAssignHere + 1
                            WLUnit['components'][ComponentID]['amount'] = ToAssignHere # assign
                            ComponentNo = ComponentNo + 1 #-BF:0.13:1
        # _v1.1: composite
        
        #--- Use the registered generator function to generate this unit's jobs
        try:
            # get a Units dic = {'info':dictionary; 'jobs':dictionary}
            print "STATUS! Generating unit", WLUnitID, "(type=", WLUnit['apptype'], ")" 
            #--- v1.1: composite
            # composite?
            if WLUnit['composite'] == 1:
                
                #-- generate jobs for subunits and add them to the unit set of jobs 
                for SubUnit in WLUnit['composite.subunits']:
                    #-- generate jobs, one by one -> this allows setting the right parameters for file dependencies support
                    SubUnit['unit'] = {}
                    SubUnit['unit']['info'] = {}
                    SubUnit['unit']['jobs'] = {}
                    NJobsToGenerate = SubUnit['.NJobsToGenerate']
                    for JobIndex in xrange(NJobsToGenerate):
                        CurrentWLUnitID = "%s-%d" % (SubUnit['id'], JobIndex)
                        #-- choose job generator
                        CurrentGeneratorFunc = AUnitGensLoader.getGeneratorFunc( SubUnit['apptype'] )
                        #-- generate jop
                        CurrentUnit = CurrentGeneratorFunc( WLOutDir, CurrentWLUnitID, SubUnit, SubmitDurationMS, bGenerateRandom )
                        
                        ##print ">>>", "ID:", CurrentWLUnitID, "app type:", SubUnit['apptype'], "(", SubUnit['generatedjobs'], "jobs)"
                        #-- add jobs
                        if SubUnit['generatedjobs'] == 1:
                            #-- copy info to unit jobs set
                            SubUnit['unit']['info'][JobIndex] = CurrentUnit['info'][0]
                            SubUnit['unit']['jobs'][JobIndex] = CurrentUnit['jobs'][0]
                            # TODO: allow composite jobs in composite jobs...
                            SubUnit['unit']['info'][JobIndex]['composition-type'] = 'unitary'
                        else:
                            print "ERROR! More than one job generated as a node of a composite job!!! ("  +str(SubUnit['generatedjobs']) + ')'
                            
                #-- add information about dependencies
                #   placed here to facilitate future support for dependencies between jobs in different sub-units
                for SubUnit in WLUnit['composite.subunits']:
                    SubUnit['dependsOn'] = {}
                    SubUnit['dependsOn']['.unit'] = [] # the unit doesn't depend on anything [future support for unit2unit dependency]
                    CompositeStructure = WLUnit['composite.structures'][SubUnit['.CompositeStructureIndex']]
                    NJobsToGenerate = SubUnit['.NJobsToGenerate']
                    for JobIndex in xrange(NJobsToGenerate):
                        JobID = SubUnit['unit']['info'][JobIndex]['id']
                        SubUnit['dependsOn'][JobID] = []
                        ListOfPredecessors = CompositeStructure.getNodePredecessors(JobIndex)
                        for PredecessorJobIndex in ListOfPredecessors:
                            PredecessorID = SubUnit['unit']['info'][PredecessorJobIndex]['id']
                            SubUnit['dependsOn'][JobID].append(PredecessorID)
                        SubUnit['unit']['info'][JobIndex]['dependsOn'] = SubUnit['dependsOn'][JobID]
                            
                #-- add to the main unit one job per composite application
                WLUnit['unit'] = {}
                WLUnit['unit']['info'] = {}
                WLUnit['unit']['jobs'] = {}
                OverallIndex = 0
                    
                LastArrivalTime = -1.0
                for SubUnit in WLUnit['composite.subunits']:
                    SubUnit['jobinfo'] = {}
                    SubUnit['jobinfo']['id'] = "%s-%d_%s" % (WLUnitID, SubUnit['.CompositeStructureIndex'], SubUnit['apptype'])
                    SubUnit['jobinfo']['name'] = "%s__composite" % SubUnit['jobinfo']['id']
                    SubUnit['jobinfo']['description'] = "Composite application of type %s, with %d internal jobs" % (SubUnit['apptype'], SubUnit['.NJobsToGenerate'])
                    
                    # create the name of the JDF file for the composite structure
                    #SubUnit['jobinfo']['jdf'] = os.path.join( WLOutDir, "wl-unit-%s.graph" % SubUnit['jobinfo']['id'])        
                    #SubUnit['jobinfo']['default_jdf'] = SubUnit['jobinfo']['jdf']
                    SubUnit['jobinfo']['default_jdf'] = os.path.join( WLOutDir, "wl-unit-%s.graph" % SubUnit['jobinfo']['id'])        
                    # the extenstion can be specified in the DAG input file, otherwise we just use the default name
                    SubUnit['jobinfo']['jdf'] = []
                    if 'WLFileExtensions' in WLUnit['otherinfo'].keys(): 
                        ExtensionsArray = WLUnit['otherinfo']['WLFileExtensions'].split(',')
                        if len(ExtensionsArray) != NEngines:
                            raise Exception("Number of WL File Extensions does not correspond with number of generators")
                    
                        for ii in range(0, len(ExtensionsArray)):
                                DagFile = "%s%s" % (CompositeStructure.getID(), ExtensionsArray[ii])    
                                #SubUnit['jobinfo']['jdf'].append(os.path.join(FullDirName, DagFile))
                                SubUnit['jobinfo']['jdf'].append(os.path.join(FullDirName, DagFile))
                                #print "### Using DAG file: " + SubUnit['jobinfo']['jdf'][ii] + "\n"
                                
                    else:
                        #NEngines = 1
                        SubUnit['jobinfo']['jdf'] = []
                        SubUnit['jobinfo']['jdf'].append(SubUnit['jobinfo']['default_jdf'])
                        print "STATUS! Using default DAG file"
                         
                    #if JDFGeneratorName == 'condor-jdf':
                     #   SubUnit['jobinfo']['jdf'] = FullCondorDagFile
                     #   SubUnit['jobinfo']['default_jdf'] = FullCondorDagFile + '_default'
                       
		            # select the submit command; this can be specified in the DAG input file
                    # otherwise we take the default wl-exec.py
                    SubUnit['jobinfo']['submitCommand'] = []
                    for ii in range (0, NEngines):
                        DagSubmitCmd = 'wl-exec.py' 
                        DagArguments = ''
                        submitterString = 'Submitter%d' % ii
                        if submitterString in WLUnit['otherinfo'].keys():
                            CmdArray = WLUnit['otherinfo'][submitterString].split(' ')
                            DagSubmitCmd = CmdArray[0]
                            print "STATUS! Using submitter: " + DagSubmitCmd + "\n"
                            if len(CmdArray) > 2:
                                for jj in range(2, len(CmdArray)):
                                    DagArguments = DagArguments + CmdArray[jj] + " "
                            completeCmd = '%s %s %s' % (DagSubmitCmd, SubUnit['jobinfo']['jdf'][ii], DagArguments)
                            SubUnit['jobinfo']['submitCommand'].append(completeCmd)
                            print "STATUS! Using composite submit command: " + SubUnit['jobinfo']['submitCommand'][ii]
                        else:
                            print "STATUS! Using default submitter wl-exec.py"                     
                            
                    
                    # TODO: use the arrivaltimeinfo data to generate a correct runtime info for each SubUnit
                    # Done - but made the first subunit start at t = 0
                    #SubUnit['jobinfo']['runTime'] = "%.3f" % 0.0
                    try:
                        Name = SubUnit['arrivaltimeinfo'][0]
                        ParamsList = SubUnit['arrivaltimeinfo'][1]
                        #make the first job start at t = 0:
                        if LastArrivalTime < 0:
                            RunTime = 0.0
                        else:
                            RunTime = LastArrivalTime + SubUnit['arrivaltimefunc']( Name, ParamsList )
                        LastArrivalTime = RunTime
                        SubUnit['jobinfo']['runTime'] = "%.3f" % RunTime
                    except AIRandomUtils.AIRandomError, e:
                        print "AIRandomUtils.AIRandomError", e
                        SubUnit['jobinfo']['runTime'] = None
                    except Exception, e:
                        print "ERROR!", e, "Name", Name, "Params", ParamsList
                        SubUnit['jobinfo']['runTime'] = None
                        
                    if (SubUnit['jobinfo']['runTime'] == None) or (float(SubUnit['jobinfo']['runTime']) < 0):
                        print "Wrong arrival time of", SubUnit['runTime'], "generated by", Name, ParamsList
                        print "Resetting to default 0.0"
                        InfoDic['runTime'] = "%.3f" % 0.0
		    		    
                    SubUnit['jobinfo']['composition-type'] = 'composite'
                    WLUnit['unit']['info'][OverallIndex] = SubUnit['jobinfo']
                    WLUnit['unit']['jobs'][OverallIndex] = SubUnit['.CompositeStructureIndex'] # no list, just a pointer!!!
                    OverallIndex = OverallIndex + 1
                    
                    try:
                        CompositeStructure = WLUnit['composite.structures'][SubUnit['.CompositeStructureIndex']]
                        #FullFileName = os.path.join(FullDirName, "%s.dag" % CompositeStructure.getID())
                        #CompositeStructure.saveToFile( FullFileName, FileFormat = 'dagman', WLUnit['composite.subunits'] )
                        #if DagSubmitCmd != 'wl-exec.py':
                        FileFormat = "dagman"  
                        if 'CompositeFileFormats' in WLUnit['otherinfo'].keys():
                            FileFormatsArray = WLUnit['otherinfo']['CompositeFileFormats'].split(',')
                            for ii in range(0, len(FileFormatsArray)): 
                                if (FileFormatsArray[ii] != 'default'): 
                                    SubUnit['JDFGeneratorName'] = JDFGeneratorNames[ii]
                                    print "STATUS! Using DAG file format: " + FileFormatsArray[ii] + "\n"
                                    SubUnit['CurrentJDFGenerator'] = JDFGeneratorNames[ii]
                                    CompositeStructure.saveToFile( SubUnit['jobinfo']['jdf'][ii], FileFormatsArray[ii], SubUnit)
                        else:
                            print "WARNING! DAG file format not specified in the .xin file, using default - Condor DAGMan"
                        #CompositeStructure.saveToFile( SubUnit['jobinfo']['jdf'], FileFormat, SubUnit )
                    except:
                        print traceback.print_exc()
                        
                WLUnit['generatedjobs'] = OverallIndex
            else:
                if WLUnit['IsWorkload'] == 1:
                    CurrentGeneratorFunc = AWLGensLoader.getGeneratorFunc( WLUnit['apptype'] )
                else:
                    CurrentGeneratorFunc = AUnitGensLoader.getGeneratorFunc( WLUnit['apptype'] )
                if CurrentGeneratorFunc is None:
                    print "Cannot find a generator for AppType", "'"+WLUnit['apptype']+"'", "for unit", WLUnitID, "...skipping unit"
                    continue
                WLUnit['unit'] = CurrentGeneratorFunc( WLOutDir, WLUnitID, WLUnit, SubmitDurationMS, bGenerateRandom )
                
                
            # _v1.1: composite
            WLUnit['status'] = 1 # define a status field
            print "STATUS! ...done generating unit", WLUnitID, "(type=", WLUnit['apptype'], ")"
        except Exception, e:
            print "The generator for unit", WLUnit['id'], "/ AppType=", WLUnit['apptype'], "is incorrect...skipping unit"
            print "\tReason:", e
            print "TRACEBACK::GENERATOR>>>\n", traceback.print_exc()
            print "\n<<<\n"
            #print "\tGeneratorFunc", GeneratorFunc
            pass
            
    #--- Print all units
    try:
        print "STATUS! Writing workload JDFs"
        #--- v1.1_: JDF per unit
        #try:
        #    CurrentJDFGeneratorName = WLUnit['JDFGeneratorName']
        #except:
        #    CurrentJDFGeneratorName = JDFGeneratorName
        
        # v. 0.22 hack: get the JDF generator names only from the command line
        # we'll use the same generator for all the WLUnits
        JDFGeneratorFuncs = []
        for name in JDFGeneratorNames:
            JDFGeneratorFuncs.append(AJDFGeneratorsLoader.getGeneratorFunc( name ))
            
        if (len(JDFGeneratorFuncs) < NEngines):
            #print "Cannot find JDF generator", "'"+JDFGeneratorName+"'", "...quitting"
            print "Could only find %d generators - and %d are needed\n" % (len(JDFGeneratorFuncs), NEngines) 
            raise NameError, JDFGeneratorName
        # _v1.1: JDF per unit
            
        NJobs = 0
        NComponents, MinComponents, MaxComponents = 0, None, None
        TotalJobNCPUs, MinJobNCPUs, MaxJobNCPUs = 0, None, None
        TotalComponentNCPUs, MinComponentNCPUs, MaxComponentNCPUs = 0, None, None
        
        WLJobsInfoList = []
        for WLUnit in ListOfDefs:
            if 'status' in WLUnit.keys():
                #--- Use the registered generator function to generate a JDF for this
                ListOfComponents = []
                
                #--- v1.1: composite
                try:
                    
                    #--- print app nodes / parts
                    index = 0
                    if WLUnit['generatedjobs'] >= 1:
                        ##print ">>>", "Generated jobs", WLUnit['generatedjobs']
                        while index < WLUnit['generatedjobs']:
                            JobInfo = WLUnit['unit']['info'][index]
                            
                            #--- actually print the job
                            #    for unitary jobs, use the unit's JDF printer
                            #    for composite jobs, use the job's subunit JDF printer if it exists, or the unit's JDF printer otherwise
                            if 'composition-type' not in JobInfo: JobInfo['composition-type'] = 'unitary'
                            
                            if JobInfo['composition-type'] == 'composite':
                                #-- get sub unit data
                                SubUnitIndex = WLUnit['unit']['jobs'][index]
                                SubUnit = WLUnit['composite.subunits'][SubUnitIndex]
                                #--- print sub-jobs
                                Composite_JobsInfoList = [] 
                                NJobsToGenerate = SubUnit['.NJobsToGenerate']
                                
                                for JobIndex in xrange(NJobsToGenerate):
                                    #-- add sub-job to set of jobs for the subunit JDF
                                    Composite_JobsInfoList.append(SubUnit['unit']['info'][JobIndex])
                                    
                                   
                                    #-- get list of components for this unitary job
                                    JobComponentsList = SubUnit['unit']['jobs'][JobIndex]
                                    
                                    #--- statistics for this job
                                    CurrentNComponents = len(JobComponentsList)
                                    NComponents = NComponents + CurrentNComponents
                                    if (MinComponents is None) or (MinComponents > CurrentNComponents): MinComponents = CurrentNComponents
                                    if (MaxComponents is None) or (MaxComponents < CurrentNComponents): MaxComponents = CurrentNComponents
                                    CurrentTotalJobNCPUs = 0
                                    for JobComponent in JobComponentsList: 
                                        if 'count' in JobComponent:
                                            CurrentNCPUs = JobComponent['count']
                                            # per job stats
                                            CurrentTotalJobNCPUs = CurrentTotalJobNCPUs + CurrentNCPUs
                                            # per component stats
                                            TotalComponentNCPUs = TotalComponentNCPUs + CurrentNCPUs
                                            if (MinComponentNCPUs is None) or (MinComponentNCPUs > CurrentNCPUs): MinComponentNCPUs = CurrentNCPUs
                                            if (MaxComponentNCPUs is None) or (MaxComponentNCPUs < CurrentNCPUs): MaxComponentNCPUs = CurrentNCPUs
                                    # per job stats
                                    TotalJobNCPUs = TotalJobNCPUs + CurrentTotalJobNCPUs
                                    if (MinJobNCPUs is None) or (MinJobNCPUs > CurrentTotalJobNCPUs): MinJobNCPUs = CurrentTotalJobNCPUs
                                    if (MaxJobNCPUs is None) or (MaxJobNCPUs < CurrentTotalJobNCPUs): MaxJobNCPUs = CurrentTotalJobNCPUs
                                    
                                     # v. 0.22 - generate multiple types of JDFs
                                    ii = 0; 
                                    for GenName in JDFGeneratorNames:
#                                        try:
#                                            CurrentJDFGeneratorName = SubUnit['JDFGeneratorName']
#                                            
#                                            CurrentJDFGeneratorFunc = AJDFGeneratorsLoader.getGeneratorFunc( CurrentJDFGeneratorName )
#                                            if CurrentJDFGeneratorFunc is None:
#                                                print "Cannot find JDF generator", "'"+CurrentJDFGeneratorName+"'", "...using existing JDF generator"
#                                                raise NameError, CurrentJDFGeneratorName
#                                        except:
#                                            CurrentJDFGeneratorFunc = JDFGeneratorFunc
                                    
                                        
                                        #-- select the output file for this job
                                        ResManagerName = GenName.replace('-jdf', '')
                                        DirName = "jdfs-%s" % ResManagerName
                                        SubJobJDFFileName = SubUnit['unit']['info'][JobIndex]['jdf'].replace('jdfs', DirName)
                                        print "STATUS! Saving subjob", JobIndex, "of SubUnit", SubUnit['id'], "("+str(SubUnitIndex)+")", "to", SubJobJDFFileName
                                    
                                        #-- print job to its JDF file
                                        
                                        if JDFGeneratorFuncs[ii] is None:
                                            print "Cannot find JDF generator", "'"+JDFGeneratorNames[ii]+"'"
                                            raise NameError, CurrentJDFGeneratorName
                                        JDFGeneratorFuncs[ii]( SubJobJDFFileName, JobComponentsList )
                                        ii = ii + 1
                                    #-- print job to its JDF file
                                    # CurrentJDFGeneratorFunc( SubJobJDFFileName, JobComponentsList )
                                    
                                #--- print composite job - to multiple files if necessary
                                for ii in range (0, NEngines):
                                    #Composite_JDFFileName = JobInfo['default_jdf']
                                    if (FileFormatsArray[ii] == 'default'):
                                        Composite_JDFFileName = JobInfo['jdf'][ii]
                                        print "STATUS! %d Writing default composite file to: %s " % (ii, Composite_JDFFileName)
                                        Composite_Name = JobInfo['id'] 
                                        Composite_Type = 'composite:' + WLUnit['CompositionType'] 
                                        WLDocHandlers.writeWorkloadSubmitFile( Composite_JDFFileName, Composite_Name, Composite_JobsInfoList, JDFGeneratorNames[ii], Composite_Type, GeneratorName ) 
                                
                            else:
                                #-- get list of components for this unitary job
                                JobComponentsList = WLUnit['unit']['jobs'][index]
                                #--- statistics for this unit
                                CurrentNComponents = len(JobComponentsList)
                                NComponents = NComponents + CurrentNComponents
                                if (MinComponents is None) or (MinComponents > CurrentNComponents): MinComponents = CurrentNComponents
                                if (MaxComponents is None) or (MaxComponents < CurrentNComponents): MaxComponents = CurrentNComponents
                                CurrentTotalJobNCPUs = 0
                                for JobComponent in JobComponentsList: 
                                    if 'count' in JobComponent:
                                        CurrentNCPUs = JobComponent['count']
                                        # per job stats
                                        CurrentTotalJobNCPUs = CurrentTotalJobNCPUs + CurrentNCPUs
                                        # per component stats
                                        TotalComponentNCPUs = TotalComponentNCPUs + CurrentNCPUs
                                        if (MinComponentNCPUs is None) or (MinComponentNCPUs > CurrentNCPUs): MinComponentNCPUs = CurrentNCPUs
                                        if (MaxComponentNCPUs is None) or (MaxComponentNCPUs < CurrentNCPUs): MaxComponentNCPUs = CurrentNCPUs
                                # per job stats
                                TotalJobNCPUs = TotalJobNCPUs + CurrentTotalJobNCPUs
                                if (MinJobNCPUs is None) or (MinJobNCPUs > CurrentTotalJobNCPUs): MinJobNCPUs = CurrentTotalJobNCPUs
                                if (MaxJobNCPUs is None) or (MaxJobNCPUs < CurrentTotalJobNCPUs): MaxJobNCPUs = CurrentTotalJobNCPUs
                                #-- print job to its JDF file
                                ii = 0; 
                                for GenName in JDFGeneratorNames:
                                    #try:
                                        #CurrentJDFGeneratorName = SubUnit['JDFGeneratorName']
                                        #CurrentJDFGeneratorFunc = AJDFGeneratorsLoader.getGeneratorFunc( CurrentJDFGeneratorName )
                                        #if CurrentJDFGeneratorFunc is None:
                                        #    print "Cannot find JDF generator", "'"+CurrentJDFGeneratorName+"'", "...using existing JDF generator"
                                        #    raise NameError, CurrentJDFGeneratorName
                                    #except:
                                    #    CurrentJDFGeneratorFunc = JDFGeneratorFunc
                                
                                    
                                    #-- select the output file for this job
                                    ResManagerName = GenName.replace('-jdf', '')
                                    DirName = "jdfs-%s" % ResManagerName
                                    #SubJobJDFFileName = SubUnit['unit']['info'][JobIndex]['jdf'].replace('jdfs', DirName)
                                    #print "STATUS! Saving subjob", JobIndex, "of SubUnit", SubUnit['id'], "("+str(SubUnitIndex)+")", "to", SubJobJDFFileName
                                
                                    #-- print job to its JDF file
                                    
                                    if JDFGeneratorFuncs[ii] is None:
                                        print "Cannot find JDF generator", "'"+JDFGeneratorNames[ii]+"'"
                                        raise NameError, CurrentJDFGeneratorName
                                    JDFGeneratorFuncs[ii]( JobInfo['jdf'], JobComponentsList )
                                    ii = ii + 1                                
                                #JDFGeneratorFunc( JobInfo['jdf'], JobComponentsList )
                            
                            WLJobsInfoList.append( JobInfo )
                            index = index + 1
                        
                except Exception, e:
                    #print "The JDF generator", JDFGeneratorName, "is incorrect...skipping whole unit"
                    print "The JDF generator is incorrect...skipping whole unit"
                    print "\tReason:", e
                    print "TRACEBACK::JDF>>>\n", traceback.print_exc()
                    print "\n<<<\n"
                # _v1.1: composite
                    
        NJobs = len(WLJobsInfoList)
                    
        for ii in range (0, NEngines):
            FinalWLFileName = "%s%02d" % (FullWLFileName, ii)
            print "STATUS! Writing workload to %s." % ("'"+FinalWLFileName+"'")
            WLDocHandlers.writeWorkloadSubmitFile( FinalWLFileName, WLName, WLJobsInfoList, ii, 'root', GeneratorName ) 
            print "\nSUCCESS! Workload generation complete for engine no. %d!\n" % ii
        
        #--- print statistics
        if NJobs > 0:
            FComponentsPerJobs = float(1.0 * NComponents) / NJobs
        else:
            FComponentsPerJobs = 0.0
        if MinComponents is None: MinComponents = -1
        if MaxComponents is None: MaxComponents = -1
        
        if MinJobNCPUs is None: MinJobNCPUs = -1 
        if MaxJobNCPUs is None: MaxJobNCPUs = -1
        if NJobs > 0:
            FNCPUsPerJob = float(1.0 * TotalJobNCPUs) / NJobs
        else:
            FNCPUsPerJob = 0.0
            
        if MinComponentNCPUs is None: MinComponentNCPUs = -1 
        if MaxComponentNCPUs is None: MaxComponentNCPUs = -1
        if NComponents > 0:
            FNCPUsPerComponent = float(1.0 * TotalComponentNCPUs) / NComponents
        else:
            FNCPUsPerComponent = 0.0
            
        print "\n------ WORKLOAD GENERATION SUMMARY ---------\n"
        print "Jobs: %d / Components: %d components" % ( NJobs, NComponents )
        print "Components/job Avg:%.3f | Min:%d | Max:%d" % ( FComponentsPerJobs, MinComponents, MaxComponents )
        print "CPUs/job       Avg:%.3f | Min:%d | Max:%d" % ( FNCPUsPerJob, MinJobNCPUs, MaxJobNCPUs )
        print "CPUs/component Avg:%.3f | Min:%d | Max:%d" % ( FNCPUsPerComponent, MinComponentNCPUs, MaxComponentNCPUs )
        print "--------------------------------------------"
        print "Submission time: %.1fs / Jobs submitted per second: %.3f" % \
            (float(SubmitDurationMS/1000.0), float(1000.0 * NJobs / SubmitDurationMS))
            
       
        
    except Exception, e:
        print "\nFAILED! An error occured while writing the workload file\n\t--", e
        print "TRACEBACK>>>\n", traceback.print_exc()
        print "\n<<<\n"
        raise e
    
##    for WLUnit in ListOfDefs:
##        print "\n>>>\n", 
##        if 'status' in WLUnit.keys():
##            print WLUnit['apps']
##        else:
##            print "Could not generate unit", WLUnit['id'], "AppType=", WLUnit['apptype']
##            


