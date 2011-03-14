#---------------------------------------------------
# Log:
# 03/11/2005 A.I. 0.1  Added complete parametrization for the random generator
# 11/08/2005 A.I. 0.1  Started this app
#---------------------------------------------------

Generator="""
    Name=smpi1
    Info=Workload based on the smpi1 synthetic MPI application
    Author=C. Dumitrescu
    Contact=email:cldumitr@cs.uchicago.edu
    """
import os.path

import sys
if "utils" not in sys.path:
    sys.path.append("utils")
import AIRandomUtils
import AIParseUtils
import traceback
import EFFBotMultiReplace
    
SMPI1_LastRunTime = 0

def replaceDic( OriginalString, ReplaceDic ):
    try:
        import string
        t = string.Template(OriginalString)
        return str(t.substitute(ReplaceDic))
    except AttributeError, e:
        print "SMPI1 generator: Submitter: Your Python version does not include string.Template (ver<2.4)",
        # TODO: create a ${} substitution function, to replace Python 2.4's !!!!
        ReplaceDic2 = {}
        for Key in ReplaceDic.keys():
            ReplaceDic2['${'+Key+'}'] = ReplaceDic[Key]
        replacer = EFFBotMultiReplace.MultiReplace(ReplaceDic2)
        return str(replacer.replace(OriginalString))
    except KeyError, e:
        print "SMPI1 generator: ", e, "not found...replacing with default"
        raise KeyError, e
        
    raise Exception, "SMPI1 generator: cannot substitute " + str(ReplaceDic) + " in '" + OriginalString + "'"


class SMPI1Component:
    
    SMPI1_Exe = os.path.join( "/tmp", "smpi1t" )
        
    SMPI1_ParKSizes = [ "0", "32", "128", "512", "1024" ]
    SMPI1_ParKSuperSizes = [ "0", "16", "32", "64", "128", "256" ]
    SMPI1_ParSupersteps = [ "1", "2", "5", "10", "20", "50", "100" ]
    SMPI1_ParMemoryKItems = [ "10", "25", "50", "100", "250", "500", "1000", "5000" ]
    SMPI1_ParMemoryElementsPerItem = [ "3", "4", "10", "100", "500", "1000" ]
    SMPI1_ParXChangeElementsPerStep = [ "100", "500", "1000", "10000", "50000" ]
    SMPI1_ParComputationPerMemoryItem = [ "2", "10", "100", "1000" ]
        
    SMPI1_RunTimeInMinutes = [ "2", "5", "10", "15" ]
    
    def __init__( self, BaseDir, ComponentIndex, ComponentData, HaveInput = 0, HaveOutput = 0 ):
        """ 
        Init a SMPI1 Component 
        
        In:
            UnitDir       -- physical location of this workload unit
            ComponentIndex -- used to identify this component within the workload unit
            ComponentData  -- a component data dictionary, with the following fields
                              already set:
                              id -- component's ID (if unique, the better)
                              count -- the number of apps to be executed in this component
        """
        self.BaseDir = BaseDir
        self.ComponentIndex = ComponentIndex
        self.ComponentData = ComponentData
        self.HaveInput = HaveInput
        self.HaveOutput = HaveOutput
        
    def generateArgsList(self, I1, I2, O1, O2, O3, N, M, S, X, C ):
        """
        Generates the arguments list for an application of type SMPI1
        
        In: (specific parameters of SMPI1 applications)
        """
        ArgsList = [ 
            "-n", str(N), 
            "-m", str(M), 
            "-s", str(S), 
            "-c", str(C),
            "-x", str(X)
            ]
        if I1 > 0 or I2 > 0:
            if I1 > 0:
                ArgsList.append("-i1")
                ArgsList.append(str(I1)) 
            if I2 > 0:
                ArgsList.append("-i2")
                ArgsList.append(str(I2))
        else:    
            ArgsList.append("--noinput")
            
        if O1 > 0 or O2 > 0 or O3 > 0:
            if O1 > 0:
                ArgsList.append("-o1")
                ArgsList.append(str(O1)) 
            if O2 > 0:
                ArgsList.append("-o2")
                ArgsList.append(str(O2))
            if O3 > 0:
                ArgsList.append("-o3")
                ArgsList.append(str(O3))
        else:    
            ArgsList.append("--nooutput")
        return ArgsList
        
    def generateEnvList( self, index ):
        """ Generates the environment variables list for an application of type SMPI1 """
        EnvList = [ 
            ("GLOBUS_DUROC_SUBJOB_INDEX", "%d" % index),
            ("LD_LIBRARY_PATH", "/usr/local/globus/globus-3.2/lib/") 
            ]
        return EnvList
        
    def generateStageInList( self, StageInData ):
        """ 
        Generates the stagein list for an application of type SMPI1 
        
        In:
            StageInData -- A dictionary of data required for generating the 
                           stagein list. For SMPI1, it has one key: 'EmptyFileName'
        """
        StageInList = [ StageInData['EmptyFileName'] ]
        return StageInList
        
    def generateStageOutList( self, StageOutData ):
        """ 
        Generates the stagein list for an application of type SMPI1 
        
        In:
            StageInData -- A dictionary of data required for generating the 
                           stagein list. For SMPI1, it is empty
        """
        StageOutList = [ ]
        for FileData in StageOutData.keys():
            StageOutList.append(FileData)
        return StageOutList
        
    def getComponentData(self):
        return self.ComponentData
        

    def generateComponent( self, bGenerateRandom = 1, \
        Size = 0, N = 0, M = 0, S = 0, X = 0, C = 0, MaxWallTime = 0 ):
        """
        
        Generates one component using SMPI1 as the application. 
        
        This method does NOT write a physical JDF, but generates 
        all the needed parameters, directories, and input files 
        instead. The WLMain.generateWorkload is responsible for 
        actualy writing the JDFs. 
        
        In:
            bGenerateRandom -- whether this component is to be generated randomly 
                               (>0 for true, <=0 for false)
            size, N, M, S, X, C, MaxWallTime -- only valid if bGenerateRandom is 0
        
        Return:
            Int, >=0 on success, <0 otherwise
            
        Notes:
          o Upon success, the ComponentData will contain at least the following
            fields:
            executable    -- the complete path to an executable file
            stdout        -- a file that will receive the standard output messages
            stderr        -- a file that will receive the standard error messages
            name          -- a name for this component (if unique, the better)
            description   -- a description of this component
            directory     -- the directory where the component should run
            maxWallTime   -- the max time requested this app should run
            arguments     -- the list of arguments to be fed to the component's application
            env           -- the list of environmental variables, as (Name, Value) tuples
            stagein       -- a list of files to be staged in
            stageout      -- a list of files to be staged out
        
        """
        if bGenerateRandom > 0:
            if self.HaveInput > 0:
                InputSize = AIRandomUtils.getRandomListElement( SMPI1Component.SMPI1_ParKSuperSizes )
            else:
                InputSize = 0
            if self.HaveOutput > 0:
                OutputSize = AIRandomUtils.getRandomListElement( SMPI1Component.SMPI1_ParKSuperSizes )
            else:
                OutputSize = 0
            N = AIRandomUtils.getRandomListElement( SMPI1Component.SMPI1_ParSupersteps )
            M = AIRandomUtils.getRandomListElement( SMPI1Component.SMPI1_ParMemoryKItems )
            S = AIRandomUtils.getRandomListElement( SMPI1Component.SMPI1_ParMemoryElementsPerItem )
            X = AIRandomUtils.getRandomListElement( SMPI1Component.SMPI1_ParXChangeElementsPerStep )
            C = AIRandomUtils.getRandomListElement( SMPI1Component.SMPI1_ParComputationPerMemoryItem )
            MaxWallTime = AIRandomUtils.getRandomListElement( SMPI1Component.SMPI1_RunTimeInMinutes )
        
        ## too long component dir name
        #ComponentDirName = "%s_smpi1_%dx_%d_i%d_o%d" % \
        #        (self.ComponentData['id'], self.ComponentData['count'], int(N), int(InputSize), int(OutputSize))
        ComponentDirName = "%s" % self.ComponentData['id']
        FullComponentDirName = os.path.join( self.BaseDir, ComponentDirName ) 
        #--- Create component directory, if it does not exist
        if os.path.exists( FullComponentDirName ):
            if not os.path.isdir( FullComponentDirName ):
                print "Output for job", self.ComponentData['id'], "("+FullComponentDirName+")", "exists, but is not a directory", "...skipping job"
                return -1
        else:
            try:
                os.makedirs( FullComponentDirName )
            except OSError, e:
                print "Cannot create output directory for job", self.ComponentData['id'] , "...skipping job"
                print '\tOS returned:', e
                return -1
                
        # support the directory stagein
        EmptyFileName = os.path.join( FullComponentDirName, "__empty_file__" )
        try:
            EmptyFile = open( EmptyFileName, "w" )
            EmptyFile.close()
        except:
            pass 
                
        OutFileName = "%s.jdf" % ComponentDirName
        FullOutFileName = os.path.join( self.BaseDir, OutFileName ) 
        
        #--- generate other component data 
        #    the initial part is generated in generateJobComponents
        self.ComponentData['name']   = "%s_smpi1" % self.ComponentData['id']
        self.ComponentData['description'] = \
                    "SMPI1, Count=%d, N=%d, M=%d, S=%d, X=%d, C=%d, I1=I2=%d, O1=O2=O3=%d" % \
                    (int(self.ComponentData['count']), int(N), int(M), int(S), int(X), int(C), int(InputSize), int(OutputSize))
        self.ComponentData['directory'] = FullComponentDirName
        self.ComponentData['maxWallTime'] = MaxWallTime
        self.ComponentData['stdout'] = os.path.join( FullComponentDirName, "smpi1-%s.out" % self.ComponentData['id'] )
        self.ComponentData['stderr'] = os.path.join( FullComponentDirName, "smpi1-%s.err" % self.ComponentData['id'] )
        
        # I1 = InputSize, I2 = InputSize, O1 = OutputSize, O2 = OutputSize, O3 = OutputSize
        self.ComponentData['arguments'] = \
            self.generateArgsList( InputSize, InputSize, OutputSize, OutputSize, OutputSize, N, M, S, X, C )
        self.ComponentData['env'] = self.generateEnvList( self.ComponentIndex )
        
        StageInData = { 'EmptyFileName': os.path.join( FullComponentDirName, os.path.basename(EmptyFileName) ) }
        self.ComponentData['stagein'] = self.generateStageInList( StageInData )
        
        StageOutData = { }
        self.ComponentData['stageout'] = self.generateStageOutList( StageOutData )
        
        return 0
        
def generateJobInfo( UnitDir, UnitID, JobIndex, WLUnit, SubmitDurationMS, Submitter ):
    """ 
    Out:
        A dictionary having at least the keys:
        'name', 'description', 'jdf', 'submitCommand', 'runTime'
        
    See also:
        utils/WLDocHandlers.WLSubmitJobKeys
    """
    global SMPI1_LastRunTime
    
    InfoDic = {}
    JobType = WLUnit['apptype']
    InfoDic['id'] = "%s_%d_%s" % ( UnitID, JobIndex, JobType )
    InfoDic['name'] = "%s_%d_%s__smpi1" % ( UnitID, JobIndex, JobType )
    InfoDic['description'] = \
                "Workload unit %s, job %d, comprising only applications of type %s." % \
                                ( UnitID, JobIndex, JobType )
    InfoDic['jdf'] = os.path.join( UnitDir, "wl-unit-%s-%d.jdf" % (UnitID, JobIndex) )
    
    try:
        SubmitInfoDic = {}
        SubmitInfoDic['JDF'] = InfoDic['jdf']
        InfoDic['submitCommand'] = replaceDic( Submitter, SubmitInfoDic )
    except KeyError, e:
        print '>>>TRACE>>>>', traceback.print_exc()
        print '>>>>>', e
        pass
    except Exception, e:
        print '>>>TRACE>>>>', traceback.print_exc()
        print '>>>>>', e
        pass
    
    if 'submitCommand' not in InfoDic.keys():
        InfoDic['submitCommand'] = 'run.test.sh'
        print 'WARNING!', 'All SubmitCommand parsing failed!', 'Assigned default', InfoDic['submitCommand']
    
    try:
        Name = WLUnit['arrivaltimeinfo'][0]
        ParamsList = WLUnit['arrivaltimeinfo'][1]
        RunTime = SMPI1_LastRunTime + WLUnit['arrivaltimefunc']( Name, ParamsList )
        SMPI1_LastRunTime = RunTime
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
    
def generateJobComponents( UnitDir, UnitID, JobIndex, WLUnit, PreComponentsList, \
                           Application, AppBaseDir, \
                           bGenerateRandom = 1, \
                           Size = 0, N = 0, M = 0, S = 0, X = 0, C = 0, MaxWallTime = 0):
        
    if UnitDir[0] != '/':
        if sys.platform.find("linux") >= 0:
            UnitDir = os.path.join( os.environ['PWD'], UnitDir )
        else:
            UnitDir = os.path.join( os.getcwd(), UnitDir )
        ### THE UGLY HACK: convert /disk1/home3/koala5/grenchmark to /home/koala5/grenchmark
        pos = UnitDir.find('/koala')
        if pos >= 0:
            print 'WARNING! SMPI1 replacing current UnitDir', UnitDir, 
            UnitDir = '/home' + UnitDir[pos:]
            print 'with', UnitDir
        
    ComponentsList = []
    
    NumComponents = len(PreComponentsList)
    
    ComponentDirName = "%s-%d_smpi_%dc" % ( UnitID, JobIndex, NumComponents )
    FullComponentDirName = os.path.join( UnitDir, ComponentDirName ) 
    #--- Create job directory, if it does not exist
    ### NOTE: this is redundant, as the job's components will create the subdirs 
    ###       and all the path to the subdirs, including the job directory
    if os.path.exists( FullComponentDirName ):
        if not os.path.isdir( FullComponentDirName ):
            print "Output for job", JobIndex, "("+FullComponentDirName+")", "exists, but is not a directory", "...skipping job"
            return None
    else:
        try:
            os.makedirs( FullComponentDirName )
        except OSError, e:
            print "Cannot create output directory for job", JobIndex, "...skipping job"
            print '\tOS returned:', e
            return None
    
    for PreComponent in PreComponentsList:
        #--- reset component data
        ComponentData = {}
        
        #--- generate initial component data
        ComponentData['id'] = "%s-%d-%2.2d" % ( UnitID, PreComponent['id'], JobIndex )
        ComponentData['location'] = PreComponent['location']
        ComponentData['count'] = PreComponent['count']
        ComponentData['jobtype'] = 'mpi'
        ComponentData['executable'] = os.path.join(AppBaseDir, Application)
        
        OneSMPI1 = SMPI1Component( FullComponentDirName, PreComponent['id'], ComponentData )
        if OneSMPI1.generateComponent( bGenerateRandom, Size, N, M, S, X, C, MaxWallTime ) >= 0: 
            # job successfully generated
                
            #-- get the new component data
            ComponentData = OneSMPI1.getComponentData()
            #-- add component to the job
            ComponentsList.append( ComponentData )
            #-- ack component
        
    return ComponentsList
    
def generateWorkloadUnit( UnitDir, UnitID, WLUnit, SubmitDurationMS, bGenerateRandom = 1 ):
    """ 
    Out:
        UnitsDic 
            o A dictionary with keys 'info' and 'jobs'.
            
    Notes:
        o UnitsDic['info'] contains a dictionary of jobs info, 
          indexed with an integer counter
        o Each job info contains at least the keys
          name, description, jdf, submitCommand, runTime
        o UnitsDic['jobs'] contains a dictionary of jobs data, 
          indexed with an integer counter
        o Each job data contains the list of components of that job
        o Each component in the list is a dictionary with at least the 
          following fields: executable, stdout, stderr, name, description,
          directory, maxWallTime, arguments, env, stagein, stageout 
        
    See also:
        utils/WLDocHandlers.WLSubmitJobKeys
        this_file.SMPI1Component.generateComponent
    """
    
    global SMPI1_LastRunTime
    
    SMPI1Component.SMPI1_Exe = os.path.join( "/tmp", "smpi1t" )
    SMPI1Component.SMPI1_ParKSizes = [ "0", "32", "128", "512", "1024" ]
    SMPI1Component.SMPI1_ParKSuperSizes = [ "0", "16", "32", "64", "128", "256" ]
    SMPI1Component.SMPI1_ParSupersteps = [ "1", "2", "5", "10", "20", "50", "100" ]
    SMPI1Component.SMPI1_ParMemoryKItems = [ "10", "25", "50", "100", "250", "500", "1000", "5000" ]
    SMPI1Component.SMPI1_ParMemoryElementsPerItem = [ "3", "4", "10", "100", "500", "1000" ]
    SMPI1Component.SMPI1_ParXChangeElementsPerStep = [ "100", "500", "1000", "10000", "50000" ]
    SMPI1Component.SMPI1_ParComputationPerMemoryItem = [ "2", "10", "100", "1000" ]        
    SMPI1Component.SMPI1_RunTimeInMinutes = [ "2", "5", "10", "15" ]
    
    if 'otherinfo' in WLUnit.keys():
        
        try:
            OneString = WLUnit['otherinfo']['Exe']
            SMPI1Component.SMPI1_Exe = OneString
        except KeyError:
            pass
        
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParKSizes'], 
                    ItemSeparator = ',' )
            SMPI1Component.SMPI1_ParKSizes = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParKSuperSizes'], 
                    ItemSeparator = ',' )
            SMPI1Component.SMPI1_ParKSuperSizes = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParSupersteps'], 
                    ItemSeparator = ',' )
            SMPI1Component.SMPI1_ParSupersteps = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParMemoryKItems'], 
                    ItemSeparator = ',' )
            SMPI1Component.SMPI1_ParMemoryKItems = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParMemoryElementsPerItem'], 
                    ItemSeparator = ',' )
            SMPI1Component.SMPI1_ParMemoryElementsPerItem = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParXChangeElementsPerStep'], 
                    ItemSeparator = ',' )
            SMPI1Component.SMPI1_ParXChangeElementsPerStep = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParComputationPerMemoryItem'], 
                    ItemSeparator = ',' )
            SMPI1Component.SMPI1_ParComputationPerMemoryItem = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['RunTimeInMinutes'], 
                    ItemSeparator = ',' )
            SMPI1Component.SMPI1_RunTimeInMinutes = OneIntList
        except KeyError:
            pass
        
        try:
            NComponentsWithWeightsDic = \
                AIParseUtils.readIntWithWeightsList( 
                    WLUnit['otherinfo']['NComponentsWithWeights'], 
                    DefaultWeight = 1.0 
                    )
            # NComponentsWithWeightsDic['Values']; NComponentsWithWeightsDic['TotalWeight']
        except KeyError:
            raise Exception, "SMPI1 generator: Invalid NComponentsWithWeights info specified in the OtherInfo field."
        ##print ">>>>>> NComponentsWithWeightsDic", NComponentsWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
        try:
            TotalCPUsWithWeightsDic = \
                AIParseUtils.readIntWithWeightsList( 
                    WLUnit['otherinfo']['TotalCPUsWithWeights'], 
                    DefaultWeight = 1.0 
                    )
        except KeyError:
            raise Exception, "SMPI1 generator: Invalid TotalCPUsWithWeights info specified in the OtherInfo field."
        ##print ">>>>>> TotalCPUsWithWeightsDic", TotalCPUsWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
        
        try:
            MinComponentSize = AIParseUtils.readInt(WLUnit['otherinfo']['MinComponentSize'], DefaultValue = 0)
        except KeyError:
            MinComponentSize = 1
            #raise Exception, "SMPI1 generator: No MinComponentSize info specified in the OtherInfo field."
            
        try:
            MaxComponentSize = AIParseUtils.readInt(WLUnit['otherinfo']['MaxComponentSize'], DefaultValue = 0)
        except KeyError:
            MaxComponentSize = 10000000
            #raise Exception, "SMPI1 generator: No MaxComponentSize info specified in the OtherInfo field."
        
        try:
            EqualCPUsPerComponent = AIParseUtils.readBoolean(WLUnit['otherinfo']['SMPI1AppsDir'])
        except KeyError:
            EqualCPUsPerComponent = 0
            #raise Exception, "SMPI1 generator: No EqualCPUsPerComponent info specified in the OtherInfo field. Setting to default " + AIParseUtils.IntToBooleanDic[EqualCPUsPerComponent] + '.'
        
        try:
            AppBaseDir = WLUnit['otherinfo']['AppBaseDir']
        except KeyError:
            AppBaseDir = '/tmp'
            #raise Exception, "SMPI1 generator: No AppBaseDir info specified in the OtherInfo field."
            print "WARNING! SMPI1 generator: No AppBaseDir info specified in the OtherInfo field.", "Assuming default:", AppBaseDir
            
        try:
            Application = WLUnit['otherinfo']['Application']
        except KeyError:
            Application = 'smpi1t-gm'
            #raise Exception, "SMPI1 generator: No AppBaseDir info specified in the OtherInfo field."
            print "WARNING! SMPI1 generator: No Application info specified in the OtherInfo field.", "Assuming default:", Application
        
        try:
            Submitter = WLUnit['otherinfo']['Submitter']
        except KeyError:
            Submitter = 'run.test.sh'
            print "WARNING! SMPI1 generator: No Submitter info specified in the OtherInfo field.", "Assuming default", Submitter
            
        try:
            SiteTypesWithWeightsDic = \
                AIParseUtils.readStringWithWeightsList( 
                    WLUnit['otherinfo']['SiteTypesWithWeights'], 
                    DefaultWeight = 1.0 
                    )
        except KeyError:
            SiteTypesWithWeights = {AIParseUtils.VALUES:[], AIParseUtils.TOTAL_WEIGHT:0.0 }
            print "WARNING! SMPI1 generator: No SiteTypesWithWeights info specified in the OtherInfo field.\n\tSetting to default", SitesList
        ##print ">>>>>> SiteTypesWithWeightsDic", SiteTypesWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
        try:
            SitesWithWeightsDic = \
                AIParseUtils.readStringWithWeightsList( 
                    WLUnit['otherinfo']['SitesWithWeights'], 
                    DefaultWeight = 1.0 
                    )
        except KeyError:
            SitesWithWeightsDic = {AIParseUtils.VALUES:[], AIParseUtils.TOTAL_WEIGHT:0.0 }
            print "WARNING! SMPI1 generator: No SitesWithWeights info specified in the OtherInfo field.\n\tSetting to default", SitesList
        ##print ">>>>>> SitesWithWeightsDic", SitesWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
            
    else:
        raise Exception, "SMPI1 generator: No OtherInfo data! Expected at least ComponentSize,NJobs,NComponents fields."
    
    
    UnitsDic = {}
    UnitsDic['info'] = {}
    UnitsDic['jobs'] = {}
    
    #-- init start time
    try:
        StartAt = AIParseUtils.readInt(WLUnit['otherinfo']['StartAt'], DefaultValue = 0)
        StartAt = StartAt * 1000 # the time is given is seconds
    except KeyError:
        StartAt = 0
    SMPI1_LastRunTime = StartAt
    
    if 'FirstJobIndex' in WLUnit:
        JobIndex = int(WLUnit['FirstJobIndex'])
    else: 
        JobIndex = 0
    
    WLUnitMultiplicity = int(WLUnit['multiplicity'])
    if bGenerateRandom > 0 :
        
        index = 0
        while index < WLUnitMultiplicity:
            # 1. generate a random site type (unordered or ordered)
            SiteType = AIRandomUtils.getRandomWeightedListElement(
                            SiteTypesWithWeightsDic,
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            )
                            
            # 2. select the number of CPU for this job
            #TODO: repeat NCPUs selection until App can run on that many CPUs
            NCPUs = AIRandomUtils.getRandomWeightedListElement(
                       TotalCPUsWithWeightsDic,
                       ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                    )
            # 3. select the number of components and try to create subcomponents,
            #    until successfully matching restrictions
            WhileCondition = 1
            NTries = 100
            while WhileCondition != 0 and NTries > 0:
                
                NTries = NTries - 1
                
                NComponents = AIRandomUtils.getRandomWeightedListElement(
                                    NComponentsWithWeightsDic,
                                    ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                                    )
                                    
                if NComponents > NCPUs: 
                    continue # impossible match, just retry
                
                NCPUsPerComponent = NCPUs / NComponents
                # ensure restrictions are met
                if NCPUsPerComponent < MinComponentSize or NCPUsPerComponent > MaxComponentSize:
                    continue
                
                NRemainingComponents = NCPUs - NCPUsPerComponent * NComponents
                if NRemainingComponents > 0 and EqualCPUsPerComponent == 1:
                    continue
                
                # >= -> including the extra CPU for some components
                if NRemainingComponents > 0 and NCPUsPerComponent == MaxComponentSize:
                    continue
                
                PreComponentsList = []
                for ComponentID in xrange(NComponents):
                    
                    # cpu count
                    ToAssignHere = NCPUsPerComponent
                    if ComponentID < NRemainingComponents: # assign the extra CPUs, round-robin
                        ToAssignHere = ToAssignHere + 1
                        
                    # site location
                    if SiteType == 'ordered':
                        Site = AIRandomUtils.getRandomWeightedListElement(
                                    SitesWithWeightsDic,
                                    ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                                    )
                    else:
                        Site = '*'
                        
                    # create pre-component information
                    PreComponent = {}
                    PreComponent['id'] = ComponentID
                    PreComponent['count'] = ToAssignHere
                    PreComponent['location'] = Site
                    
                    # add pre-component
                    PreComponentsList.append(PreComponent)
                    
                WhileCondition = 0
                    
            if WhileCondition == 1: # failed to generate in 100 tries
                continue # try again for the same job
                
            #--- generate rnd job
            #-- generate job info
            UnitsDic['info'][index] = \
               generateJobInfo( UnitDir, UnitID, JobIndex, \
                                WLUnit, SubmitDurationMS, Submitter )
                                
            #-- generate job components
            UnitsDic['jobs'][index] = \
               generateJobComponents( UnitDir, UnitID, JobIndex, WLUnit, PreComponentsList, \
                                      Application, AppBaseDir, \
                                      bGenerateRandom )
            index = index + 1
            JobIndex = JobIndex + 1
        WLUnit['generatedjobs'] = index
        
    else:
        index = 0
        for Size in SMPI1Component.SMPI1_ParKSuperSizes:
            for N in SMPI1Component.SMPI1_ParSupersteps:
                for M in SMPI1Component.SMPI1_ParMemoryKItems:
                    for S in SMPI1Component.SMPI1_ParMemoryElementsPerItem:
                        for X in SMPI1Component.SMPI1_ParXChangeElementsPerStep:
                            for C in SMPI1Component.SMPI1_ParComputationPerMemoryItem:
                                
                                raise Exception, "ERROR! SMPI1 is not finished!"
                                
                                #--- generate wall time once for all components of this job
                                MaxWallTime = AIRandomUtils.getRandomListElement( SMPI1Component.SMPI1_RunTimeInSeconds )
                                #-- generate a random site type (unordered, ordered, ...)
                                SiteType = AIRandomUtils.getRandomWeightedListElement(
                                                SiteTypesWithWeightsDic,
                                                ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                                                )
                                #-- generate job info
                                UnitsDic['info'][index] = \
                                   generateJobInfo( UnitDir, UnitID, JobIndex, \
                                                    WLUnit, SubmitDurationMS )
                                #-- generate job components
                                UnitsDic['jobs'][index] = \
                                   generateJobComponents( UnitDir, UnitID, JobIndex, WLUnit, \
                                                          bGenerateRandom, SiteType, Size, \
                                                          N, M, S, X, C, MaxWallTime )
                                index = index + 1
                                JobIndex = JobIndex + 1
        #-- set generated jobs
        WLUnit['generatedjobs'] = index
        
    return UnitsDic
    
    
if __name__ == "__main__":
    print "SMPI1-workload"
    pass
    
