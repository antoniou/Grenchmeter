Generator="""
    Name=sser
    Info=Workload based on the synthetic serial application
    Author=A. Iosup
    Contact=email:A.Iosup@ewi.tudelft.nl
    License=Python
    """
# --------------------------------------
# Log:
# 15/10/2007 C.S. 0.2 Modified the command used to submit the jobs
#
# --------------------------------------

import os.path

import sys
if "utils" not in sys.path:
    sys.path.append("utils")
import AIRandomUtils
import AIParseUtils

SSER_LastRunTime = 0

class SSERComponent:
    
    SSER_Exe = "python "#os.path.join( "/tmp", "ssert" )
        
    SSER_ParKSizes = ( "0", "32", "128", "512", "1024" )
    SSER_ParKSuperSizes = ( "0", "16", "32", "64", "128", "256" )
    SSER_ParSupersteps = ( "1", "2", "5", "10", "20", "50", "100" )
    SSER_ParMemoryKItems = ( "10", "25", "50", "100", "250", "500", "1000", "5000" ) 
    SSER_ParMemoryElementsPerItem = ( "3", "4", "10", "100", "500", "1000" )    
    SSER_ParComputationPerMemoryItem = ( "2", "10", "100", "1000" )
        
    SSER_RunTimeInMinutes = ( "2", "5", "10", "15" )
    
    def __init__( self, UnitDir, ComponentIndex, ComponentData, HaveInput = 0, HaveOutput = 0 ):
        """ 
        Init a SSER Component 
        
        In:
            UnitDir       -- physical location of this workload unit
            ComponentIndex -- used to identify this component within the workload unit
            ComponentData  -- a component data dictionary, with the following fields
                              already set:
                              id -- component's ID (if unique, the better)
                              count -- the number of apps to be executed in this component
        """
        self.UnitDir = UnitDir
        self.ComponentIndex = ComponentIndex
        self.ComponentData = ComponentData
        self.HaveInput = HaveInput
        self.HaveOutput = HaveOutput
        
    def generateArgsList(self, I1, I2, O1, O2, O3, N, M, S, C ):
        """
        Generates the arguments list for an application of type SSER
        
        In: (specific parameters of SSER applications)
        """
        ArgsList = [ 
            "-n", str(N), 
           # "-m", str(M), 
           # "-s", str(S), 
            "-c", str(C), 
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
            
        ArgsList.append("--nosummary")
        ArgsList.append("--verbose")
        return ArgsList
        
    def generateEnvList( self, index ):
        """ Generates the environment variables list for an application of type SSER """
        EnvList = [ 
            ("GLOBUS_DUROC_SUBJOB_INDEX", "%d" % index),
            ("LD_LIBRARY_PATH", "/usr/local/globus/globus-3.2/lib/") 
            ]
        return EnvList
        
    def generateStageInList( self, StageInData ):
        """ 
        Generates the stagein list for an application of type SSER 
        
        In:
            StageInData -- A dictionary of data required for generating the 
                           stagein list. For SSER, it has one key: 'EmptyFileName'
        """
        StageInList = [ StageInData['EmptyFileName'] ]
        return StageInList
        
    def generateStageOutList( self, StageOutData ):
        """ 
        Generates the stagein list for an application of type SSER 
        
        In:
            StageInData -- A dictionary of data required for generating the 
                           stagein list. For SSER, it is empty
        """
        StageOutList = [ ]
        return StageOutList
        
    def getComponentData(self):
        return self.ComponentData
        

    def generateComponent( self, bGenerateRandom = 1, \
        Size = 0, N = 0, M = 0, S = 0, C = 0, MaxWallTime = 0 ):
        """
        
        Generates one component using SSER as the application. 
        
        This method does NOT write a physical JDF, but generates 
        all the needed parameters, directories, and input files 
        instead. The WLMain.generateWorkload is responsible for 
        actualy writing the JDFs. 
        
        In:
            bGenerateRandom -- whether this component is to be generated randomly 
                               (>0 for true, <=0 for false)
            size, N, M, S, C, MaxWallTime -- only valid if bGenerateRandom is 0
        
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
                InputSize = AIRandomUtils.getRandomListElement( SSERComponent.SSER_ParKSuperSizes )
            else:
                InputSize = 0
            if self.HaveOutput > 0:
                OutputSize = AIRandomUtils.getRandomListElement( SSERComponent.SSER_ParKSuperSizes )
            else:
                OutputSize = 0
            N = AIRandomUtils.getRandomListElement( SSERComponent.SSER_ParSupersteps )
            M = AIRandomUtils.getRandomListElement( SSERComponent.SSER_ParMemoryKItems )
            S = AIRandomUtils.getRandomListElement( SSERComponent.SSER_ParMemoryElementsPerItem )
            C = AIRandomUtils.getRandomListElement( SSERComponent.SSER_ParComputationPerMemoryItem )

#            N = SSERComponent.SSER_ParSupersteps[2]
#            M = AIRandomUtils.getRandomListElement( SSERComponent.SSER_ParMemoryKItems )
#            S = AIRandomUtils.getRandomListElement( SSERComponent.SSER_ParMemoryElementsPerItem )
#            C = SSERComponent.SSER_ParComputationPerMemoryItem[3]

            MaxWallTime = AIRandomUtils.getRandomListElement( SSERComponent.SSER_RunTimeInMinutes )
        
        if self.UnitDir[0] != '/':
            if sys.platform.find("linux") >= 0:
                self.UnitDir = os.path.join( os.environ['PWD'], self.UnitDir )
            else:
                self.UnitDir = os.path.join( os.getcwd(), self.UnitDir )
        
        ## too long component dir name
        #ComponentDirName = "%s_sser_%dx_%d_i%d_o%d" % \
        #        (self.ComponentData['id'], self.ComponentData['count'], int(N), int(InputSize), int(OutputSize))
        ComponentDirName = "%s_sser" % self.ComponentData['id']
        FullComponentDirName = os.path.join( self.UnitDir, ComponentDirName ) 
        #--- Create output directory, if it does not exist
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
        FullOutFileName = os.path.join( self.UnitDir, OutFileName ) 
        
        self.ComponentData['executable'] = SSERComponent.SSER_Exe
        self.ComponentData['stdout'] =  "sser-"+self.ComponentData['id']+".out"#os.path.join( FullComponentDirName, "sser-%s.out" % self.ComponentData['id'] )
        self.ComponentData['stderr'] = "sser-"+self.ComponentData['id']+".err"#os.path.join( FullComponentDirName, "sser-%s.err" % self.ComponentData['id'] )
        self.ComponentData['logfile'] = os.path.join( FullComponentDirName, "sser-%s.log" % self.ComponentData['id'] )
        self.ComponentData['name']   = "%s_sser" % self.ComponentData['id']
        self.ComponentData['description'] = \
                    "SSER, Count=%d, N=%d, M=%d, S=%d, C=%d, I1=I2=%d, O1=O2=O3=%d" % \
                    (int(self.ComponentData['count']), int(N), int(M), int(S), int(C), int(InputSize), int(OutputSize))
        self.ComponentData['directory'] = FullComponentDirName
        self.ComponentData['maxWallTime'] = MaxWallTime
        
        # I1 = InputSize, I2 = InputSize, O1 = OutputSize, O2 = OutputSize, O3 = OutputSize
        InputSize=0
        self.ComponentData['arguments'] = \
            self.generateArgsList( InputSize, None, OutputSize, OutputSize, OutputSize, N, M, S, C )
        self.ComponentData['env'] = self.generateEnvList( self.ComponentIndex )
        
        #StageInData = { 'EmptyFileName': os.path.join( FullComponentDirName, os.path.basename(EmptyFileName) ) }
        StageInData = {'EmptyFileName': ""  }
        self.ComponentData['stagein'] = self.generateStageInList( StageInData )
        
        StageOutData = { }
        self.ComponentData['stageout'] = self.generateStageOutList( StageOutData )
        
        return 0
        
def generateJobInfo( UnitDir, UnitID, JobIndex, WLUnit, SubmitDurationMS):
    """ 
    Out:
        A dictionary having at least the keys:
        'name', 'description', 'jdf', 'submitCommand', 'runTime'
        
    See also:
        utils/WLDocHandlers.WLSubmitJobKeys
    """
    global SSER_LastRunTime
    InfoDic = {}
    JobType = WLUnit['apptype']
    InfoDic['id'] = "%s_%d_%s" % ( UnitID, JobIndex, JobType )
    InfoDic['name'] = "%s_%d_%s__sser" % ( UnitID, JobIndex, JobType )
    InfoDic['description'] = \
                "Workload unit %s, job %d, comprising only applications of type %s." % \
                                ( UnitID, JobIndex, JobType )
    InfoDic['jdf'] = os.path.join( UnitDir, "wl-unit-%s-%d.jdf" % (UnitID, JobIndex) )
#    InfoDic['submitCommand'] = 'krunner -l DEBUG -g -e -o -f %s' % InfoDic['jdf']
    #InfoDic['submitCommand'] = 'wrapper_scripts/condor_submit_wrapper.sh %s' % InfoDic['jdf']
    absPath = os.path.abspath(InfoDic['jdf'])
    InfoDic['jdf'] = absPath
    
    InfoDic['submitCommand'] = 'python ../Cmeter/ec2br/ec2br.py -p 3000 -u localhost -j %s' % absPath
    
    try:
        Name = WLUnit['arrivaltimeinfo'][0]
        print "In sser-unit: Distribution NAME IS ",Name
        print "In sser-unit: Distribution PARAMS ARE ",WLUnit['arrivaltimeinfo'][1]
        ParamsList = WLUnit['arrivaltimeinfo'][1]
        RunTime = SSER_LastRunTime + WLUnit['arrivaltimefunc']( Name, ParamsList )
        SSER_LastRunTime = RunTime
        InfoDic['runTime'] = "%.3f" % RunTime
        print "In sser-unit: RUNTIME IS ",InfoDic['runTime']
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
    
def generateJobComponents( UnitDir, UnitID, JobIndex, WLUnit, bGenerateRandom = 1, \
    Size = 0, N = 20, M = None, S = None, C = 10, MaxWallTime = 0):
        
    ComponentsList = []
    nValidComponents = 0
    for ComponentID in WLUnit['components'].keys():
        
        Component = WLUnit['components'][ComponentID]
        WLCompName = "%s-%d-%s" % ( UnitID, JobIndex, ComponentID ) # added multiplicity id
        
        #-- set component
        ComponentData = {}
        if bGenerateRandom > 0:
            ComponentData['count'] = int(Component['amount'])
        else:
            ComponentData['count'] = 1
            
        ComponentData['id'] = "%s-%d-%2.2d" % ( UnitID, JobIndex, int(ComponentID) )
            
        ComponentData['location'] = Component['location']
                
        OneSSER = SSERComponent( UnitDir, nValidComponents, ComponentData )
        if OneSSER.generateComponent( bGenerateRandom, Size, N, M, S, C, MaxWallTime ) >= 0: 
            # job successfully generated
                
            #-- get the new component data
            ComponentData = OneSSER.getComponentData()
            #-- add component to the job
            ComponentsList.append( ComponentData )
            #-- ack component
            nValidComponents = nValidComponents + 1 
        
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
        this_file.SSERComponent.generateComponent
    """
    
    global SSER_LastRunTime
    
            
    SSERComponent.SSER_Exe = "/home/antoniou/Synthetic_Apps/sseriot" #os.path.join( "/tmp", "ssert" )
    SSERComponent.SSER_ParKSizes = [ "0", "32", "128", "512", "1024" ]
    SSERComponent.SSER_ParKSuperSizes = [ "0", "16", "32", "64", "128", "256" ]
    SSERComponent.SSER_ParSupersteps = [ "1", "2", "5", "10", "20", "50", "100" ]
    SSERComponent.SSER_ParMemoryKItems = [ "10", "25", "50", "100", "250", "500", "1000", "5000" ]
    SSERComponent.SSER_ParMemoryElementsPerItem = [ "3", "4", "10", "100", "500", "1000" ]
    SSERComponent.SSER_ParComputationPerMemoryItem = [ "2", "10", "100", "1000" ]        
    SSERComponent.SSER_RunTimeInMinutes = [ "2", "5", "10", "15" ]
    
    if 'otherinfo' in WLUnit.keys():
        
        try:
            OneString = WLUnit['otherinfo']['Exe']
            SSERComponent.SSER_Exe = OneString
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParKSizes'], 
                    ItemSeparator = ',' )
            SSERComponent.SSER_ParKSizes = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParKSuperSizes'], 
                    ItemSeparator = ',' )
            SSERComponent.SSER_ParKSuperSizes = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParSupersteps'], 
                    ItemSeparator = ',' )
            SSERComponent.SSER_ParSupersteps = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParMemoryKItems'], 
                    ItemSeparator = ',' )
            SSERComponent.SSER_ParMemoryKItems = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParMemoryElementsPerItem'], 
                    ItemSeparator = ',' )
            SSERComponent.SSER_ParMemoryElementsPerItem = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['ParComputationPerMemoryItem'], 
                    ItemSeparator = ',' )
            SSERComponent.SSER_ParComputationPerMemoryItem = OneIntList
        except KeyError:
            pass
            
        try:
            OneIntList = AIParseUtils.readIntList( 
                    Text = WLUnit['otherinfo']['RunTimeInMinutes'], 
                    ItemSeparator = ',' )
            SSERComponent.SSER_RunTimeInMinutes = OneIntList
        except KeyError:
            pass
    
    UnitsDic = {}
    UnitsDic['info'] = {}
    UnitsDic['jobs'] = {}
    
    #-- init start time
    try:
        StartAt = AIParseUtils.readInt(WLUnit['otherinfo']['StartAt'], DefaultValue = 0)
        StartAt = StartAt * 1000 # the time is given is seconds
    except KeyError:
        StartAt = 0
    SSER_LastRunTime = StartAt
    
    if 'FirstJobIndex' in WLUnit:
        JobIndex = int(WLUnit['FirstJobIndex'])
    else: 
        JobIndex = 0
    
   
    if bGenerateRandom > 0 :
        index = 0
        maxIndex = WLUnit['multiplicity']
        while index < maxIndex:
            UnitsDic['info'][index] = \
               generateJobInfo( UnitDir, UnitID, JobIndex, \
                                WLUnit, SubmitDurationMS )
            UnitsDic['jobs'][index] = \
               generateJobComponents( UnitDir, UnitID, JobIndex, WLUnit, \
                                      bGenerateRandom )
            index = index + 1
            JobIndex = JobIndex + 1
        WLUnit['generatedjobs'] = index
        
    else:
        index = 0
        for Size in SSERComponent.SSER_ParKSuperSizes:
            for N in SSERComponent.SSER_ParSupersteps:
                for M in SSERComponent.SSER_ParMemoryKItems:
                    for S in SSERComponent.SSER_ParMemoryElementsPerItem:
                        for C in SSERComponent.SSER_ParComputationPerMemoryItem:
                            for MaxWallTime in SSERComponent.SSER_RunTimeInSeconds:
                                UnitsDic['info'][index] = \
                                   generateJobInfo( UnitDir, UnitID, JobIndex, \
                                                    WLUnit, SubmitDurationMS )
                                UnitsDic['jobs'][index] = \
                                   generateJobComponents( UnitDir, UnitID, JobIndex, WLUnit, \
                                                          bGenerateRandom, Size, N, M, S, C, MaxWallTime)
                                
                                index = index + 1
                                JobIndex = JobIndex + 1
        #-- set generated jobs
        WLUnit['generatedjobs'] = index
        
    return UnitsDic
    
    
if __name__ == "__main__":
    print "sser-workload"
    pass
    
