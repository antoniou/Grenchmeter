#! /usr/bin/env python

"""
NAME
    GenBPatterns -- generate basic workflow patterns

"""

#---------------------------------------
# Log:
# 15/04/2008 C.S. 0.1	Started this app.
#---------------------------------------

__rev = "0.1";
__author__ = 'Corina Stratam';
__email__ = 'corina at cs.pub.ro';
__file__ = 'WLCompositeGenBPatterns.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2007/10/21 14:27:05 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python" 

import sys
import os
import getopt
import string
import time
import shutil
import glob
if "utils" not in sys.path: sys.path.append("utils")
import AIRandomUtils
import WFDAGMan
import ASPNShell
import AIParseUtils
import traceback
from WLCompositeGenGraphs import TaskGraph
from WLCompositeGenGraphs import DOTColorTypes

__verbose = 0

class BPatternTaskGraph(TaskGraph):
    
#    KnownExtOutputFormats = {'dagman':WFDAGMan.saveToDAGMan, 'karajan':WFKarajan.saveToKarajan}
    
    #--- init
    def __init__(self, GraphID = 'graph', GraphName = None):
        TaskGraph.__init__(self, GraphID, GraphName = None)
              
    #--- generators
    def generateSequencePattern( self, NTasks = 20):
        """
        NTasks -- the number of tasks in the graph
        """
        ##print "NTasks=", NTasks, "type(NTasks)", type(NTasks)
        ##print "p=", p, "type(p)", type(p)
        
        self.resetAll()
        self.NTasks = NTasks
        
        for i in xrange(NTasks - 1):
            self.TaskEdges[i] = {}
            self.TaskEdges[i][i + 1] = 1
        self.TaskEdges[NTasks - 1] = {}
            
                        
    def generateParallelSplitPattern( self, NBranches = 4, MinTasksPerBranch = 1, MaxTasksPerBranch = 10 ):
        """
        NBranches -- the number branches to be executed in parallel
        MinTasksPerBranch -- minimum number of tasks to generate in a branch
        MaxTasksPerBranch -- maximum number of tasks to generate in a branch
        """
        ##print "NTasks=", NTasks, "type(NTasks)", type(NTasks)
        ##print "NConnect=", NConnect, "type(NConnect)", type(NConnect)
        if (MinTasksPerBranch > MaxTasksPerBranch):
            MaxTasksPerBranch = MinTasksPerBranch
        
        OneRandom = AIRandomUtils.AIRandom()
        
        self.resetAll()
        #self.NTasks = NTasks
        CrtTask = 0
        
        for i in xrange(NBranches):
            rnd = int(OneRandom.nextUniform([MinTasksPerBranch,MaxTasksPerBranch]))
            #print "### Generating %d tasks per branch\n" % rnd
            for j in xrange(rnd - 1):
                self.TaskEdges[CrtTask] = {}
                self.TaskEdges[CrtTask][CrtTask + 1] = 1 
                CrtTask = CrtTask + 1
            self.TaskEdges[CrtTask] = {}
            CrtTask = CrtTask + 1
                
        self.NTasks = CrtTask
        
                
    
        
class BPatternGraphType:
    FromSTG = 0
    Sequence = 1
    ParallelSplit = 2
    LastType = 3
    Names = { 'FromSTG' : 0,
              'Sequence' : 1,
              'ParallelSplit' : 2 }
    
def getBPatternGraphTypeName( Type ):
    if Type == BPatternGraphType.FromSTG:
        return "BPatternGraphType.FromSTG : graph generated from STG file"
    elif Type == BPatternGraphType.Sequence:
        return "BPatternGraphType.Sequence : graph generated using the Sequence pattern"
    elif Type == BPatternGraphType.ParallelSplit:
        return "BPatternGraphType.ParallelSplit : graph generated using the ParallelSplit pattern"
    return None

def generateRandomGraph( KeyValueDic ):
    
    try:
        keys = ['GraphID', 'GraphType', 'GraphData', 'GraphName', 'STGFileNamesList', 'OutDir', 'OutFileName']
        for kw in keys:
            temp = KeyValueDic[kw]
    except:
        print "Could not find keyword", kw, "quitting!"
    
    GraphID   = KeyValueDic['GraphID']
    GraphType = KeyValueDic['GraphType']
    GraphData = KeyValueDic['GraphData']
    STGFileNamesList = KeyValueDic['STGFileNamesList']
    OutDir = KeyValueDic['OutDir']
    OutFileName = KeyValueDic['OutFileName']
    GraphName = KeyValueDic['GraphName']
    
    print 'Generating a', getBPatternGraphTypeName(GraphType), "graph"
    
    OneRandom = AIRandomUtils.AIRandom()
    
    OneTaskGraph = BPatternTaskGraph(GraphID, GraphName)
    if GraphType == BPatternGraphType.FromSTG:
        STGName = OneRandom.getRandomListElement(STGFileNamesList)
        OneTaskGraph.loadFromSTG( STGName )
        #OneTaskGraph.removeLastTask()
        OneTaskGraph.autosetPredSuccLeaf()
        
    elif GraphType == BPatternGraphType.Sequence:
        OneTaskGraph.generateSequencePattern( GraphData['NTasks'] )
        OneTaskGraph.autosetPredSuccLeaf()
        OneTaskGraph.autosetUniqueStartEnd()
        
    elif GraphType == BPatternGraphType.ParallelSplit:
        OneTaskGraph.generateParallelSplitPattern( GraphData['NBranches'], GraphData['MinTasksPerBranch'], GraphData['MaxTasksPerBranch'] )
        OneTaskGraph.autosetPredSuccLeaf()
        OneTaskGraph.autosetUniqueStartEnd()
        
    else:
        raise Exception, "generateBPatternGraph got wrong type of graph type: " + str(GraphType)
        
    #OneTaskGraph.printEdges()
    OneTaskGraph.autosetPredSuccLeaf()
    OneTaskGraph.doTopologicalSort()

    OneTaskGraph.assignRandomDataToAllTasks([{'name':'node', 'colordata':(0.628,0.227,1.000),'colortype':DOTColorTypes.HSB}])
    OneTaskGraph.setEdgeColor({'colordata':(0.649,0.701,0.701),'colortype':DOTColorTypes.HSB})
    
    if OutFileName is not None:
        OneTaskGraph.saveToDOT(os.path.join( OutDir, OutFileName ), 
                               {'GraphName':GraphID, 'Comment':GraphName})
        
    return OneTaskGraph
    
def readAllParams( WLUnit ):
    
    Params = {}
    for ParamCategory in BPatternGraphType.Names:
        Params[ParamCategory] = {}
        
    try:
        Sequence_NTasksWithWeights = \
            AIParseUtils.readIntWithWeightsList( 
                WLUnit['otherinfo']['Params.Sequence.NTasksWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['Sequence']['NTasksWithWeights'] = Sequence_NTasksWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
        
    try:
        ParallelSplit_NBranchesWithWeights = \
            AIParseUtils.readIntWithWeightsList( 
                WLUnit['otherinfo']['Params.ParallelSplit.NBranchesWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['ParallelSplit']['NBranchesWithWeights'] = ParallelSplit_NBranchesWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
    try:
        ParallelSplit_MinTasksPerBranchWithWeights = \
            AIParseUtils.readIntWithWeightsList( 
                WLUnit['otherinfo']['Params.ParallelSplit.MinTasksPerBranchWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['ParallelSplit']['MinTasksPerBranchWithWeights'] = ParallelSplit_MinTasksPerBranchWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
        
    try:
        ParallelSplit_MaxTasksPerBranchWithWeights = \
            AIParseUtils.readIntWithWeightsList( 
                WLUnit['otherinfo']['Params.ParallelSplit.MaxTasksPerBranchWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['ParallelSplit']['MaxTasksPerBranchWithWeights'] = ParallelSplit_MaxTasksPerBranchWithWeights
    except:
        ##
        print traceback.print_exc()
        pass

    return Params
    
    
def generateRandomStructures(WLOutDir, WLUnitID, WLUnit, SubmitDurationMS):
    #--- params read
    ##print ">>> WLUnit=", WLUnit
    try:
        NCompositeItems = AIParseUtils.readInt(WLUnit['otherinfo']['NCompositeItems'], 1)
    except:
        NCompositeItems = 1
        
    try:
        GraphTypesWithWeights = \
                AIParseUtils.readStringWithWeightsList( 
                    WLUnit['otherinfo']['GraphTypesWithWeights'], 
                    DefaultWeight = 1.0, ItemSeparator = ';' 
                    )
##        ValidGraphTypesWithWeights = {}
##        for GraphType in GraphTypesWithWeights[AIParseUtils.VALUES]:
##            if GraphTypes not in RandomGraphType.Names:
##                print "WARNING!", GraphTypes, "is not a valid GraphType. Skipping it."
##            else:
##                ValidGraphTypesWithWeights[GraphTypes] = GraphTypesWithWeights[AIParseUtils.VALUES][GraphTypes]
##        GraphTypesWithWeights[AIParseUtils.VALUES] = ValidGraphTypesWithWeights
    except:
        print "ERROR! No GraphTypesWithWeights info specified in the OtherInfo field.\n\tQuitting!"
        return None
    ##print ">>> GraphTypesWithWeights=", GraphTypesWithWeights
        
        
    STGFileNamesList = []
    try:
        STGFilters = WLUnit['otherinfo']['STGFiles']
        STGFilterList = STGFilters.split(',')
        for Filter in STGFilterList:
            CurrentSTGList = glob.glob(Filter)
            for STGFileName in CurrentSTGList:
                if STGFileName not in STGFileNamesList:
                    STGFileNamesList.append(STGFileName)
    except:
        STGFileNamesList = []
        pass
        
    ##print ">>>", "before Params = readAllParams( WLUnit )"
    Params = readAllParams( WLUnit )
    ##print ">>>", "after Params = readAllParams( WLUnit )"
        
    #--- init
    ListOfGraphs = []
        
    #--- generate all composite structures
    index = 0
    maxIndex = NCompositeItems
    while index < maxIndex:
        #--- generate one composite structure
        GraphID = WLUnitID + ("-%d_graph" % index)
        #print("### Graph ID initial: " + GraphID)
        #print ("### WLUnit ID initial: " + WLUnitID)
        GraphType = AIRandomUtils.getRandomWeightedListElement(
                            GraphTypesWithWeights,
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            )
        GraphType = BPatternGraphType.Names[GraphType]
        #print ">>>", "Selected", GraphType, "from", GraphTypesWithWeights
        
        
        GraphName = getBPatternGraphTypeName(GraphType)
        GraphData = {}
        if GraphType == BPatternGraphType.FromSTG:
            pass            
        elif GraphType == BPatternGraphType.Sequence:
            try:
                GraphData['NTasks'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['Sequence']['NTasksWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
            except Exception, e:
                print "Could not find a definition for", getRandomGraphTypeName(GraphType), "parameter", e
                continue
            GraphName = GraphName + ' NTasks=' + str(GraphData['NTasks']) 
        elif GraphType == BPatternGraphType.ParallelSplit:
            try:
                GraphData['NBranches'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['ParallelSplit']['NBranchesWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
                
                GraphData['MinTasksPerBranch'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['ParallelSplit']['MinTasksPerBranchWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
                #print "### MinTasksPerBranch: %d \n" % GraphData['MinTasksPerBranch']
                        
                GraphData['MaxTasksPerBranch'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['ParallelSplit']['MaxTasksPerBranchWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
                #print "### MaxTasksPerBranch: %d \n" % GraphData['MaxTasksPerBranch']
            except Exception, e:
                print "Could not find a definition for", getRandomGraphTypeName(GraphType), "parameter", e
                continue
            GraphName = GraphName + ' NBranches=' + str(GraphData['NBranches']) + ' MinTasksPerBranch=' + str(GraphData['MinTasksPerBranch']) + ' MaxTasksPerBranch=' + str(GraphData['MinTasksPerBranch'])
        
        #--- generate structure
        CurrentData = {}
        CurrentData['GraphID'] = GraphID
        CurrentData['GraphName'] = GraphName
        CurrentData['GraphType'] = GraphType
        CurrentData['GraphData'] = GraphData
        CurrentData['STGFileNamesList'] = STGFileNamesList
        CurrentData['OutDir'] = None
        CurrentData['OutFileName'] = None
        ListOfGraphs.append( generateRandomGraph(CurrentData) )
        
        #-- ack generated structure
        index = index + 1 
    
    return ListOfGraphs
  
if __name__ == "__main__":
    
    pass
    
