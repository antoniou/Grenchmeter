WLGenerator="""
    Name=ibis
    Info=Workload based on the Ibis applications
    Author=A. Iosup
    Contact=email:A.Iosup@ewi.tudelft.nl
    """
    
import os.path

import sys
if "utils" not in sys.path:
    sys.path.append("utils")
import AIRandomUtils
import AIParseUtils
import EFFBotMultiReplace
import string
import traceback

   
# Applications are indexed by their name. An application tuple includes:
# Dir Archive Executable ParamsList StageIn StageOut MaxReqMemory Description 
# Note: the Dir should be relative to the IbisAppsDir, passed in the OtherInfo
class IBISConsts:
    Dir = 0 
    Archive = 1
    Executable = 2 
    ParamsList = 3
    StageIn = 4
    StageOut = 5
    MaxReqMemory = 6
    Description =7
    
IBIS_Apps = {
    'Ibis:Cell1D': ( 'apps/ibis/cell1d', 'cell1d.jar', 'Cell1D', '-size 10000 10', '', '', 800, 'Cellular Automata 1D' ),
    #'Ibis:SOR': ( 'apps/ibis/sor/explicit', 'sor.jar', 'SOR', '1024 0', '', '', 800, 'Successive Over-Relaxation' ),
    'RMI:SOR': ( 'apps/rmi/sor_grid', 'sorgrid.jar', 'Main', '4096 4096 0 async', '', '', 800, 'Successive Over-Relaxation' ),
    'RMI:ACP': ( 'apps/rmi/acp', 'acp.jar', 'ACP', 'input0', 'input0', '', 800, 'Arc Consistency Checker' ),
    'GMI:ACP': ( 'apps/gmi/acp', 'acp.jar', 'ACP', 'input0', 'input0', '', 800, 'Arc Consistency Checker' ),
    'RMI:ASP': ( 'apps/rmi/asp_toplass', 'asptop.jar', 'Main', '1000 -thread-pool', '', '', 800, 'All-Pairs Shortest Path' ),
    'GMI:ASP': ( 'apps/gmi/asp', 'asp.jar', 'Main', '1000', '', '', 800, 'All-Pairs Shortest Path' ),
    'RMI:FFT1D': ( 'apps/rmi/fft', 'fft1d.jar', 'fft', '22 -warmup 4', '', '', 800, 'Fast Fourier Transform 1D' ),
    'GMI:FFT1D': ( 'apps/gmi/fft', 'fft1d.jar', 'Main', '20', '', '', 800, 'Fast Fourier Transform 1D' ),
    'Satin:FFT1D': ( 'apps/satin/fft', 'fft1d.jar', 'FFT', '524288', '', '', 800, 'Fast Fourier Transform 1D' ),
    'RMI:LEQ': ( 'apps/rmi/leq', 'leq.jar', 'Main', '', '', '', 800, 'Linear Equation Solver' ),
    'GMI:LEQ': ( 'apps/gmi/leq', 'leq.jar', 'Main', '1000', '', '', 800, 'Linear Equation Solver' ),
    'RMI:QR': ( 'apps/rmi/qr', 'qr.jar', 'Main', '', '', '', 800, 'QR factorization' ),
    'GMI:QR': ( 'apps/gmi/QR', 'qr.jar', 'Main', '2000', '', '', 800, 'QR factorization' ),
    'RMI:TSP': ( 'apps/rmi/tsp', 'tsp.jar', 'Server', 'table_15.1 -bound 300', 'table_15.1', '', 800, 'Travelling Salesperson Problem' ),
    'GMI:TSP': ( 'apps/gmi/tsp', 'tsp.jar', 'Main', 'table_15.1 -bound 300', 'table_15.1', '', 800, 'Travelling Salesperson Problem' ),
    'Satin:TSP': ( 'apps/satin/tsp', 'tsp.jar', 'Tsp', '-seed 100 -bound 289 17', 'table_17.1', '', 800, 'Travelling Salesperson Problem' ),
    'Satin:TSP-Tuples': ( 'apps/satin/tsp_tuple', 'tspt.jar', 'Tsp', '-seed 100 -bound 289 17', 'table_17.1', '', 800, 'Travelling Salesperson Problem' ),
    'RMI:BarnesHutt': ( 'apps/rmi/barnes', 'barnes.jar', 'BarnesHutt', '-N50000 -M10 -tstop 0.25 -dtime 0.025', '', '', 800, 'The Barnes-Hutt Algorithm for N-Body Simulation' ),
    'Satin:BarnesHutt': ( 'apps/satin/barnes', 'barnes.jar', 'BarnesHut', '-tuple2 -t 6 200000 80 -v', '', '', 800, 'The Barnes-Hutt Algorithm for N-Body Simulation' ),
    'Satin:BarnesHutt-Inline': ( 'apps/satin/barnes_inline', 'barnesi.jar', 'BarnesHut', '-tuple2 -t 6 200000 80 -v', '', '', 800, 'The Barnes-Hutt Algorithm for N-Body Simulation' ),
    'RMI:Radix': ( 'apps/rmi/radix', 'radix.jar', 'Radix', '-r1024 -n1000', '', '', 800, 'Radix parallel sort' ),
    'RMI:Water': ( 'apps/rmi/water', 'water.jar', 'Water', 'random.1728', 'random.1728', '', 800, 'SPLASH suite: N-Body simulation' ),
    'Satin:IDA': ( 'apps/satin/ida', 'ida.jar', 'Ida', '-f inputs/2 -max 70', '', '', 800, 'SPLASH suite: N-Body simulation' ),
    'Satin:Knapsack': ( 'apps/satin/knapsack', 'knapsack.jar', 'Knapsack', '29', '', '', 800, 'Knapsack problem; find a set of items (weight w and value v), such as to maximize the total value, while not exceeding the max weight' ),
    'Satin:PrimFact': ( 'apps/satin/primfac', 'primfac.jar', 'PrimFac', '6678904321', '', '', 800, 'Split a number into its prime factors' ),
    'Satin:Raytracer': ( 'apps/satin/raytracer', 'raytracer.jar', 'Raytracer', 'pics/balls2.nff', 'pics/balls2.nff', 'out.ppm', 800, 'Raytracing application' ),
    'Satin:AdaptInt': ( 'apps/satin/adapint', 'adapint.jar', 'AdapInt', '0 250000 0.000001', '', '', 800, 'Adaptive Numerical Integration' ),
    'Satin:Cover': ( 'apps/satin/cover', 'cover.jar', 'Cover', '30', '', '', 800, 'Set covering' ),
    'Satin:NQueens': ( 'apps/satin/nqueens', 'nqueens.jar', 'NQueens', ['10','12','14','16','18','20'], '', '', 800, 'N-Queens placement problem' ),
    'Satin:Checkers': ( 'apps/satin/checkers', 'checkers.jar', 'Checkers', '-benchmark 2', '', '', 800, 'Set covering' ),
    'Satin:Compress': ( 'apps/satin/grammy', 'grammy.jar', 'Compress', '-verify sample1.txt sample.xxx', 'sample1.txt', 'sample.xxx', 800, 'Grammar-based text compressor' ),
    'Satin:Paraffins': ( 'apps/satin/paraffins', 'paraffins.jar', 'Paraffins', '36', '', '', 800, 'Salishan paraffins problem' ),
    'Satin:SAT': ( 'apps/satin/sat', 'sat.jar', '???', 'examples/benchmarksuite/qg5-10.cnf', '', '', 800, 'SAT solver' ),
    } 

##Verify that one field exists (but not that it's value is what it should be!!!!)
##for Application in IBIS_Apps.keys():
##    try:
##        AppMemoryLimit = IBIS_Apps[Application][IBISConsts.MaxReqMemory]
##    except:
##        raise Exception, 'IBIS generator: Application ' + Application + ' does not have a MaxReqMemory field!'

import re
def ExpandApplication(Application):
    """ 
    replace an ambiguous application name (*) with a real name 
    (randomly selected from the global applications list) 
    """
    
    #-- find all matching names
    FullNamesList = []
    
    #-- replace the user friendly '*' with the Python RegExp correspondent
    Application = Application.replace('*', '\w+') # re's synthax requires + for 1/1+ matches
    SearchRE = re.compile(Application)
    #-- create the list of applications whose name match the request
    for App in IBIS_Apps.keys():
        if SearchRE.search('^' + App):
            FullNamesList.append(App)
            
    #-- select one name or die
    #print FullNamesList
    if len(FullNamesList) == 0:
        raise Exception, 'IBIS generator: Wrong application name ' + Application + ' (cannot expand).'
        
    FullApplicationName = AIRandomUtils.getRandomListElement(FullNamesList)
    return FullApplicationName
    
### Printer    
##import AIStorageUtils
##
##List = AIStorageUtils.dict_sortbykey(IBIS_Apps)
##
##for Key, Value in List:
##    print Key

IBIS_Defs = [ 
    'ibis.name_server.host',
    'ibis.name_server.port',
    'ibis.verbose',
    'ibis.name_server.impl',
    'ibis.name_server.key',
    'ibis.pool.total_hosts',
    'ibis.pool.server.host',
    'ibis.pool.server.port',
    'ibis.pool.cluster',
    'cluster',
    'ibis.library.path',
    'ibis.tcp.cache',
    'ibis.connect.hub.host',
    'ibis.connect.hub.port',
    'ibis.connect.control_links',
    'ibis.connect.data_links',
    'ibis.connect.verbose',
    'ibis.connect.debug'
    ]
    
IBIS_LastRunTime = 0
 
class IBISSelectionMethod:
    
    SM_Random = 0
    SM_WeightedRandom = 1
    SM_RoundRobin = 2
    SM_WeightedRoundRobin = 3
    SM_DefaultSelectionMethod = SM_WeightedRandom
    
    SM_Names = { 
        SM_Random:['Random','R'],
        SM_WeightedRandom:['WeightedRandom','WR'],
        SM_RoundRobin:['RoundRobin','RR'],
        SM_WeightedRoundRobin:['WeightedRoundRobin','WRR'] 
        }
        
    def __init__( self, AppsWithWeightsDic ):
        self.AppsWithWeightsDic = AppsWithWeightsDic
        self.setSelectionMethod( IBISSelectionMethod.SM_DefaultSelectionMethod )
        self.RandomGenerator = AIRandomUtils.AIRandom()
        
    def setAppsWithWeightsDic( self, AppsWithWeightsDic ):
        self.AppsWithWeightsDic = AppsWithWeightsDic
        self.setSelectionMethod( self.SelectionMethod )
        
    def setSelectionMethodByName( self, SelectionMethodName ):
        Method = None
        # find the method by name
        for Key in IBISSelectionMethod.SM_Names.keys():
            NamesList = IBISSelectionMethod.SM_Names[Key]
            if SelectionMethodName in NamesList:
                Method = Key
                break
        if not Method:
            raise Exception, "Method name not found " + SelectionMethodName
        #print '>>>>> Method:', Method
        self.setSelectionMethod( Method )
            
    def setSelectionMethod( self, SelectionMethod ):
        self.SelectionMethod = SelectionMethod
        if self.SelectionMethod == IBISSelectionMethod.SM_Random:
            self.DataList = self.AppsWithWeightsDic.keys()
        elif self.SelectionMethod == IBISSelectionMethod.SM_WeightedRandom:
            self.DataDic = self.AppsWithWeightsDic
        elif self.SelectionMethod == IBISSelectionMethod.SM_RoundRobin:
            self.DataDic = self.AppsWithWeightsDic
            self.Counter = 0
            self.MaxCounter = len(self.DataDic[AIParseUtils.VALUES])
            ##if self.MaxCounter == 0: print "MAXCOUNTER == 0"
            
        elif self.SelectionMethod == IBISSelectionMethod.SM_WeightedRoundRobin:
            self.DataDic = self.AppsWithWeightsDic
            self.Counter = 0.0
            self.MaxCounter = int(self.DataDic[AIParseUtils.TOTAL_WEIGHT])
            
        
    def getNextValue(self):
        if self.SelectionMethod == IBISSelectionMethod.SM_Random:
            return self.RandomGenerator.getRandomListElement( self.DataList )
        elif self.SelectionMethod == IBISSelectionMethod.SM_WeightedRandom:
            return AIRandomUtils.getRandomWeightedListElement(
                       self.DataDic,
                       ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                    )
        elif self.SelectionMethod == IBISSelectionMethod.SM_RoundRobin:
            if self.Counter >= self.MaxCounter: self.Counter = 0
            try:
                ReturnValue = self.DataDic[AIParseUtils.VALUES][self.Counter][0]
            except IndexError, e:
                print '>>>>>>>>>', e
                print '>>TRACE>>', traceback.print_exc()
                print '>>CNTR>>>', self.Counter, "/", self.MaxCounter
            self.Counter = self.Counter + 1
            return ReturnValue
        elif self.SelectionMethod == IBISSelectionMethod.SM_WeightedRoundRobin:
            if self.Counter >= self.MaxCounter: self.Counter = 0.0
            Index = 0
            CurrentCounter = 0.0
            while CurrentCounter <= self.Counter:
                try:
                    ReturnValue = self.DataDic[AIParseUtils.VALUES][Index][0]
                except IndexError, e:
                    print '>>>>>>>>>', e
                    print '>>TRACE>>', traceback.print_exc()
                    print '>>CNTR>>>', self.Counter, "/", self.MaxCounter
                CurrentCounter = CurrentCounter + self.DataDic[AIParseUtils.VALUES][Index][1]
                Index = Index + 1
            
            self.Counter = self.Counter + 1.0
            return ReturnValue
            
        return None
    

def replaceDic( OriginalString, ReplaceDic ):
    try:
        import string
        t = string.Template(OriginalString)
        return str(t.substitute(ReplaceDic))
    except AttributeError, e:
        #print "IBIS generator: Submitter: Your Python version does not include string.Template (ver<2.4)",
        # TODO: create a ${} substitution function, to replace Python 2.4's !!!!
        ReplaceDic2 = {}
        for Key in ReplaceDic.keys():
            ReplaceDic2['${'+Key+'}'] = ReplaceDic[Key]
        replacer = EFFBotMultiReplace.MultiReplace(ReplaceDic2)
        return str(replacer.replace(OriginalString))
    except KeyError, e:
        #print "IBIS generator: ", e, "not found...replacing with default"
        raise KeyError, e
        
    raise Exception, "IBIS generator: cannot substitute " + str(ReplaceDic) + " in '" + OriginalString + "'"

def generateJobInfo( UnitDir, UnitID, JobIndex, JobType, WLUnit, SubmitDurationMS, Submitter ):
    global IBIS_LastRunTime
    """ 
    Out:
        A dictionary having at least the keys:
        'name', 'description', 'jdf', 'submitCommand', 'runTime'
        
    See also:
        utils/WLDocHandlers.WLSubmitJobKeys
    """
    InfoDic = {}
    OverallJobType = WLUnit['apptype']
    InfoDic['id'] = "%s_%d_%s" % ( UnitID, JobIndex, JobType )
    InfoDic['name'] = "%s_%d_%s__sser" % ( UnitID, JobIndex, JobType )
    InfoDic['description'] = \
        "Workload unit %s, job %d; application type %s/%s." % \
                ( UnitID, JobIndex, OverallJobType, JobType )
    InfoDic['jdf'] = os.path.join( UnitDir, "wl-unit-%d-%s.jdf" % (JobIndex, UnitID) )
    
    try:
        SubmitInfoDic = {}
        SubmitInfoDic['JDF'] = InfoDic['jdf']
        InfoDic['submitCommand'] = replaceDic( Submitter, SubmitInfoDic)
    except KeyError, e:
        pass
    except:
        pass
    
    if 'submitCommand' not in InfoDic.keys():
        InfoDic['submitCommand'] = 'grunner -e -o -g -f %s' % ( InfoDic['jdf'] )
        print InfoDic['submitCommand']
        
    try:
        Name = WLUnit['arrivaltimeinfo'][0]
        ParamsList = WLUnit['arrivaltimeinfo'][1]
        RunTime = IBIS_LastRunTime + WLUnit['arrivaltimefunc']( Name, ParamsList )
        IBIS_LastRunTime = RunTime
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
    PreComponentsList, JavaHomeDir, IbisAppsDir, IbisLibDir, \
    JavaMaxMemoryLimitMB, Application, NCPUs):
    
    # minutes: 3, 15, 30, 700
    RunTimeInMinutesList = [ '3', '15', '30', '700' ]
    
    NumComponents = len(PreComponentsList)
    
    ComponentsList = []
    
    #--- generate wall time once for all components of this job
    MaxWallTime = AIRandomUtils.getRandomListElement( RunTimeInMinutesList )
    
    if UnitDir[0] != '/':
        if sys.platform.find("linux") >= 0:
            UnitDir = os.path.join( os.environ['PWD'], UnitDir )
        else:
            UnitDir = os.path.join( os.getcwd(), UnitDir )
        ### THE UGLY HACK: convert /disk1/home3/koala5/grenchmark to /home/koala5/grenchmark
        pos = UnitDir.find('/koala')
        if pos >= 0:
            UnitDir = '/home' + UnitDir[pos:]
            
    #-- IBIS workload definition
    ComponentDirName = "%d-%d" % ( JobIndex, NumComponents )
    FullComponentDirName = os.path.join( UnitDir, "%s/" % UnitID, ComponentDirName ) 
    #--- Create output directory, if it does not exist
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
            
    # support the directory stagein
    EmptyFileName = os.path.join( FullComponentDirName, "__empty_file__" )
    try:
        EmptyFile = open( EmptyFileName, "w" )
        EmptyFile.close()
    except:
        pass 
    
    
    AppJAR = IBIS_Apps[Application][IBISConsts.Archive]
    AppJARFullPath = os.path.join( IbisAppsDir, IBIS_Apps[Application][IBISConsts.Dir], 'build/', AppJAR )
    AppClassPath = ':'.join([ os.path.join(IbisLibDir, "build/ibis.jar"), 
                              os.path.join(IbisLibDir, "3rdparty/log4j-1.2.9.jar"),
                              AppJARFullPath ] )
                    
    #ParamsList StageIn StageOut MaxReqMemory Description 
    if Application not in IBIS_Apps.keys():
        raise Exception, 'IBIS generator: Application ' + Application + 'not known!'
        
    AppMemoryLimit = IBIS_Apps[Application][IBISConsts.MaxReqMemory]
        
    if JavaMaxMemoryLimitMB < AppMemoryLimit:
        print "WARNING! IBIS generator:", "Although the application specific JVM memory limit was", AppMemoryLimit, "the JavaMaxMemoryLimitMB field forced it to", JavaMaxMemoryLimitMB
        AppMemoryLimit = JavaMaxMemoryLimitMB
        
    #-- need the same parameters for all the data
    ParamsData = IBIS_Apps[Application][IBISConsts.ParamsList]
    if type(ParamsData) == list:
        ParamsData = AIRandomUtils.getRandomListElement( ParamsData )
    
    for PreComponent in PreComponentsList:
        #--- reset component data
        ComponentData = {}
        
        #--- generate component data
        ComponentData['id'] = "%s-%d-%2.2d" % ( UnitID, JobIndex, PreComponent['id'] )
        ComponentData['name']   = "%s_ibis" % ComponentData['id']
        ComponentData['location'] = PreComponent['location']
        ##ComponentData['jobtype'] = 'mpi'
        ComponentData['count'] = PreComponent['count']
        ComponentData['description'] = \
                    "Ibis Workload Job, Type=%s Count=%d, maxWallTime=%d" % \
                    (Application, ComponentData['count'], int(MaxWallTime) )
        ComponentData['directory'] = FullComponentDirName
        ComponentData['executable'] = os.path.join(JavaHomeDir,'bin/java')
        ComponentData['maxWallTime'] = MaxWallTime
        ComponentData['stdout'] = os.path.join( FullComponentDirName, "ibis"+ComponentData['id']+".out" )
        ComponentData['stderr'] = os.path.join( FullComponentDirName, "ibis"+ComponentData['id']+".err" )
        ComponentData['stagein'] = [ AppJARFullPath, os.path.join( FullComponentDirName, os.path.basename(EmptyFileName) ) ]
        ComponentData['arguments'] = [ 
            #"-Xbootclasspath/p:" + AppClassPath, # prepend the default bootstrap classpath 
            "-classpath", AppClassPath
            ]
        for IBISDef in IBIS_Defs:
            if IBISDef in WLUnit['otherinfo'].keys():
                try:
                    ReplaceDic = {}
                    ReplaceDic['JOB_ID'] = "%s-%d" % (UnitID, JobIndex)
                    ReplaceDic['NPROCS'] = "%s" % str(NCPUs)
                    Argument = replaceDic( WLUnit['otherinfo'][IBISDef], ReplaceDic )
                except KeyError, e:
                    print "KeyError!!!!!", e
                    continue
                except Exception, e:
                    print "UNKNOWN EXCEPTION ", e
                    continue
                ComponentData['arguments'].append( "-D" + IBISDef + "=" + Argument )
                
        ComponentData['arguments'].append( "-Xmx" + str(AppMemoryLimit) + 'M' ) # maximum size of the memory allocation pool
        ComponentData['arguments'].append( IBIS_Apps[Application][IBISConsts.Executable] )
        #ComponentData['arguments'].append( IBIS_Apps[Application][IBISConsts.ParamsList] )
        for Parameter in ParamsData.split(' '):
            ComponentData['arguments'].append( Parameter )

        
        ComponentData['env'] = [ 
            ("GLOBUS_DUROC_SUBJOB_INDEX", "%d" % PreComponent['id']),
            ("LD_LIBRARY_PATH", "/usr/local/globus/globus-3.2/lib/"),
            ("IBIS_HOME", IbisLibDir)  
            ]
        ComponentData['label'] = "subjob %d" % PreComponent['id']
        
        #--- add component to the job
        ComponentsList.append( ComponentData )
        
    return ComponentsList 



def generateWorkload( UnitDir, UnitID, WLUnit, SubmitDurationMS, bGenerateRandom = 1 ):
    global IBIS_LastRunTime
    #print WLUnit['otherinfo']
    #{'RandomWorkload': 'true', 'NComponents': '1-8', 'NJobs': '50', 'ComponentSize':'4-8'}
    
    if bGenerateRandom > 0:
        print "Random workload"
    else:
        print "Full workload"
    
    if 'otherinfo' in WLUnit.keys():
        
        try:
            ##print ">>>>>> NJobs" 
            NJobs = AIParseUtils.readInt(WLUnit['otherinfo']['NJobs'], DefaultValue = 0)
        except KeyError:
            NJobs = 0
            if bGenerateRandom > 0: #-- NJobs required if random, optional otherwise
                raise Exception, "IBIS generator: No NJobs info specified in the OtherInfo field."
        
        try:
            NComponentsWithWeightsDic = \
                AIParseUtils.readIntWithWeightsList( 
                    WLUnit['otherinfo']['NComponentsWithWeights'], 
                    DefaultWeight = 1.0 
                    )
            # NComponentsWithWeightsDic['Values']; NComponentsWithWeightsDic['TotalWeight']
        except KeyError:
            raise Exception, "IBIS generator: Invalid NComponentsWithWeights info specified in the OtherInfo field."
        ##print ">>>>>> NComponentsWithWeightsDic", NComponentsWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
        try:
            TotalCPUsWithWeightsDic = \
                AIParseUtils.readIntWithWeightsList( 
                    WLUnit['otherinfo']['TotalCPUsWithWeights'], 
                    DefaultWeight = 1.0 
                    )
        except KeyError:
            raise Exception, "IBIS generator: Invalid TotalCPUsWithWeights info specified in the OtherInfo field."
        ##print ">>>>>> TotalCPUsWithWeightsDic", TotalCPUsWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
        
        try:
            MinComponentSize = AIParseUtils.readInt(WLUnit['otherinfo']['MinComponentSize'], DefaultValue = 0)
        except KeyError:
            MinComponentSize = 1
            #raise Exception, "IBIS generator: No MinComponentSize info specified in the OtherInfo field."
            
        try:
            MaxComponentSize = AIParseUtils.readInt(WLUnit['otherinfo']['MaxComponentSize'], DefaultValue = 0)
        except KeyError:
            MaxComponentSize = 10000000
            #raise Exception, "IBIS generator: No MaxComponentSize info specified in the OtherInfo field."
        
        try:
            EqualCPUsPerComponent = AIParseUtils.readBoolean(WLUnit['otherinfo']['IbisAppsDir'])
        except KeyError:
            EqualCPUsPerComponent = 0
            #raise Exception, "IBIS generator: No EqualCPUsPerComponent info specified in the OtherInfo field. Setting to default " + AIParseUtils.IntToBooleanDic[EqualCPUsPerComponent] + '.'
        
        try:
            IbisAppsDir = WLUnit['otherinfo']['IbisAppsDir']
        except KeyError:
            raise Exception, "IBIS generator: No IbisAppsDir info specified in the OtherInfo field."
            
        try:
            IbisLibDir = WLUnit['otherinfo']['IbisLibDir']
        except KeyError:
            raise Exception, "IBIS generator: No IbisLibDir info specified in the OtherInfo field."
            
        try:
            JavaHomeDir = WLUnit['otherinfo']['JavaHomeDir']
        except KeyError:
            raise Exception, "IBIS generator: No JavaHomeDir info specified in the OtherInfo field."
        
        try:
            AppsWithWeightsDic = \
                AIParseUtils.readStringWithWeightsList( 
                    WLUnit['otherinfo']['AppsWithWeights'], 
                    DefaultWeight = 1.0 
                    )
        except KeyError:
            raise Exception, "IBIS generator: Invalid AppsWithWeights info specified in the OtherInfo field."
        ###print ">>>>>> AppsWithWeightsDic", AppsWithWeightsDic#[AIParseUtils.TOTAL_WEIGHT]
        
        try:
            Submitter = WLUnit['otherinfo']['Submitter']
        except KeyError:
            Submitter = 'grunner'
            print "WARNING! IBIS generator: No Submitter info specified in the OtherInfo field.\n\tSetting to default", Submitter
            
        try:
            SiteTypesWithWeightsDic = \
                AIParseUtils.readStringWithWeightsList( 
                    WLUnit['otherinfo']['SiteTypesWithWeights'], 
                    DefaultWeight = 1.0 
                    )
        except KeyError:
            SiteTypesWithWeights = {AIParseUtils.VALUES:[], AIParseUtils.TOTAL_WEIGHT:0.0 }
            print "WARNING! IBIS generator: No SiteTypesWithWeights info specified in the OtherInfo field.\n\tSetting to default", SitesList
        ##print ">>>>>> SiteTypesWithWeightsDic", SiteTypesWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
        try:
            SitesWithWeightsDic = \
                AIParseUtils.readStringWithWeightsList( 
                    WLUnit['otherinfo']['SitesWithWeights'], 
                    DefaultWeight = 1.0 
                    )
        except KeyError:
            SitesWithWeightsDic = {AIParseUtils.VALUES:[], AIParseUtils.TOTAL_WEIGHT:0.0 }
            print "WARNING! IBIS generator: No SitesWithWeights info specified in the OtherInfo field.\n\tSetting to default", SitesList
        ##print ">>>>>> SitesWithWeightsDic", SitesWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
        try:    
            JavaMaxMemoryLimitMB = AIParseUtils.readInt(WLUnit['otherinfo']['JavaMaxMemoryLimitMB'], 10000)
        except KeyError:
            JavaMaxMemoryLimitMB = 10000
            print "WARNING! IBIS generator: No JavaMaxMemoryLimitMB info specified in the OtherInfo field.\n\tSetting to default", JavaMaxMemoryLimitMB, "MB"
        
        try:
            SelectionMethodName = WLUnit['otherinfo']['SelectionMethod']
        except KeyError:
            SelectionMethodName = 'R'
            raise Exception, "IBIS generator: No SelectionMethod info specified in the OtherInfo field."
            
    else:
        raise Exception, "IBIS generator: No OtherInfo data! Expected at least ComponentSize,NJobs,NComponents fields."
    
    UnitsDic = {}
    UnitsDic['info'] = {}
    UnitsDic['jobs'] = {}
    
    #-- init start time
    try:
        StartAt = AIParseUtils.readInt(WLUnit['otherinfo']['StartAt'], DefaultValue = 0)
        StartAt = StartAt * 1000 # the time is given is seconds
    except KeyError:
        StartAt = 0
    IBIS_LastRunTime = StartAt
    
    WLUnitMultiplicity = int(WLUnit['multiplicity'])
    if bGenerateRandom > 0:
        #--- generate random
        
        OneIBISSelectionMethod = IBISSelectionMethod( AppsWithWeightsDic )
        OneIBISSelectionMethod.setSelectionMethodByName( SelectionMethodName )
        
        JobIndex = 0
        if WLUnitMultiplicity > 1:
            NJobs = NJobs * WLUnitMultiplicity
        while JobIndex < NJobs:
            # 1. select application type
##            Application = AIRandomUtils.getRandomWeightedListElement(
##                       AppsWithWeightsDic,
##                       ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
##                    )
            Application = OneIBISSelectionMethod.getNextValue()
            if Application.find('*') >= 0:
                print "IBIS generator: Expanded", Application, "to", 
                Application = ExpandApplication(Application)
                print Application
            
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
                
                SiteType = AIRandomUtils.getRandomWeightedListElement(
                                    SiteTypesWithWeightsDic,
                                    ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                                    )
                
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
            #-- generate rnd job: ID
            CurrentUnitID = "%s-%d" % (UnitID, JobIndex % WLUnitMultiplicity)
            #-- generate rnd job: index
            UnitsDic['info'][JobIndex] = \
                        generateJobInfo( UnitDir, CurrentUnitID, JobIndex, Application, \
                                         WLUnit, SubmitDurationMS, Submitter )
            #-- generate rnd job: components
            UnitsDic['jobs'][JobIndex] = \
                        generateJobComponents( 
                            UnitDir, CurrentUnitID, JobIndex, WLUnit, 
                            PreComponentsList, JavaHomeDir, IbisAppsDir, IbisLibDir, 
                            JavaMaxMemoryLimitMB, Application, NCPUs
                            )
            #-- be more descriptive
            UnitsDic['info'][JobIndex]['description'] = \
                UnitsDic['info'][JobIndex]['description'] + \
                " Components: %d. NCPUs: %d." % (len(PreComponentsList), NCPUs) 
                            
            #--- done generating
            if UnitsDic['jobs'][JobIndex] == None:
                NJobs = NJobs - 1 #-- don't ack job, but make sure total no of jobs is decreased
            else:
                
                print "IBIS generator: Generated a job of type", Application, 
                print "with", len(PreComponentsList), "components/", 
                print NCPUs, "CPUs, in", UnitsDic['info'][JobIndex]['jdf']
                
                JobIndex = JobIndex + 1 #-- ack job 
                
                
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
                                               NumComponents, ComponentSize, Application, NCPUs )
                    JobIndex = JobIndex + 1
            RepetitionIndex = RepetitionIndex + 1
            
            if JobIndex > NJobs and NJobs > 0:
                print "Generated %d jobs and stopped because of the NJobs limit."
                break
            
        WLUnit['generatedjobs'] = JobIndex
        
    #raise Exception, "IBIS generator: Not implemented yet"
    return UnitsDic


    
if __name__ == "__main__":
    print "ibis-workload"
    pass
    
