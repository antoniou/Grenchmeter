"""
    The GrenchmarkController class is responsible for 
    the management of Grenchmark, more particularly
    it calls the generation and sumbission modules
    of Grenchmark
"""

__rev = "0.01";
__author__ = 'Athanasios Antoniou';
__email__ = 'A.Antoniou at ewi.tudelft.nl';
__file__ = 'GrenchmarkController.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2011/04/04 14:12:39 $"
__copyright__ = "Copyright (c) 2011 Athanasios Antoniou"
__license__ = "Python" 

import time
import sys
import os
import operator
if "Cmeter/analysis/" not in sys.path:
    sys.path.append("Cmeter/analysis/")

import analyze

validConfigurationKeys = ('Util','Distr','ErrorMargin','MaxDuration')
MAX_DURATION = 1000000000

class GrenchmarkController:
    def __init__(self,cMeterHandle, workloadConfig):
        self.workloadConfig = workloadConfig
        self.cMeterHandle = cMeterHandle
        self._utilizSatisfied = False
        
    def generateWorkload(self,genArgs,useArrivalDistribution = False):
        
        if useArrivalDistribution is True:
            arrivalArg = "\'{0}({1})\'".format(self.workloadConfig.getConfig("Distr"),
                                           self.meanArrivalTime)
            genArgs['--arrival'] = arrivalArg
        
        maxDuration = MAX_DURATION    
        maxDur = self.workloadConfig.getConfig("MaxDuration") 
        if maxDur is not None:
            maxDuration = maxDur
            
        genArgs["--duration"] = maxDuration
        
        argString = self.generateArgs(genArgs)
        
        workloadGenCommand = "python wl-gen.py --jdfgen=jsdl-jdf {0}".format(argString) 
        workloadGenCommand += " 1>/dev/null"
        os.chdir("Grenchmark/")
        result = os.system(workloadGenCommand)
        
        if result!=0: 
            print "ERROR during the workload generation phase."
            print "Exiting..."
            sys.exit(2)
            
        os.chdir("..")
        
    def submitWorkload(self, submitArgs):
        
        argString = self.generateArgs(submitArgs)
        
        workloadSubmitCommand = "python wl-submit.py {0} ".format(argString)
        workloadSubmitCommand+="1>/dev/null"
        os.chdir("Grenchmark/")
        result = os.system(workloadSubmitCommand)
        
        if result!=0: 
            print "ERROR during the workload submission phase."
            print "Exiting..."
            sys.exit(2)
            
        os.chdir("..")
        
        # Wait until all jobs in the workload have been executed
        print "!STATUS: Waiting until workload has been executed"
        while not self.cMeterHandle.isStatus("ready"):
            print "Cmeter Status is {0}".format(self.cMeterHandle.getStatus())
            time.sleep(5)
            
    def generateArgs(self,argumentDic):
        argString=""
        for arg in argumentDic:
            if argumentDic[arg]=='':
                argString+= " {0} ".format(arg)
            else:
                argString+= " {0}={1} ".format(arg,argumentDic[arg])
                
        return argString
        
    def defineArrivalDistrParameters(self):
        
        self.estimateAverage("ded_runtime")
        print "Average CPU time is ", self.avgMetric
        
        self.calculateDistrParameters()
        
    def estimateAverage(self,metric):
        workloadSubmitFile = self.workloadConfig.getWorkloadOutDir() + "/wl-to-submit.wl00"
        dedicatedMode = True
        submitArgs = { workloadSubmitFile:''}
        if dedicatedMode:
            submitArgs["--dedicated"]=''
            
        #self.submitWorkload(submitArgs)
        
        self.cMeterHandle.storeDedStatsToDB()
    
        analysis = analyze.Analysis()
        self.avgMetric = analysis.getAverage(metric)
        
        print "Average Metric is",self.avgMetric
        
    def calculateDistrParameters(self):
        utilization = float(self.workloadConfig.getConfig("Util"))
        
        numberOfComputingUnits = self.cMeterHandle.resourceManager.getNumberOfComputingUnits()
        
        self.meanArrivalTime = self.avgMetric  / (utilization * numberOfComputingUnits)*1000
        
        print "Mean arrival time for {0} computing units is: {1}".format(numberOfComputingUnits, self.meanArrivalTime)
        
         
    def verifyUtilization(self):

        hashValues, arrivalTimes = self.getWorkloadInfo()
        
        try:
            jobRunTimes = self.getRunTimes(hashValues)
            meanRunTime = self.calculateMeanRunTime(jobRunTimes)*1000
        except:
            # Runtimes are not known---> use avgMetric instead
            meanRunTime = self.avgMetric * 1000  
        
        meanInterarrivalTime = self.calculateMeanInterarrivalTime(arrivalTimes)
        
        numberOfComputingUnits = self.cMeterHandle.resourceManager.getNumberOfComputingUnits()
        computedUtilization = meanRunTime / ( meanInterarrivalTime * numberOfComputingUnits )
        
        print "Mean inter-arrival time is: {0}".format(meanInterarrivalTime)
        print "!STATUS. Computed utilization is ", computedUtilization
        
        self.determineSatisfiability(computedUtilization)
        
    def calculateMeanRunTime(self,runTimes):
        meanRunTime = reduce(operator.add, runTimes)/ len(runTimes)
        return meanRunTime 
        
        
    def getRunTimes(self,hashValues):
        runTimes = []
        for hashVal in hashValues:
            runTimeDic = self.cMeterHandle.databaseStatistics.getKnownStats(hashVal)
            runTimes.append(runTimeDic['jobExec'])
        return runTimes
        
    def determineSatisfiability(self,computedUtilization):
        
        errorMargin = float(self.workloadConfig.getConfig("ErrorMargin"))
        desiredUtilization = float(self.workloadConfig.getConfig("Util"))
            
        if computedUtilization <= desiredUtilization * (1 + errorMargin) \
            and \
           computedUtilization >= desiredUtilization * (1 - errorMargin):
            print "!STATUS: Utilization requirements satisfied!"
            self._utilizSatisfied = True
            
    def calculateMeanInterarrivalTime(self,arrivalTimes):
        interarrivalTimes=[arrivalTimes[0]]
        for i in range(1,len(arrivalTimes)):
            interarrivalTimes.append(arrivalTimes[i] - arrivalTimes[i-1])
            
        print "Interarrival times are:",interarrivalTimes
            
        meanInterarrivalTime = reduce(operator.add, interarrivalTimes)/ len(interarrivalTimes) 
        
        return meanInterarrivalTime
    
    def getWorkloadInfo(self):
        arrivalTimesFileName = "arrivalTimes.dat"
        arrivalTimes = [] 
        hashValues = []
        try:
            arrivalTimesFile  = open(arrivalTimesFileName,'r')
            for tuple in arrivalTimesFile:
                hashValue,arrivalTime = tuple.split('\t')
                arrivalTimes.append(float(arrivalTime))
                hashValues.append(hashValue)
        except:
            print "ERROR: While reading runTimes from file {0}".format(arrivalTimesFileName)
            
        arrivalTimesFile.close()
        
        return hashValues, arrivalTimes
                        
    def utilSatisfied(self):
        return self._utilizSatisfied

class WorkloadConfig:
    
    def __init__(self,workloadFile, workloadOutDir):
        self.workloadFile = workloadFile
        self.workloadDir  = workloadOutDir
        self.configDic = dict()
        self.read(workloadFile)
        
    def getWorkloadFile(self):
        return self.workloadFile
    
    def getWorkloadOutDir(self):
        return self.workloadDir
        
    def read(self,workloadFile):
        LineNo = 0
        InFile = open( workloadFile ) 
        while 1:
            lines = InFile.readlines(100000) # buffered read
            if not lines:
                break
            #-- process lines
            
            for line in lines: 
                LineNo = LineNo + 1
                if len(line) > 0:
                    line=line.strip() 
                    
                # Configuration line 
                if (len(line) > 0) and (line[0] == 'c'):
                    #Remove 'c' character
                    line = line[1:]
                    try:
                        self.getConfigurationLine(line.split(','))
                    except:
                        print "Erroneous configuration line #", LineNo, "('" + line + "')", "...skipping"
                    continue
        
        # close the WL desc file
        InFile.close()
        print "CONFIGDIC IS ",self.configDic
        
    def getConfigurationLine(self, configs):

        for config in configs:
            try:
                key,value = config.strip().split('=')
            except:
                raise
            
            if key in validConfigurationKeys:
                # if Utilization is given
                self.configDic[key] = value
            else:
                raise Exception
            
    def getConfig(self,key):
        try:
            return self.configDic[key]
        except :
            # Key does not exist
            return None
            
    def systemUtilizationMode(self):
        return self.getConfig('Util')!=None
