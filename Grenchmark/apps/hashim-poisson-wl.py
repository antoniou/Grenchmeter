WLGenerator="""
    Name=poisson
    Info=Hashim's test application
    Author=Hashim
    Contact=email:H.H.Mohamed@ewi.tudelft.nl
    """
    
import os.path

import sys
if "utils" not in sys.path:
    sys.path.append("utils")
import AIRandomUtils
import AIParseUtils

   
HSH_LastRunTime = 0
    
def generateJobInfo( UnitDir, UnitID, JobIndex, WLUnit, SubmitDurationMS, Submitter ):
    global HSH_LastRunTime
    """ 
    Out:
        A dictionary having at least the keys:
        'name', 'description', 'jdf', 'submitCommand', 'runTime'
        
    See also:
        utils/WLDocHandlers.WLSubmitJobKeys
    """
    InfoDic = {}
    JobType = WLUnit['apptype']
    InfoDic['id'] = "%s_%d_%s" % ( UnitID, JobIndex, JobType )
    InfoDic['name'] = "%s_%d_%s__sser" % ( UnitID, JobIndex, JobType )
    InfoDic['description'] = \
        "Workload unit %s, job %d, comprising only applications of type %s." % \
                ( UnitID, JobIndex, JobType )
    InfoDic['jdf'] = os.path.join( UnitDir, "wl-unit-%s-%d.jdf" % (UnitID, JobIndex) )
    
    InfoDic['submitCommand'] = '%s -e -o -g -f %s' % ( Submitter, InfoDic['jdf'] )
    
    try:
        Name = WLUnit['arrivaltimeinfo'][0]
        ParamsList = WLUnit['arrivaltimeinfo'][1]
        RunTime = HSH_LastRunTime + WLUnit['arrivaltimefunc']( Name, ParamsList )
        HSH_LastRunTime = RunTime
        InfoDic['runTime'] = "%.3f" % RunTime
    except AIRandomUtils.AIRandomError, e:
        print "AIRandomUtils.AIRandomError", e
        InfoDic['runTime'] = None
    except Exception, e:
        print "ERROR!", e, "Name", Name, "Params", ParamsList
        InfoDic['runTime'] = None
        
    if (InfoDic['runTime'] == None) or \
       (float(InfoDic['runTime']) < 0) or (float(InfoDic['runTime']) > SubmitDurationMS):
        # all workload units are started within at most SubmitDurationMS miliseconds
        print "Wrong arrival time of", InfoDic['runTime'], "generated by", Name, ParamsList
        print "Resetting to default U(0,%d)" % SubmitDurationMS
        InfoDic['runTime'] = str(AIRandomUtils.getRandomInt(0, SubmitDurationMS))
        
    return InfoDic

def generateJobComponents( UnitDir, UnitID, JobIndex, WLUnit, \
    NumComponents, ComponentSize, Application):
    
    # minutes: 3, 15, 30, 700
    RunTimeInMinutesList = [ '3', '15', '30', '700' ]
    
    ComponentsList = []
    
    #--- generate wall time once for all components of this job
    MaxWallTime = AIRandomUtils.getRandomListElement( RunTimeInMinutesList )
    
    if UnitDir[0] != '/':
        if sys.platform.find("linux") >= 0:
            UnitDir = os.path.join( os.environ['PWD'], UnitDir )
        else:
            UnitDir = os.path.join( os.getcwd(), UnitDir )
            
    #-- hashim's workload definition
    ComponentDirName = "%d-%d-%d" % ( JobIndex, NumComponents, ComponentSize )
    FullComponentDirName = os.path.join( UnitDir, "%s/" % UnitID, ComponentDirName ) 
    #--- Create output directory, if it does not exist
    if os.path.exists( FullComponentDirName ):
        if not os.path.isdir( FullComponentDirName ):
            print "Output for job", JobIndex, "("+FullComponentDirName+")", "exists, but is not a directory", "...skipping job"
            return -1
    else:
        try:
            os.makedirs( FullComponentDirName )
        except OSError, e:
            print "Cannot create output directory for job", JobIndex, "...skipping job"
            print '\tOS returned:', e
            return -1
    
    for ComponentID in xrange(NumComponents):
        #--- reset component data
        ComponentData = {}
        
        #--- generate component data
        ComponentData['id'] = "%s-%d-%2.2d" % ( UnitID, JobIndex, ComponentID )
        ComponentData['location'] = '*'
        ComponentData['jobtype'] = 'mpi'
        ComponentData['count'] = int(ComponentSize)
        ComponentData['directory'] = FullComponentDirName
        ComponentData['executable'] = \
            os.path.join('/home2/hashim/share/experiments/koala-1/bin/',Application)
        ComponentData['maxWallTime'] = MaxWallTime
        ComponentData['stdout'] = os.path.join( FullComponentDirName, "pois-2.out" )
        ComponentData['stagein'] = ['/var/scratch/hashim/pdcaDevel2.0.1.tar']
        
        ComponentData['name']   = "%s_hashim" % ComponentData['id']
        ComponentData['description'] = \
                    "Hashim Workload Job, Count=%d, maxWallTime=%d" % \
                    (ComponentData['count'], int(MaxWallTime) )
        
        ComponentData['arguments'] = [ "%d" % (ComponentSize*2), "%d" % (NumComponents/2) ]
        ComponentData['env'] = [ 
            ("GLOBUS_DUROC_SUBJOB_INDEX", "%d" % ComponentID),
            ("LD_LIBRARY_PATH", "/usr/local/globus/globus-3.2/lib/") 
            ]
        ComponentData['label'] = "subjob %d" % ComponentID
        
        #--- add component to the job
        ComponentsList.append( ComponentData )
        
    return ComponentsList

def generateWorkload( UnitDir, UnitID, WLUnit, SubmitDurationMS, bGenerateRandom = 1 ):
    global HSH_LastRunTime
    #print WLUnit['otherinfo']
    #{'RandomWorkload': 'true', 'NComponents': '1-8', 'NJobs': '50', 'ComponentSize':'4-8'}
    
    if bGenerateRandom > 0:
        print "Random workload"
    else:
        print "Full workload"
    
    if 'otherinfo' in WLUnit.keys():
        try:
            NComponents = WLUnit['otherinfo']['NComponents']
        except KeyError:
            raise Exception, "Hashim's generator: No NComponents info specified in the OtherInfo field."
        
        try:
            NumComponentsList = AIParseUtils.readIntRange( NComponents )
            if len(NumComponentsList) == 0:
                NumComponentsList = AIParseUtils.readIntList( NComponents )
                if len(NumComponentsList) == 0:
                    raise Exception, ""
        except Exception, e:
            raise Exception, "Hashim's generator: Incorrect NComponents format!\n\tExpected NComponents=X-Y, with X,Y integers and X<Y or\n\tNComponents=V1;...;Vn, Vi integer. Got %s." % NComponents
        #print ">>>DEBUG>>> NumComponentsList", NumComponentsList
        
        try:
            NJobs = WLUnit['otherinfo']['NJobs']
        except KeyError:
            NJobs = "0"
            if bGenerateRandom > 0: #-- NJobs required if random, optional otherwise
                raise Exception, "Hashim's generator: No NJobs info specified in the OtherInfo field."
        
        try:
            NJobs = int(NJobs.strip())
        except:
            raise Exception, "Hashim's generator: Incorrect NJobs format! Expected NJobs=X, with X integer."
        #print ">>>DEBUG>>> NJobs", NJobs
    
        try:
            ComponentSize = WLUnit['otherinfo']['ComponentSize']
        except KeyError:
            raise Exception, "Hashim's generator: No ComponentSize info specified in the OtherInfo field."
        
        try:
            ComponentSizeList = AIParseUtils.readIntRange( ComponentSize )
            if len(ComponentSizeList) == 0:
                ComponentSizeList = AIParseUtils.readIntList( ComponentSize )
                if len(ComponentSizeList) == 0:
                    raise Exception, ""
        except:
            raise Exception, "Hashim's generator: Incorrect ComponentSize format!\n\tExpected ComponentSize=X-Y, with X,Y integers and X<Y or\n\tComponentSize=V1;...;Vn, Vi integer. Got %s." % ComponentSize
        #print ">>>DEBUG>>> ComponentSizeList", ComponentSizeList
        
        try:
            Submitter = WLUnit['otherinfo']['Submitter']
        except KeyError:
            Submitter = 'drunner'
            print "WARNING! Hashim's generator: No Submitter info specified in the OtherInfo field.\n\tSetting to default", Submitter
            
        try:
            Application = WLUnit['otherinfo']['Application']
        except KeyError:
            Application = 'Poisson-g2-gm'
            print "WARNING! Hashim's generator: No Application info specified in the OtherInfo field.\n\tSetting to default", Application
        
    else:
        raise Exception, "Hashim's generator: No OtherInfo data! Expected at least ComponentSize,NJobs,NComponents fields."
    
    UnitsDic = {}
    UnitsDic['info'] = {}
    UnitsDic['jobs'] = {}
    
    #-- init start time
    try:
        StartAt = AIParseUtils.readInt(WLUnit['otherinfo']['StartAt'], DefaultValue = 0)
        StartAt = StartAt * 1000 # the time is given is seconds
    except KeyError:
        StartAt = 0
    HSH_LastRunTime = StartAt
    
    WLUnitMultiplicity = int(WLUnit['multiplicity'])
    if bGenerateRandom > 0:
        #--- generate random
        JobIndex = 0
        if WLUnitMultiplicity > 1:
            NJobs = NJobs * WLUnitMultiplicity
        while JobIndex < NJobs:
            
            ComponentSize = AIRandomUtils.getRandomListElement( ComponentSizeList )
            NumComponents = AIRandomUtils.getRandomListElement( NumComponentsList )
            
            CurrentUnitID = "%s-%d" % (UnitID, JobIndex % WLUnitMultiplicity)
            UnitsDic['info'][JobIndex] = \
                        generateJobInfo( UnitDir, CurrentUnitID, JobIndex, \
                                         WLUnit, SubmitDurationMS, Submitter )
            UnitsDic['jobs'][JobIndex] = \
                        generateJobComponents( UnitDir, CurrentUnitID, JobIndex, WLUnit, \
                                               NumComponents, ComponentSize, Application)
            JobIndex = JobIndex + 1
        WLUnit['generatedjobs'] = JobIndex
        
    else:
        print "Complete workload"
        #--- generate all
        JobIndex = 0
        RepetitionIndex = 0
        while RepetitionIndex < WLUnitMultiplicity:
            for ComponentSize in ComponentSizeList:
                for NumComponents in NumComponentsList:
                    CurrentUnitID = "%s-%d" % (UnitID, JobIndex % WLUnitMultiplicity)
                    UnitsDic['info'][JobIndex] = \
                        generateJobInfo( UnitDir, CurrentUnitID, JobIndex, \
                                         WLUnit, SubmitDurationMS, Submitter )
                    UnitsDic['jobs'][JobIndex] = \
                        generateJobComponents( UnitDir, CurrentUnitID, JobIndex, WLUnit, \
                                               NumComponents, ComponentSize, Application)
                    JobIndex = JobIndex + 1
            RepetitionIndex = RepetitionIndex + 1
            
            if JobIndex > NJobs and NJobs > 0:
                print "Generated %d jobs and stopped because of the NJobs limit."
                break
            
        WLUnit['generatedjobs'] = JobIndex
        
    #raise Exception, "Hashim's generator: Not implemented yet"
    return UnitsDic
