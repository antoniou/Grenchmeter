WLGenerator="""
    Name=swf
    Info=Workload based on the Standard Workloads Format (Parallel Workloads Archive)
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
 
class SWFConsts:
    JobNumber = 0
    SubmitTime = 1
    WaitTime = 2
    RunTime = 3
    NCPUs = 4
    AvgCPUTime = 5
    UsedMem = 6
    ReqNCPUs = 7
    ReqTime = 8
    ReqMem = 9
    Status = 10
    UserID = 11
    GroupID = 12
    ApplicationID = 13
    QNo = 14
    PartitionNo = 15
    PrecedingJobNo = 16
    ThinkTime = 17
    def getID(self,name):
        if name in SWFConsts.__dict__:
            return SWFConsts.__dict__[name]
        else:
            return None
            
##>>> xxx  =  X()
##>>> print xxx.get('a')
##1
##>>> print xxx.get('b')
##2
##>>> xxx.c = 3
##>>> xxx.a = 3111
##>>> print xxx.get('a')
##1
##>>> print xxx.get('b')
##2
##>>> print xxx.get('c')
##None
            
class SWFFilter:
    Min = 0
    Max = 1
    Equals = 2
    
    def apply(self, FilterName, FilterValue, CurrentValue):
        """ return 1 if the CurrentValue passes the filter, 0 otherwise """
        FilterID = None
        ##print type(FilterName)
        if type(FilterName) == str:
            if FilterName in SWFFilter.__dict__:
                FilterID = SWFFilter.__dict__[FilterName]
        else:
            FilterID = FilterName
                
        if FilterID == None:
            raise Exception, "swf-wl.py::SWFFilter: Filter " + str(FilterName) + " not found!"
            
        ##print "Filter", FilterName, "identified as", FilterID
        ##print type(CurrentValue), type(FilterValue)
                
        if FilterID == SWFFilter.Min:
            if CurrentValue >= FilterValue:
                ##print CurrentValue, ">=", FilterValue, '-> true'
                return 1
            else:
                ##print CurrentValue, ">=", FilterValue, '-> false'
                return 0
        elif FilterID == SWFFilter.Max:
            if CurrentValue <= FilterValue:
                ##print CurrentValue, "<=", FilterValue, '-> true'
                return 1
            else:
                ##print CurrentValue, "<=", FilterValue, '-> false'
                return 0
        elif FilterID == SWFFilter.Equals:
            if CurrentValue == FilterValue:
                ##print CurrentValue, "==", FilterValue, '-> true'
                return 1
            else:
                ##print CurrentValue, "==", FilterValue, '-> false'
                return 0
        return 1 ### default filter: pass all

class SWFOnlyParams:
    def __init__(self):
        self.File = None
        self.Filters = {}
        self.Scale = {}
    
class SWFParams:
    pass
    
SWF_LastRunTime = 0
SWF_UseOriginalTime = 1
 
class SWFSelectionMethod:
    
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
        
    raise Exception, "SWF generator: cannot substitute " + str(ReplaceDic) + " in '" + OriginalString + "'"

def generateJobInfo( UnitDir, UnitID, JobIndex, JobType, WLUnit, SubmitDurationMS, Submitter, \
                     UseArrivalTimeDistribution = 1, JobStartTime = None ):
    global SWF_LastRunTime
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
    InfoDic['name'] = "%s_%d_%s" % ( UnitID, JobIndex, JobType )
    InfoDic['description'] = \
        "Workload unit %s, job %d; application type %s/%s." % \
                ( UnitID, JobIndex, OverallJobType, JobType )
    InfoDic['jdf'] = os.path.join( UnitDir, "wl-unit-%s-%d.jdf" % (UnitID, JobIndex) )
    
    try:
        SubmitInfoDic = {}
        SubmitInfoDic['JDF'] = InfoDic['jdf']
        InfoDic['submitCommand'] = replaceDic( Submitter, SubmitInfoDic)
    except KeyError, e:
        pass
    except:
        pass
    
    if 'submitCommand' not in InfoDic.keys():
        InfoDic['submitCommand'] = 'krunner -e -o -g -f %s' % ( InfoDic['jdf'] )
        print InfoDic['submitCommand']
        
    if UseArrivalTimeDistribution == 1:
        try:
            Name = WLUnit['arrivaltimeinfo'][0]
            ParamsList = WLUnit['arrivaltimeinfo'][1]
            RunTime = SWF_LastRunTime + WLUnit['arrivaltimefunc']( Name, ParamsList )
            if RunTime < 0.0: RunTime = 0.0
            SWF_LastRunTime = RunTime
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
    else:
        SWFConstsInstace = SWFConsts()
        RunTime = JobStartTime
        if RunTime < 0.0: RunTime = 0.0
        SWF_LastRunTime = RunTime
        if float(RunTime) > SubmitDurationMS:
            InfoDic['runTime'] = str(AIRandomUtils.getRandomInt(0, SubmitDurationMS))
        else:
            InfoDic['runTime'] = str(RunTime)
        
    return InfoDic

def generateJobComponents( UnitDir, UnitID, JobIndex, WLUnit, \
                           PreComponentsList, ApplicationBinaryFullPath, \
                           NCPUs, Job, MaxWallTimeInMinutes ):
    
    NumComponents = len(PreComponentsList)
    
    ComponentsList = []
    
    #--- generate wall time once for all components of this job
    SWFConstsInstace = SWFConsts()
    
    MaxWallTime = Job[SWFConstsInstace.ReqTime]
    MaxWallTime = MaxWallTime / 60 # get time in minutes, from seconds
    if MaxWallTime > MaxWallTimeInMinutes:
        MaxWallTime = MaxWallTimeInMinutes
    
    if Job[SWFConstsInstace.AvgCPUTime] > 0:
        if Job[SWFConstsInstace.RunTime] == 0:
            RunTime = Job[SWFConstsInstace.AvgCPUTime]
        else:
            RunTime = int(Job[SWFConstsInstace.RunTime] / Job[SWFConstsInstace.NCPUs])
    else:
        RunTime = Job[SWFConstsInstace.RunTime]
    
    if RunTime > MaxWallTime * 60:
        RunTime = MaxWallTime * 60
    if RunTime > 10:
        RunTime = RunTime - 10
    
    if UnitDir[0] != '/':
        if sys.platform.find("linux") >= 0:
            UnitDir = os.path.join( os.environ['PWD'], UnitDir )
        else:
            UnitDir = os.path.join( os.getcwd(), UnitDir )
        ### THE UGLY HACK: convert /disk1/home3/koala5/grenchmark to /home/koala5/grenchmark
        pos = UnitDir.find('/koala')
        if pos >= 0:
            UnitDir = '/home' + UnitDir[pos:]
            
    #-- SWF workload definition
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
                    "SWF Job, Count=%d, maxWallTime=%d" % \
                    (ComponentData['count'], int(MaxWallTime) )
        ComponentData['directory'] = FullComponentDirName
        ComponentData['executable'] = ApplicationBinaryFullPath
        ComponentData['maxWallTime'] = MaxWallTime
        ComponentData['stdout'] = os.path.join( FullComponentDirName, "swf"+ComponentData['id']+".out" )
        ComponentData['stderr'] = os.path.join( FullComponentDirName, "swf"+ComponentData['id']+".err" )
        ComponentData['stagein'] = [ os.path.join( FullComponentDirName, os.path.basename(EmptyFileName) ) ]
        
        ComponentData['arguments'] = [ 
            "-m", Job[SWFConstsInstace.UsedMem], "-t", RunTime
            ]
        ComponentData['env'] = [ 
            ("GLOBUS_DUROC_SUBJOB_INDEX", "%d" % PreComponent['id']),
            ("LD_LIBRARY_PATH", "/usr/local/globus/globus-3.2/lib/")
            ]
        ComponentData['label'] = "subjob %d" % PreComponent['id']
        
        #--- add component to the job
        ComponentsList.append( ComponentData )
        
    return ComponentsList 


def readParams( ParamsDic ):
    """ read params, return a SWFParams class, with new fields """
    
    CurrentSWFParams = SWFParams()
    CurrentSWFParams.SWF = SWFOnlyParams()
    
    if 'otherinfo' in ParamsDic.keys():
        
        SWFConstsInstance = SWFConsts()
        try:
            for key in ParamsDic['otherinfo']:
                OneList = key.split('.')
                if OneList[0] == 'SWF':
                    if OneList[1] == 'File':
                        CurrentSWFParams.SWF.File = ParamsDic['otherinfo'][key]
                    elif OneList[1] == 'Scale': # SWF.Scale.SubmitTime=1:1
                        KeyID = SWFConstsInstance.getID(OneList[2])
                        if (KeyID is not None) and (KeyID >= 0):
                            # save: ['SubmitTime']: (1,1)
                            ScaleIn, ScaleOut = ParamsDic['otherinfo'][key].split(':')
                            ScaleIn = float(ScaleIn)
                            ScaleOut = float(ScaleOut)
                            CurrentSWFParams.SWF.Scale[OneList[2]] = (ScaleIn, ScaleOut)
                    elif OneList[1] == 'Filter':
                        KeyID = SWFConstsInstance.getID(OneList[2])
                        ##print 'Filter', OneList[2], "KeyID=", KeyID
                        if (KeyID is not None) and (KeyID >= 0):
                            #SWF.Filter.JobNumber.Min=31
                            # save: ['JobNumber']: ('Min',31)
                            if OneList[2] not in CurrentSWFParams.SWF.Filters:
                                CurrentSWFParams.SWF.Filters[OneList[2]] = []
                            CurrentSWFParams.SWF.Filters[OneList[2]].append((OneList[3], int(ParamsDic['otherinfo'][key])))
                        else:
                            # special cases
                            ##print "Special case filter", OneList[2]
                            
                            # SWF.Filter.Delta.SubmitTime.Hours.Max=3
                            # save: ['Delta']['SubmitTime']['Hours']('Max',31)
                            if OneList[2] == 'Delta':
                                if 'Delta' not in CurrentSWFParams.SWF.Filters:
                                    CurrentSWFParams.SWF.Filters['Delta'] = {}
                                KeyID = SWFConstsInstance.getID(OneList[3])
                                if KeyID and KeyID >= 0:
                                    if OneList[3] not in CurrentSWFParams.SWF.Filters['Delta']:
                                        CurrentSWFParams.SWF.Filters['Delta'][OneList[3]] = {}
                                    CurrentSWFParams.SWF.Filters['Delta'][OneList[3]][OneList[4]] = (OneList[5], int(ParamsDic['otherinfo'][key]))
                                    
                            # SWF.Filter.NJobs.Max=1000
                            # save: ['NJobs']: ('Max',1000)
                            if OneList[2] == 'NJobs':
                                CurrentSWFParams.SWF.Filters['NJobs'] = (OneList[3], int(ParamsDic['otherinfo'][key]))
        except Exception, e:
            print "Exception", e
            print traceback.print_exc()
            raise Exception, "SWF generator: could not decode " + str(key) + '.'
            
        if CurrentSWFParams.SWF.File is None:
            raise Exception, "SWF generator: No SWF.File field in OtherInfo (cannot read an unknown file)."
            
        # UseArrivalTimeDistribution=false
        try:
            CurrentSWFParams.UseArrivalTimeDistribution = AIParseUtils.readBoolean(ParamsDic['otherinfo']['UseArrivalTimeDistribution'])
        except KeyError:
            CurrentSWFParams.UseArrivalTimeDistribution = 0
            
        #Application=swf
        #AppBaseDir=/tmp
        try:
            CurrentSWFParams.AppBaseDir = ParamsDic['otherinfo']['AppBaseDir']
        except KeyError:
            CurrentSWFParams.AppBaseDir = '/tmp'
            #raise Exception, "SMPI1 generator: No AppBaseDir info specified in the OtherInfo field."
            print "WARNING! SWF generator: No AppBaseDir info specified in the OtherInfo field.", "Assuming default:", AppBaseDir
            
        try:
            CurrentSWFParams.Application = ParamsDic['otherinfo']['Application']
        except KeyError:
            CurrentSWFParams.Application = 'swf'
            #raise Exception, "SMPI1 generator: No AppBaseDir info specified in the OtherInfo field."
            print "WARNING! SWF generator: No Application info specified in the OtherInfo field.", "Assuming default:", Application
            
        try:
            CurrentSWFParams.Submitter = ParamsDic['otherinfo']['Submitter']
        except KeyError:
            CurrentSWFParams.Submitter = 'krunner -l DEBUG -g -e -o -f ${JDF}'
            print "WARNING! SWF generator: No Submitter info specified in the OtherInfo field.", "Assuming default", Submitter
        
        try:
            CurrentSWFParams.NComponentsWithWeightsDic = \
                AIParseUtils.readIntWithWeightsList( 
                    ParamsDic['otherinfo']['NComponentsWithWeights'], 
                    DefaultWeight = 1.0 
                    )
            # NComponentsWithWeightsDic['Values']; NComponentsWithWeightsDic['TotalWeight']
        except KeyError:
            raise Exception, "SWF generator: Invalid NComponentsWithWeights info specified in the OtherInfo field."
        ##print ">>>>>> NComponentsWithWeightsDic", NComponentsWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
        try:
            CurrentSWFParams.MinComponentSize = AIParseUtils.readInt(ParamsDic['otherinfo']['MinComponentSize'], DefaultValue = 0)
        except KeyError:
            CurrentSWFParams.MinComponentSize = 1
            print "WARNING! SWF generator: No MinComponentSize info specified in the OtherInfo field.", "Assuming default", CurrentSWFParams.MinComponentSize
            #raise Exception, "SWF generator: No MinComponentSize info specified in the OtherInfo field."
        
        try:
            CurrentSWFParams.DelayBetweenUnits = AIParseUtils.readInt(ParamsDic['otherinfo']['DelayBetweenUnits'], DefaultValue = 0)
        except KeyError:
            CurrentSWFParams.DelayBetweenUnits = 1
            print "WARNING! SWF generator: No DelayBetweenUnits info specified in the OtherInfo field.", "Assuming default", CurrentSWFParams.DelayBetweenUnits
            
        try:
            CurrentSWFParams.MaxWallTime = AIParseUtils.readInt(ParamsDic['otherinfo']['MaxWallTime'], DefaultValue = 1000000)
        except KeyError:
            CurrentSWFParams.MaxWallTime = 1
            print "WARNING! SWF generator: No DelayBetweenUnits info specified in the OtherInfo field.", "Assuming default", CurrentSWFParams.MaxWallTime
            
        try:
            CurrentSWFParams.MaxComponentSize = AIParseUtils.readInt(ParamsDic['otherinfo']['MaxComponentSize'], DefaultValue = 0)
        except KeyError:
            CurrentSWFParams.MaxComponentSize = 10000000
            print "WARNING! SWF generator: No MaxComponentSize info specified in the OtherInfo field.", "Assuming default", CurrentSWFParams.MaxComponentSize
            #raise Exception, "SWF generator: No MaxComponentSize info specified in the OtherInfo field."
        
        try:
            CurrentSWFParams.EqualCPUsPerComponent = AIParseUtils.readBoolean(ParamsDic['otherinfo']['SWFAppsDir'])
        except KeyError:
            CurrentSWFParams.EqualCPUsPerComponent = 0
            #raise Exception, "SWF generator: No EqualCPUsPerComponent info specified in the OtherInfo field. Setting to default " + AIParseUtils.IntToBooleanDic[EqualCPUsPerComponent] + '.'
            
        try:
            CurrentSWFParams.SiteTypesWithWeightsDic = \
                AIParseUtils.readStringWithWeightsList( 
                    ParamsDic['otherinfo']['SiteTypesWithWeights'], 
                    DefaultWeight = 1.0 
                    )
        except KeyError:
            CurrentSWFParams.SiteTypesWithWeights = {AIParseUtils.VALUES:[], AIParseUtils.TOTAL_WEIGHT:0.0 }
            print "WARNING! SWF generator: No SiteTypesWithWeights info specified in the OtherInfo field.\n\tSetting to default..."
        ##print ">>>>>> SiteTypesWithWeightsDic", SiteTypesWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
        try:
            CurrentSWFParams.SitesWithWeightsDic = \
                AIParseUtils.readStringWithWeightsList( 
                    ParamsDic['otherinfo']['SitesWithWeights'], 
                    DefaultWeight = 1.0 
                    )
        except KeyError:
            CurrentSWFParams.SitesWithWeightsDic = {AIParseUtils.VALUES:[], AIParseUtils.TOTAL_WEIGHT:0.0 }
            print "WARNING! SWF generator: No SitesWithWeights info specified in the OtherInfo field.\n\tSetting to default..."
        ##print ">>>>>> SitesWithWeightsDic", SitesWithWeightsDic[AIParseUtils.TOTAL_WEIGHT]
        
##        try:
##            CurrentSWFParams.SelectionMethodName = ParamsDic['otherinfo']['SelectionMethod']
##        except KeyError:
##            CurrentSWFParams.SelectionMethodName = 'R'
##            raise Exception, "SWF generator: No SelectionMethod info specified in the OtherInfo field."
            
    else:
        raise Exception, "SWF generator: No OtherInfo data! Expected at least ComponentSize,NJobs,NComponents fields."
    
    return CurrentSWFParams
    
def readSWFFile( InFileName, Params ):
    """ read the given input file (in SWF format) and return a filtered and scaled list of jobs """
    
    # the data format is one line per job, with 18 fields:
    #  0 - Job Number
    #  1 - Submit Time
    #  2 - Wait Time
    #  3 - Run Time
    #  4 - Number of Processors
    #  5 - Average CPU Time Used
    #  6 - Used Memory
    #  7 - Requested Number of Processors
    #  8 - Requested Time
    #  9 - Requested Memory
    # 10 - status (1=completed, 0=killed)
    # 11 - User ID
    # 12 - Group ID
    # 13 - Executable (Application) Number
    # 14 - Queue Number
    # 15 - Partition Number
    # 16 - Preceding Job Number
    # 17 - Think Time from Preceding Job
    #    
    
    JobsList = []
    UNIXStartTime = 0
    QuitReadingLines = 0
    FirstJob = None
    
    SWFConstsInstance = SWFConsts()
    
    InFile = open( InFileName ) 
    while 1:
        
        if QuitReadingLines == 1:
            print "Exiting lines while"
            break
        
        lines = InFile.readlines(100000) ## 100KB buffer
        if not lines:
            break
        #-- process lines
        for line in lines: 
            
            if QuitReadingLines == 1:
                print "Exiting lines for"
                break
                
            if (len(line) > 0):
                if line[0] == ';': 
                    # ; UnixStartTime: 1041550561 
                    try:
                        code, value = line[1:].split(':')
                        if code.strip() == 'UnixStartTime':
                            try:
                                intval,restval = value.split('#', 1)
                            except:
                                intval = value
                            UNIXStartTime = UNIXStartTime + int(intval)
                        elif code.strip() == 'TimeZone':
                            try:
                                intval,restval = value.split('#', 1)
                            except:
                                intval = value
                            UNIXStartTime = UNIXStartTime + int(intval)
                    except:
                        pass
                        
                else:
                    # normal line
                    try:
                        # split line
                        JobNumber, SubmitTime, WaitTime, RunTime, \
                        NCPUs, AvgCPUTime, UsedMem, ReqNCPUs, ReqTime, \
                        ReqMem, Status, UserID, GroupID, ApplicationID, \
                        QNo, PartitionNo, PrecedingJobNo, ThinkTime = line.split()
                        
                        # convert interesting values to INTs
                        JobNumber = int(JobNumber)
                        SubmitTime = int(SubmitTime)
                        RunTime = int(RunTime)
                        NCPUs = int(NCPUs)
                        AvgCPUTime = int(AvgCPUTime)
                        UsedMem = int(UsedMem)
                        ReqNCPUs = int(ReqNCPUs)
                        ReqTime = int(ReqTime)
                        Status = int(Status)
                        
                        # eliminate flurries !!!
                        # e.g., SDSC'96 has job 38719 with SubmitTime = -1 [!]
                        if (JobNumber < 0) or \
                           (RunTime < 0 and AvgCPUTime < 0) or (SubmitTime < 0) or \
                           (NCPUs < 0 and ReqNCPUs < 0):
                            continue
                        
                        # create job tuple
                        Job = [ JobNumber, SubmitTime, WaitTime, RunTime,
                                NCPUs, AvgCPUTime, UsedMem, ReqNCPUs, ReqTime,
                                ReqMem, Status, UserID, GroupID, ApplicationID,
                                QNo, PartitionNo, PrecedingJobNo, ThinkTime ]
                                
                        # scale the job, *before* filtering
                        for key in Params.SWF.Scale:
                            KeyID = SWFConstsInstance.getID(key)
                            ScaleIn, ScaleOut = Params.SWF.Scale[key]
                            Job[KeyID] = int( Job[KeyID] * ScaleIn / ScaleOut )
                              
                        # filter the job
                        AnyFailed = 0
                        OneFilter = SWFFilter()
                        for key in Params.SWF.Filters:
                            KeyID = SWFConstsInstance.getID(key)
                            if (KeyID is not None) and (KeyID >= 0):
                                for SubFilter in Params.SWF.Filters[key]:
                                    FilterType, FilterValue = SubFilter
                                    JobOk = OneFilter.apply( FilterType, FilterValue, Job[KeyID] )
                                    if JobOk == 0:
                                        AnyFailed = 1
                                    if AnyFailed == 1: break
##                                        print "Filter", FilterType, "("+str(FilterValue)+")", \
##                                              "applied on JobNo", JobNumber, "["+key+"]", \
##                                              "("+str(Job[KeyID])+")", "result:", JobOk
                            else:
                                # special cases
                                # save: ['Delta']['SubmitTime']['Hours']('Max',31)
                                if key == 'Delta':
                                    if FirstJob is not None:
                                        for subkey in Params.SWF.Filters['Delta']:
                                            SubKeyID = SWFConstsInstance.getID(subkey)
                                            for subsubkey in Params.SWF.Filters['Delta'][subkey]:
                                                Multiplier = 1
                                                if subsubkey == 'Hours':
                                                    Multiplier = 3600
                                                elif subsubkey == 'Minutes':
                                                    Multiplier = 60
                                                FilterType, FilterValue = Params.SWF.Filters['Delta'][subkey][subsubkey]
                                                FilterValue = FilterValue * Multiplier
                                                JobOk = OneFilter.apply( FilterType, FilterValue, Job[SubKeyID] - FirstJob[SubKeyID] )
                                                if JobOk == 0: 
                                                    AnyFailed = 1
##                                                    print "DeltaFilter", FilterType, "("+str(FilterValue)+")", \
##                                                          "applied on JobNo", JobNumber, "["+key+"]", \
##                                                          "("+str(Job[SubKeyID] - FirstJob[SubKeyID])+")", "failed"
                                                if AnyFailed == 1: break
                                            if AnyFailed == 1: break
                            if AnyFailed == 1: break
                                
                        # add job, if not filtered out
                        if AnyFailed == 0:
                            
                            # make the job a tuple, while preserving field order
                            Job = tuple([Job[id] for id in xrange(len(Job))]) 
                            JobsList.append( Job )
                            
                            if FirstJob is None:
                                FirstJob = Job
                                ##print "FirstJob", FirstJob
                                
                            if 'NJobs' in Params.SWF.Filters:
                                FilterType, FilterValue = Params.SWF.Filters['NJobs']
                                if FilterType == 'Max' and len(JobsList) == FilterValue:
                                    QuitReadingLines = 1
                        else:
                            if 'JobNumber' in Params.SWF.Filters:
                                for SubFilter in Params.SWF.Filters['JobNumber']:
                                    FilterType, FilterValue = SubFilter
                                    if (FilterType == 'Max') and (JobNumber > FilterValue):
                                        # went past the last acceptable job number
                                        QuitReadingLines = 1
                                        print "Went past the last acceptable job number"
                                
                    except Exception, e:
                        print e
                        print traceback.print_exc()
                        
            
    if 'NJobs' in Params.SWF.Filters:
        FilterType, FilterValue = Params.SWF.Filters['NJobs']
        if FilterType == 'Min' and len(JobsList) < FilterValue: # not enough jobs -> no jobs
            JobsList = []
            UNIXStartTime = 0  
            
    print "Last parsed job number:", JobNumber
                
    return (JobsList, UNIXStartTime)
    

def generateWorkload( UnitDir, UnitID, WLUnit, SubmitDurationMS, bGenerateRandom = 1 ):
    global SWF_LastRunTime
    
    SWFConstsInstance = SWFConsts()
    CurrentSWFParams = readParams( WLUnit )
    
    for Filter in CurrentSWFParams.SWF.Filters:
        print 'Filter', Filter, '->', CurrentSWFParams.SWF.Filters[Filter]
    
    JobsList, UNIXStartTime = readSWFFile( CurrentSWFParams.SWF.File, CurrentSWFParams )
    
    print "After filtering out,", len(JobsList), "jobs remained."
    ##for Job in JobsList:
    ##    print Job
    
    UnitsDic = {}
    UnitsDic['info'] = {}
    UnitsDic['jobs'] = {}
    
    #-- init start time
    try:
        StartAt = AIParseUtils.readInt(WLUnit['otherinfo']['StartAt'], DefaultValue = 0)
        StartAt = StartAt * 1000 # the time is given is seconds
    except KeyError:
        StartAt = 0
    SWF_LastRunTime = StartAt
    
    WLUnitMultiplicity = int(WLUnit['multiplicity'])
    
    FirstJob = None
    JobIndex = 0
    NJobsInList = len(JobsList)
    for GroupID in xrange(WLUnitMultiplicity):
        for JobID in xrange(NJobsInList):
            #JobIndex = JobID + GroupID * NJobsInList
            
            #--- get trace data
            Job = JobsList[JobID]
            ##print Job
            if FirstJob is None:
                FirstJob = Job
            
            # 2. select the number of CPU for this job
            #TODO: repeat NCPUs selection until App can run on that many CPUs
            NCPUs = Job[SWFConstsInstance.NCPUs]
            # 3. select the number of components and try to create subcomponents,
            #    until successfully matching restrictions
            WhileCondition = 1
            NTries = 250
            while WhileCondition != 0 and NTries > 0:
                
                NTries = NTries - 1
                
                NComponents = AIRandomUtils.getRandomWeightedListElement(
                                    CurrentSWFParams.NComponentsWithWeightsDic,
                                    ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                                    )
                                    
                if NComponents > NCPUs: 
                    continue # impossible match, just retry
                
                NCPUsPerComponent = NCPUs / NComponents
                # ensure restrictions are met 
                if NCPUsPerComponent < CurrentSWFParams.MinComponentSize or \
                   NCPUsPerComponent > CurrentSWFParams.MaxComponentSize:
                    continue
                
                NRemainingComponents = NCPUs - NCPUsPerComponent * NComponents
                if NRemainingComponents > 0 and CurrentSWFParams.EqualCPUsPerComponent == 1:
                    continue
                    
                # >= -> including the extra CPU for some components
                if NRemainingComponents > 0 and NCPUsPerComponent == CurrentSWFParams.MaxComponentSize:
                    continue
                
                SiteType = AIRandomUtils.getRandomWeightedListElement(
                                    CurrentSWFParams.SiteTypesWithWeightsDic,
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
                                    CurrentSWFParams.SitesWithWeightsDic,
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
                
            # skip errors
            if WhileCondition != 0:
                continue
                    
            #--- generate job
            Application = CurrentSWFParams.Application
            Submitter = CurrentSWFParams.Submitter
            ApplicationBinaryFullPath = os.path.join(CurrentSWFParams.AppBaseDir, CurrentSWFParams.Application)
            SWFConstsInstace = SWFConsts()
            # convert the start time from ms to s
            JobStartTime = 1000 * (Job[SWFConstsInstace.SubmitTime] - FirstJob[SWFConstsInstace.SubmitTime])
            if JobStartTime < 0:
                print "Flurry! JobStartTime < 0"
                print "FirstJob=", FirstJob
                print "Job=", Job
            
            #-- generate job: ID
            CurrentUnitID = "%s-%d-%d" % (UnitID, GroupID, JobIndex % NJobsInList)
            #-- generate job: index
            UnitsDic['info'][JobIndex] = \
                        generateJobInfo( UnitDir, CurrentUnitID, JobIndex, Application, \
                                         WLUnit, SubmitDurationMS, Submitter, \
                                         CurrentSWFParams.UseArrivalTimeDistribution, JobStartTime )
            #-- generate job: components
            UnitsDic['jobs'][JobIndex] = generateJobComponents( 
                            UnitDir, CurrentUnitID, JobIndex, WLUnit, 
                            PreComponentsList, ApplicationBinaryFullPath, \
                            NCPUs, Job, CurrentSWFParams.MaxWallTime )
                            
            #-- be more descriptive
            UnitsDic['info'][JobIndex]['description'] = \
                UnitsDic['info'][JobIndex]['description'] + \
                " Components: %d. NCPUs: %d." % (len(PreComponentsList), NCPUs) 
                            
            #--- done generating
            if UnitsDic['jobs'][JobIndex] == None:
                NJobs = NJobs - 1 #-- don't ack job, but make sure total no of jobs is decreased
            else:
                print "SWF generator: Generated a job of type", Application, 
                print "with", len(PreComponentsList), "components/", 
                print NCPUs, "CPUs, in", UnitsDic['info'][JobIndex]['jdf']
                JobIndex = JobIndex + 1
              
        # add the delay between separate units
        SWF_LastRunTime = SWF_LastRunTime + CurrentSWFParams.DelayBetweenUnits
        
    print "Generated", JobIndex, "jobs."
    WLUnit['generatedjobs'] = JobIndex

    #raise Exception, "SWF generator: Not implemented yet"
    return UnitsDic


    
if __name__ == "__main__":
    print "SWF-workload"
    pass
    
