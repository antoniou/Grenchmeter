#! /usr/bin/env python

"""
NAME
    GenGraphs -- generate random graphs, based on the STG style

SYNOPSIS
    %(progname)s [args]

DESCRIPTION
    Generate random graphs according to Standard Task Graph Set (STG) 
    indications (http://www.kasahara.elec.waseda.ac.jp/schedule/). 
             
    Arguments:
    
    -i <dir name>,--indir=<dirname>
        use as default input directory for stg files [default ./]
        
    -s <stg file1,...,stg filen>, --stgfiles <stg file1,...,stg filen>
        comma-separated list of files in stg format (can include wildcards)
        [default *.stg]
                
    -o <dir name>,--outdir=<dirname>
        use as default output directory [default ./]
        
    -g <no graphs>, --graphs=<no graphs>
        number of graphs to generate [default 50]
        
OUTPUT
    for each graph to generate
        randomly select type of graph
        if type == FromSTGFile
            load STG file from InDir/STGFile_i, 
                 where STGFile_i is a random file name
         if type == FromTextGraphFile
            load text/graph file from InDir/TextGraphFile_i, 
                 where TextGraphFile_i is a random file name
        
FILE FORMATS
    .stg
    Line1: NoTasks
    Line2 (Dummy start job line): TaskID 0 0 0
    Line3-: TaskID TaskComputationUnits NPredecessors PredecessorsList
    Line n (Dummy end job line): TaskID 0 ? ListOfLeavesBeforeThisNode
    Line n+ (comments): # .....
    
    .dot
    See docs about graphviz at http://www.graphviz.org.
    In particular, read the dot tool user's manual, at:
       http://www.graphviz.org/Documentation/dotguide.pdf
       
   .graph
    Line1: NoTasks
    Line2-: TaskID NPredecessors PredecessorsList
    Comment lines: # .....
    (Note: the TaskIDs are consecutive numbers ranging from 0 to NoTasks-1, and are sorted 
    in the input file)

REPORTING BUGS
    Report bugs to <A.Iosup at ewi.tudelft.nl>.
    
"""

__rev = "0.33";
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'GenGraphs.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:27:05 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python" 

#---------------------------------------------------
# Log:
# 23/02/2008 C.S. 0.3 New functionalities;
#                        - Add the possibility to load from text/graph files
# 01/12/2007 C.S. 0.2 New functionalities;
#                        - added new external output formats (Condor DAGMan, Karajan)
# 12/08/2005 A.I. 0.1  Started this app
#---------------------------------------------------

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
import WFKarajan
import ASPNShell
import AIParseUtils
import traceback

__verbose = 0


class DOTColorTypes:
    RGB = 0
    HSB = 1
    XWinName = 2

class STGStage:
    NTasks = 0
    DummyNode = 1
    TaskLine = 2

class TaskGraph:
    KnownExtOutputFormats = {'dagman':WFDAGMan.saveToDAGMan, 'karajan':WFKarajan.saveToKarajan}
    
    #--- init
    def __init__(self, GraphID = 'graph', GraphName = None):
        self.resetAll()
        self.EdgeColor = (0.649,0.701,0.701)
        self.KnownOutputFormats = {'dot':self.saveToDOT}
        
        self.GraphID = GraphID
        self.GraphName = GraphName
        
    def resetAll(self):
        self.TaskEdges = {}
        self.NTasks = 0
        self.MaxTasks = 0
        self.TasksIDs = {}
        self.TasksData = {}
        
    #--- composite apps interface
    def getID(self):
        """ returns the ID of this composite structure """
        return self.GraphID
        
    def getNNodes(self):
        """ returns the number of nodes in this composite structure """
        return self.NTasks
        
    def getMaxLevels(self):
        """ 
        returns the maximum levels in a topological sort of the nodes 
        in this composite structure 
        """
        return self.MaxLevels
        
    def getNodeDepth(self, nodeid):
        """ returns the node's depth or -1 """
        if nodeid in self.NodeDepth:
            return self.NodeDepth[nodeid]
        return -1
        
    def getNodeData(self, nodeid):
        """ returns the node's data or None """
        if nodeid in self.TasksData:
            return self.TasksData[nodeid]
        return None
        
    def setNodeData(self, nodeid, data):
        """ sets the node's data """
        self.TasksData[nodeid] = data        
        
    def getNodeSuccessors(self, nodeid):
        """ returns a list of successors of the given node, or [] """
        if nodeid in self.TaskEdges: 
            return self.TaskEdges[nodeid]
        return []
        
    def getNodePredecessors(self, nodeid):
        """ returns a list of predecessors of the given node, or [] """
        ListOfPredecessors = []
        for i in xrange(self.NTasks):
            if i in self.TaskEdges: 
                if nodeid in self.TaskEdges[i] and self.TaskEdges[i][nodeid] == 1:
                    ListOfPredecessors.append(i)
        return ListOfPredecessors
        
    def saveToFile(self, OutFileName, FileFormat = None, ParamsDic = None):
        print "STATUS! Saving to file format: %s" % FileFormat
        if FileFormat:
            if FileFormat in self.KnownOutputFormats:
                self.KnownOutputFormats[FileFormat](OutFileName, ParamsDic)
            if FileFormat in TaskGraph.KnownExtOutputFormats:
                TaskGraph.KnownExtOutputFormats[FileFormat](self, OutFileName, ParamsDic)
        else:
            self.saveToDefault( OutFileName, ParamsDic )
        
    #--- generators
    def generateGraphSameProb( self, NTasks = 20, p = 0.2 ):
        """
        NTasks -- the number of tasks in the graph
        p      -- edge connection probability ( in [0.0,1.0] )
                  P[a(i,j)=1]=p for 1<=i<j<=n
                  P[a(i,j)=0]=1-p for 1<=i<j<=n
                  P[a(i,j)=0]=1 if i>=j
        """
        ##print "NTasks=", NTasks, "type(NTasks)", type(NTasks)
        ##print "p=", p, "type(p)", type(p)
        
        OneRandom = AIRandomUtils.AIRandom()
        
        self.resetAll()
        self.NTasks = NTasks
        
        for i in xrange(NTasks):
            self.TaskEdges[i] = {}
            for j in xrange(NTasks):
                # note: did not init TaskEdges[i][j] to 0 here, to closely match this code to the algo
                if i>=j:
                    self.TaskEdges[i][j] = 0
                else:
                    rnd = OneRandom.nextUniform([0.0,1.0]) # link from task i to task j
                    #print "Random = %.3f" % rnd, "rnd <= p:", rnd <= p
                    if rnd <= p:
                        self.TaskEdges[i][j] = 1
                    else: 
                        self.TaskEdges[i][j] = 0
                        
    def generateGraphSamePred( self, NTasks = 20, NConnect = 3 ):
        """
        NTasks -- the number of tasks in the graph
        NConnect -- number of nodes to which this node connects ( in {1,3,5} )
                  NOTE: node i can connect with node j, even if j<i!
        """
        ##print "NTasks=", NTasks, "type(NTasks)", type(NTasks)
        ##print "NConnect=", NConnect, "type(NConnect)", type(NConnect)
        
        OneRandom = AIRandomUtils.AIRandom()
        
        self.resetAll()
        self.NTasks = NTasks
        
        for i in xrange(NTasks):
            self.TaskEdges[i] = {}
            for j in xrange(NTasks):
                self.TaskEdges[i][j] = 0
            for j in xrange(NConnect):
                rnd = int(OneRandom.nextUniform([0.0,NTasks])) # link from task rnd to task i
                while rnd == i:
                    rnd = int(OneRandom.nextUniform([0.0,NTasks])) # link from task rnd to task i
                if rnd not in self.TaskEdges: self.TaskEdges[rnd] = {}
                self.TaskEdges[rnd][i] = 1
                
    def generateGraphLayerProb( self, NLayers = (2,5), NLayerTasks = (1,10), p = 0.2 ):
        """
        NLayers -- the number of layers in the graph, as a (min, max) tuple
        NLayerTasks
            the number of tasks per layer, as a (min, max) tuple 
            (random for each layer)
        p       -- edge connection probability ( in [0.0,1.0] )
                   NOTE: edges connect different layers; 
                  for each edge (i,j), i, j not in the same layer
                    P[a(i,j)=1]=p for 1<=i<j<=n
                    P[a(i,j)=0]=1-p for 1<=i<j<=n
                  P[a(i,j)=0]=1 if i>=j, or i, j in the same layer
                    
        """
        
        ##print "NLayers=", NLayers, "type(NLayers)", type(NLayers)
        ##print "NLayerTasks=", NLayerTasks, "type(NLayerTasks)", type(NLayerTasks)
        ##print "p=", p, "type(p)", type(p)
        
        OneRandom = AIRandomUtils.AIRandom()
        
        #-- create layers, and assign them tasks
        GraphNLayers = OneRandom.getRandomInt(NLayers[0], NLayers[1])
        TaskLayer = {}
        iCurrentTask = 0
        for Layer in xrange(GraphNLayers):
            LayerNTasks = OneRandom.getRandomInt(NLayerTasks[0], NLayerTasks[1])
            for Task in xrange(LayerNTasks):
                TaskLayer[iCurrentTask + Task] = Layer
            iCurrentTask = iCurrentTask + Task
            
        self.resetAll()
        self.NTasks = iCurrentTask
        
        for i in xrange(self.NTasks):
            self.TaskEdges[i] = {}
            for j in xrange(self.NTasks):
                # note: did not init TaskEdges[i][j] to 0 here, to closely match this code to the algo
                if (i>=j) or (TaskLayer[i] == TaskLayer[j]):
                    self.TaskEdges[i][j] = 0
                else:
                    rnd = OneRandom.nextUniform([0.0,1.0]) # link from task i to task j
                    #print "Random = %.3f" % rnd, "rnd <= p:", rnd <= p
                    if rnd <= p:
                        self.TaskEdges[i][j] = 1
                    else: 
                        self.TaskEdges[i][j] = 0
                        
    def generateGraphLayerPred( self, NLayers = (2,5), NLayerTasks = (1,10), NConnect = 3 ):
        """
        NLayers -- the number of layers in the graph, as a (min, max) tuple
        NLayerTasks
            the number of tasks per layer, as a (min, max) tuple 
            (random for each layer)
        NConnect -- number of nodes to which this node connects ( in {1,3,5} )
                  NOTE: node i cannot be node j's predecessor, if Layer[i]!=Layer[j]-1
                    
        """
        
        ##print "NLayers=", NLayers, "type(NLayers)", type(NLayers)
        ##print "NLayerTasks=", NLayerTasks, "type(NLayerTasks)", type(NLayerTasks)
        ##print "NConnect=", NConnect, "type(NConnect)", type(NConnect)
        
        OneRandom = AIRandomUtils.AIRandom()
        
        #-- create layers, and assign them tasks
        GraphNLayers = OneRandom.getRandomInt(NLayers[0], NLayers[1])
        Layers = {}
        TaskLayer = {}
        iCurrentTask = 0
        for Layer in xrange(GraphNLayers):
            Layers[Layer] = []
            LayerNTasks = OneRandom.getRandomInt(NLayerTasks[0], NLayerTasks[1])
            for Task in xrange(LayerNTasks):
                Layers[Layer].append(iCurrentTask + Task)
                TaskLayer[iCurrentTask + Task] = Layer
            iCurrentTask = iCurrentTask + LayerNTasks
            
        self.resetAll()
        self.NTasks = iCurrentTask
        
        for i in xrange(self.NTasks):
            self.TaskEdges[i] = {}
            for j in xrange(self.NTasks):
                self.TaskEdges[i][j] = 0
            if TaskLayer[i] > 0:
                for j in xrange(NConnect):
                    # get a random node from the previous layer
                    rnd = OneRandom.getRandomListElement(Layers[TaskLayer[i]-1]) 
                    self.TaskEdges[rnd][i] = 1
                
    #--- loaders
    
    def loadFromSTG(self, STGFileName):
        
        self.resetAll()
        
        InFile = open(STGFileName, "rt")
        Stage = STGStage.NTasks
        while 1:
            lines = InFile.readlines(1000000) # 1M buffer
            if not lines: break
            #-- process lines
            for line in lines:
                #print "line=", line 
                if (len(line) > 0) and (line[0] != '#'): 
                    if Stage == STGStage.NTasks:
                        self.MaxTasks = int(Stage)
                        BlockLen = len(line) - 1
                        ##print BlockLen
                        Stage = STGStage.DummyNode
                        #print "Stage=", Stage
                    elif Stage == STGStage.DummyNode:
                        #Stage = STGStage.TaskLine
                        #print "Stage=", Stage
                    #elif Stage == STGStage.TaskLine:
                        DataKeys = ['TaskNo','ProcessingTime','NPredecessors']
                        Data = {}
                        LinePos = 0
                        for Key in DataKeys:
                            try:
                                Data[Key] = int(line[LinePos:LinePos+BlockLen])
                            except Exception, e:
                                print "EXCEPTION>>", e
                                print "Line:", line
                            LinePos=LinePos+BlockLen
                        
                        j = Data['TaskNo']
                        self.TasksIDs[j] = self.NTasks
                        self.NTasks = self.NTasks + 1
                        PredecessorsList = []
                        for Predecessor in xrange(Data['NPredecessors']):
                            PredecessorID = int(line[LinePos:LinePos+BlockLen])
                            LinePos=LinePos+BlockLen
                            PredecessorsList.append(PredecessorID)
                            
                            i = PredecessorID
                            if i not in self.TasksIDs: 
                                raise Exception, "ERROR! Predecessor with ID=%d of task %d not found!" % (i,j)
                                
                            if self.TasksIDs[i] not in self.TaskEdges: 
                                self.TaskEdges[self.TasksIDs[i]] = {}
                                #print "Init'd TasksIDs[", i, "]"
                            self.TaskEdges[self.TasksIDs[i]][self.TasksIDs[j]] = 1
                            
                        ##print Data['TaskNo'], PredecessorsList
                        #print Data, PredecessorsList
                        #print "Stage=", Stage
                        
                        #PredecessorsList = extra.split(' ', NPredecessors)
        InFile.close()
      
     #--- load a graph from a text/graph file (similar format with the STG but it does not specify the
     # processing time for each task)
    def loadFromTextGraph(self, GraphFileName):
        
        self.resetAll()
        
        InFile = open(GraphFileName, "rt")
        Stage = STGStage.NTasks
        while 1:
            lines = InFile.readlines(1000000) # 1M buffer
            if not lines: break
            #-- process lines
            for line in lines:
                #print "line=", line 
                if (len(line) > 1) and (line[0] != '#'): 
                    if Stage == STGStage.NTasks:
                        self.MaxTasks = int(Stage)
                        BlockLen = len(line) - 1
                        ##print BlockLen
                        
                        #assume that the task IDs from the file are consecutive numbers
                        self.NTasks = int(line)
                        for i in range(0, self.NTasks):
                            self.TasksIDs[i] = i
                        
                        Stage = STGStage.DummyNode
                        #print "Stage=", Stage
                    elif Stage == STGStage.DummyNode:
                        #Stage = STGStage.TaskLine
                        #print "Stage=", Stage
                    #elif Stage == STGStage.TaskLine:
                        DataKeys = ['TaskNo','NPredecessors']
                        Data = {}
                        LinePos = 0
                        for Key in DataKeys:
                            try:
                                Data[Key] = int(line[LinePos:LinePos+BlockLen])
                            except Exception, e:
                                print "EXCEPTION>>", e
                                print "Line:", line
                            LinePos=LinePos+BlockLen
                        
                        j = Data['TaskNo']
                        #print "### ------- Node %d \n" % j
                        #self.TasksIDs[j] = self.NTasks
                        #self.NTasks = self.NTasks + 1
                        PredecessorsList = []
                        for Predecessor in xrange(Data['NPredecessors']):
                            PredecessorID = int(line[LinePos:LinePos+BlockLen])
                            LinePos=LinePos+BlockLen
                            PredecessorsList.append(PredecessorID)
                            
                            i = PredecessorID
                            #print "### predecessor %d " % i
                            if i not in self.TasksIDs: 
                                raise Exception, "ERROR! Predecessor with ID=%d of task %d not found!" % (i,j)
                                
                            if self.TasksIDs[i] not in self.TaskEdges: 
                                self.TaskEdges[self.TasksIDs[i]] = {}
                                #print "Init'd TasksIDs[", i, "]"
                            self.TaskEdges[self.TasksIDs[i]][self.TasksIDs[j]] = 1
        InFile.close()
            
    #--- auxiliary functions
    def setEdgeColor(self, EdgeColor):
        self.EdgeColor = EdgeColor
        
    def removeTask(self, TaskID):
        ListOfTasks = self.TasksIDs.keys()
        if len(ListOfTasks) <= TaskID: return
##        FoundTask = 0
##        for OneTaskID in self.TasksIDs: 
##            if self.TasksIDs[OneTaskID] == TaskID:
##                FoundTask = 1
##        if FoundTask == 0: return
        InternalTaskID = TaskID
        if InternalTaskID in self.TaskEdges: self.TaskEdges.remove(InternalTaskID)
        for Key in self.TaskEdges:
            if InternalTaskID in self.TaskEdges[Key]:
                self.TaskEdges[Key][InternalTaskID] = 0 # remove edge
        if InternalTaskID in self.TasksData: del self.TasksData[InternalTaskID]
        del self.TasksIDs[TaskID]
        self.NTasks = self.NTasks - 1
        
    def removeTaskByID(self, TaskID):
        if TaskID not in self.TasksIDs: return
        InternalTaskID = self.TasksIDs[TaskID]
        self.removeTask(InternalTaskID)
        
    def removeLastTask(self):
        self.removeTask(self.NTasks-1)
    
    def removeFirstTask(self):
        self.removeTaskByID(0)
        
    def setTaskData(self, TaskID, Data):
        if TaskID in self.TasksIDs:
            self.TasksData[self.TasksIDs[TaskID]] = Data
        
    def assignRandomDataToAllTasks(self, DataList):
        if self.NTasks <= 0: return
        OneRandom = AIRandomUtils.AIRandom()
        for TaskID in xrange(self.NTasks):
            self.TasksData[TaskID] = OneRandom.getRandomListElement(DataList)
            
    def autosetUniqueStartEnd(self):
        """ NOTE: call after autosetPredSuccLeaf, which sets the leaves and the starters """
                    
        # create a dummy start task
        DummyStartTask = self.NTasks
        self.TasksIDs['DummyStart'] = DummyStartTask
        self.NTasks = self.NTasks + 1
        
        # link the dummy start task to all the starter tasks
        self.TaskEdges[DummyStartTask] = {}
        for StarterID in self.StarterNodes:
            self.TaskEdges[DummyStartTask][StarterID] = 1
        
        # create a dummy end task
        DummyEndTask = self.NTasks
        self.TasksIDs['DummyEnd'] = DummyEndTask
        self.NTasks = self.NTasks + 1
        
        # link all the leaf tasks to the dummy end task
        self.TaskEdges[DummyEndTask] = {}
        for EndID in self.EndTasks:
            self.TaskEdges[EndID][DummyEndTask] = 1
        
    def autosetPredSuccLeaf(self):
        self.EndTasks = [] # tasks that are leaves after adding all edges
        for iTask in xrange(self.NTasks):
            self.EndTasks.append(iTask)
            
        self.TaskEdgesList = {}
        self.TaskPrevList = {}
        for i in xrange(self.NTasks):
            self.TaskEdgesList[i] = []
            self.TaskPrevList[i] = []
            
        for i in xrange(self.NTasks):
            #if i not in TaskEdges: continue
            for j in xrange(self.NTasks):
                if (i not in self.TaskEdges) or (j not in self.TaskEdges[i]): 
                    continue # exclude non-entries
                    
                if self.TaskEdges[i][j] == 1:
                    self.TaskEdgesList[i].append(j) # mark successor
                    self.TaskPrevList[j].append(i) # mark predecessor
                    if i in self.EndTasks:
                        self.EndTasks.remove(i) # task i is no longer a leaf
                        
        self.StarterNodes = []
        for i in xrange(self.NTasks):
            self.StarterNodes.append(i)
            
        for i in xrange(self.NTasks):
            for j in self.TaskEdgesList[i]:
                if j in self.StarterNodes:
                    self.StarterNodes.remove(j)
                        
    def doTopologicalSort(self):
        
        # topological sort
        NodesToVisit = []
        self.NodeDepth = {}
        for i in xrange(self.NTasks):
            NodesToVisit.append(i)
            self.NodeDepth[i] = -1
            
        for i in xrange(self.NTasks):
            if (i in self.TaskEdgesList) and (len(self.TaskEdgesList[i]) > 0):
                for j in self.TaskEdgesList[i]:
                    if j in NodesToVisit:
                        NodesToVisit.remove(j)
                    
        ##print "Start with", NodesToVisit, "in a", self.NTasks, "tasks graph."
                    
        # BFS
        Visited = []
        self.MaxLevels = 0
        
        while len(NodesToVisit) > 0:
            # get first
            i = NodesToVisit[0]
            # remove node
            NodesToVisit.remove(i)
            
            # check whether this task is enabled and set its highest lev predecessor
            TaskEnabled = 1
            PrevMaxLevel = -1
            if i in self.TaskPrevList:
                for k in self.TaskPrevList[i]:
                    if k not in Visited:
                        TaskEnabled = 0
                        break
                    else:
                        if PrevMaxLevel < self.NodeDepth[k]: 
                            PrevMaxLevel = self.NodeDepth[k]
            
            if TaskEnabled > 0:
                # visit the node
                Visited.append(i)
                self.NodeDepth[i] = PrevMaxLevel + 1 # ack new depth
                ##if self.NTasks < 25: print "Visiting node", i, "depth=", self.NodeDepth[i]
                if self.MaxLevels < self.NodeDepth[i]: 
                    self.MaxLevels = self.NodeDepth[i]
                
                # expand the node
                if i in self.TaskEdgesList:
                    for j in self.TaskEdgesList[i]:
                        if j not in NodesToVisit and j not in Visited:
                            # add task
                            ##if self.NTasks < 25: print "Adding node", j, "(from node", i, ")"
                            NodesToVisit.append(j)
            else:
                # put last
                NodesToVisit.append(i)
                
            ##if self.NTasks < 25: print "NodesToVisit=", NodesToVisit
            
        for i in xrange(self.NTasks):
            if self.NodeDepth[i] == -1:
                self.NodeDepth[i] = 0 # first lev nodes
                        
    def printEdges(self):
        for i in xrange(self.NTasks):
            print "TaskEdges[",i,"]=", self.TaskEdges[i]
        
    #--- save to various file formats
    def saveToDefault( self, OutFileName, ParamsDic ):
        if self.GraphName is None:
            try:
                GraphName = ParamsDic['GraphName']
            except:
                GraphName = "aaa"
        else:
            GraphName = self.GraphName
        
        try:
            Comment = ParamsDic['Comment']
        except:
            Comment = ""
            
        OutFile = open(OutFileName, "wt")
        OutFile.write('# File-type: text/graph\n')
        OutFile.write('# File-version: 1.0\n')
        OutFile.write('# graph generated by GenGraphs.py by Alexandru Iosup, on %s \n' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        OutFile.write('# Info: %s\n' % Comment)
        OutFile.write('# Graph name: %s\n' % GraphName)
        OutFile.write('\n')
        OutFile.write('# Number of nodes in the graph\n')
        nodes = self.getNNodes()
        OutFile.write('%d\n' % nodes)
        OutFile.write('# For each node: <node id><space><no. predecessors><space><id pred 1><space>...<space><id pred n>\n')
        for nodeid in xrange(nodes):
            ListOfPredecessors = self.getNodePredecessors(nodeid)
            ##print '>>>', "ListOfPredecessors=", ListOfPredecessors
            OutFile.write('%d %d' % (nodeid, len(ListOfPredecessors)) )
            for predecessorID in ListOfPredecessors:
                OutFile.write(' %d' % predecessorID )
            OutFile.write('\n')
        OutFile.close()
    
    def saveToDOT(self, DOTFileName, ParamsDic):
        
        try:
            GraphName = ParamsDic['GraphName']
        except:
            GraphName = "aaa"
        
        try:
            Comment = ParamsDic['Comment']
        except:
            Comment = "%s: %s" % (self.GraphID, self.GraphName)
            
        try:
            SizeX = ParamsDic['SizeX']
        except:
            SizeX = 10.0
            
        try:
            SizeY = ParamsDic['SizeY']
        except:
            SizeY = 7.5
            
        try:
            Orientation = ParamsDic['Orientation']
        except:
            Orientation="landscape"
        
        OutFile = open(DOTFileName, "wt")
        OutFile.write('/* graph generated by GenGraphs.py by Alexandru Iosup, on %s */\n' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        OutFile.write('/* Info: %s */\n' % Comment)
        OutFile.write('digraph %s {\n' % GraphName)
        OutFile.write('\torientation=%s; size="%.1f,%.1f"; ratio = fill;\n' % (Orientation, SizeX, SizeY))
        
        # write nodes -- levels 
        OutFile.write('\t{\n')
        #OutFile.write('\t\tnode [shape=plaintext,fontsize=10];\n')
        OutFile.write('\t\t/* level summary*/\n')
        OutFile.write('\t\t')
        for CurrentLevel in xrange(self.MaxLevels):
            OutFile.write('Level%d -> ' % CurrentLevel)
        OutFile.write('Level%d;\n' % self.MaxLevels)
        OutFile.write('\t}\n')
        
        #OutFile.write('\tnode [style=filled];\n')
        for CurrentLevel in xrange(self.MaxLevels + 1):
            OutFile.write('\t{rank=same; Level%d;\n\t\t' % CurrentLevel)
            for i in xrange(self.NTasks):
                if self.NodeDepth[i] == CurrentLevel:
                    # print node here
                    OutFile.write('Task%d; ' % i)
            OutFile.write('\t}\n')
        
        # write levels
        for CurrentLevel in xrange(self.MaxLevels + 1):
            OutFile.write('\tLevel%d [shape=plaintext,fontsize=10,label="Level\\n%d"]\n' % (CurrentLevel, CurrentLevel))
            
        #OutFile.write('\tnode [style=filled,shape=ellipse];\n')    
        # write nodes -- simple
        for i in xrange(self.NTasks):
            
            Name = self.TasksData[i]['name']
            
            ColorData = self.TasksData[i]
            if ColorData['colortype'] == DOTColorTypes.HSB:
                Color = "%.3f %.3f %.3f" % ColorData['colordata']
            elif ColorData['colortype'] == DOTColorTypes.RGB:
                Color = "#%2.2x%2.2x%2.2x" % ColorData['colordata']
            elif ColorData['colortype'] == DOTColorTypes.XWinName:
                Color = ColorData['colordata']
            else:
                print "Unknown color type", ColorData['colortype']
                Color = "white"
                
            OutFile.write('\tTask%d [shape=ellipse,width=.75,height=.75,style=filled,label="#%d\\n%s",color="%s"]\n' %\
                        (i, i, Name, Color) )
    
        # write edges
        for i in xrange(self.NTasks):
            if i not in self.TaskEdges: continue
            for j in xrange(self.NTasks):
                if j not in self.TaskEdges[i]: continue
                if self.TaskEdges[i][j]:
                    
                    ColorData = self.EdgeColor
                    if ColorData['colortype'] == DOTColorTypes.HSB:
                        Color = "%.3f %.3f %.3f" % ColorData['colordata']
                    elif ColorData['colortype'] == DOTColorTypes.RGB:
                        Color = "#%2.2x%2.2x%2.2x" % ColorData['colordata']
                    elif ColorData['colortype'] == DOTColorTypes.XWinName:
                        Color = ColorData['colordata']
                    else:
                        print "Unknown color type", ColorData['colortype']
                        Color = "black"
                    
                    #OutFile.write('\tTask%d -> Task%d [style=dotted,color="%.3f %.3f %.3f"]\n' % \
                    OutFile.write('\tTask%d -> Task%d [color="%s"]\n' % \
                                 ( i, j, Color ) )
                    
                        
        OutFile.write('}\n')
        OutFile.close()
        
class RandomGraphType:
    FromSTG = 0
    TaskSameProb = 1
    TaskSamePred = 2
    LayerSameProb = 3
    LayerSamePred = 4
    FromTextGraph = 5
    LastType = 5
    Names = { 'FromSTG' : 0,
              'TaskSameProb' : 1,
              'TaskSamePred' : 2,
              'LayerSameProb' : 3,
              'LayerSamePred' : 4,
              'FromTextGraph' : 5}
    
def getRandomGraphTypeName( Type ):
    if Type == RandomGraphType.FromSTG:
        return "RandomGraphType.FromSTG : graph generated from STG file"
    elif Type == RandomGraphType.FromTextGraph:
        return "RandomGraphType.FromTextGraph : graph generated from text/graph file"
    elif Type == RandomGraphType.TaskSameProb:
        return "RandomGraphType.TaskSameProb : graph generated using the STG SameProb method"
    elif Type == RandomGraphType.TaskSamePred:
        return "RandomGraphType.TaskSamePred : graph generated using the STG SamePred method"
    elif Type == RandomGraphType.LayerSameProb:
        return "RandomGraphType.LayerSameProb : graph generated using the STG LayerProb method"
    elif Type == RandomGraphType.LayerSamePred:
        return "RandomGraphType.LayerSamePred : graph generated using the STG LayerPred method"
    return None

def generateRandomGraph( KeyValueDic ):
    
    try:
        keys = ['GraphID', 'GraphType', 'GraphData', 'GraphName', 'STGFileNamesList', 'TextGraphFileNamesList', 'OutDir', 'OutFileName']
        for kw in keys:
            temp = KeyValueDic[kw]
    except:
        print "Could not find keyword", kw, "quitting!"
    
    GraphID   = KeyValueDic['GraphID']
    GraphType = KeyValueDic['GraphType']
    GraphData = KeyValueDic['GraphData']
    STGFileNamesList = KeyValueDic['STGFileNamesList']
    TextGraphFileNamesList = KeyValueDic['TextGraphFileNamesList']
    OutDir = KeyValueDic['OutDir']
    OutFileName = KeyValueDic['OutFileName']
    GraphName = KeyValueDic['GraphName']
    
    print 'Generating a', getRandomGraphTypeName(GraphType), "graph"
    
    OneRandom = AIRandomUtils.AIRandom()
    
    OneTaskGraph = TaskGraph(GraphID, GraphName)
    if GraphType == RandomGraphType.FromSTG:
        STGName = OneRandom.getRandomListElement(STGFileNamesList)
        OneTaskGraph.loadFromSTG( STGName )
        #OneTaskGraph.removeLastTask()
        OneTaskGraph.autosetPredSuccLeaf()
     
    elif GraphType == RandomGraphType.FromTextGraph:
        TextGraphName = OneRandom.getRandomListElement(TextGraphFileNamesList)
        OneTaskGraph.loadFromTextGraph( TextGraphName )
        #OneTaskGraph.removeLastTask()
        OneTaskGraph.autosetPredSuccLeaf()
        
    elif GraphType == RandomGraphType.TaskSameProb:
        OneTaskGraph.generateGraphSameProb( GraphData['NTasks'], GraphData['p'] )
        OneTaskGraph.autosetPredSuccLeaf()
        OneTaskGraph.autosetUniqueStartEnd()
        
    elif GraphType == RandomGraphType.TaskSamePred:
        OneTaskGraph.generateGraphSamePred( GraphData['NTasks'], GraphData['NConnect'] )
        OneTaskGraph.autosetPredSuccLeaf()
        OneTaskGraph.autosetUniqueStartEnd()
        
    elif GraphType == RandomGraphType.LayerSameProb:
        OneTaskGraph.generateGraphLayerProb( GraphData['NLayers'], GraphData['NLayerTasks'], GraphData['p'] )
        OneTaskGraph.autosetPredSuccLeaf()
        OneTaskGraph.autosetUniqueStartEnd()
        
    elif GraphType == RandomGraphType.LayerSamePred:
        OneTaskGraph.generateGraphLayerPred( GraphData['NLayers'], GraphData['NLayerTasks'], GraphData['NConnect'] )
        OneTaskGraph.autosetPredSuccLeaf()
        OneTaskGraph.autosetUniqueStartEnd()
        
    else:
        raise Exception, "generateRandomGraph got wrong type of graph type: " + str(GraphType)
        
    #OneTaskGraph.printEdges()
    OneTaskGraph.autosetPredSuccLeaf()
    OneTaskGraph.doTopologicalSort()
##    OneTaskGraph.assignRandomDataToAllTasks([
##        {'name':'a', 'colordata':(0.628,0.227,1.000),'colortype':DOTColorTypes.HSB}, 
##        {'name':'b', 'colordata':(0.603,0.258,1.000),'colortype':DOTColorTypes.HSB}, 
##        {'name':'c', 'colordata':(0.590,0.273,1.000),'colortype':DOTColorTypes.HSB}, 
##        {'name':'d', 'colordata':(0.355,0.563,1.000),'colortype':DOTColorTypes.HSB}, 
##        {'name':'e', 'colordata':(0.201,0.753,1.000),'colortype':DOTColorTypes.HSB}, 
##        {'name':'f', 'colordata':(0.578,0.289,1.000),'colortype':DOTColorTypes.HSB}, 
##        {'name':'g', 'colordata':(0.408,0.498,1.000),'colortype':DOTColorTypes.HSB}, 
##        {'name':'h', 'colordata':(128,128,128),'colortype':DOTColorTypes.RGB}, 
##        {'name':'i', 'colordata':(128,128,128),'colortype':DOTColorTypes.RGB}, 
##        {'name':'j', 'colordata':'red','colortype':DOTColorTypes.XWinName}, 
##        {'name':'k', 'colordata':(  0,  0,255),'colortype':DOTColorTypes.RGB} 
##        ])
    OneTaskGraph.assignRandomDataToAllTasks([{'name':'node', 'colordata':(0.628,0.227,1.000),'colortype':DOTColorTypes.HSB}])
    OneTaskGraph.setEdgeColor({'colordata':(0.649,0.701,0.701),'colortype':DOTColorTypes.HSB})
    
    if OutFileName is not None:
        OneTaskGraph.saveToDOT(os.path.join( OutDir, OutFileName ), 
                               {'GraphName':GraphID, 'Comment':GraphName})
        
    return OneTaskGraph
    
def readAllParams( WLUnit ):
    
    Params = {}
    for ParamCategory in RandomGraphType.Names:
        Params[ParamCategory] = {}
        
    try:
        TaskSameProb_NTasksWithWeights = \
            AIParseUtils.readIntWithWeightsList( 
                WLUnit['otherinfo']['Params.TaskSameProb.NTasksWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['TaskSameProb']['NTasksWithWeights'] = TaskSameProb_NTasksWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
        
    try:
        TaskSameProb_pWithWeights = \
            AIParseUtils.readFloatWithWeightsList( 
                WLUnit['otherinfo']['Params.TaskSameProb.pWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['TaskSameProb']['pWithWeights'] = TaskSameProb_pWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
        
    try:
        TaskSamePred_NTasksWithWeights = \
            AIParseUtils.readIntWithWeightsList( 
                WLUnit['otherinfo']['Params.TaskSamePred.NTasksWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['TaskSamePred']['NTasksWithWeights'] = TaskSamePred_NTasksWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
        
    try:
        TaskSamePred_NTasksWithWeights = \
            AIParseUtils.readIntWithWeightsList( 
                WLUnit['otherinfo']['Params.TaskSamePred.NConnectWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['TaskSamePred']['NConnectWithWeights'] = TaskSamePred_NTasksWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
        
    try:
        LayerSameProb_NLayersWithWeights = \
            AIParseUtils.readTupleWithWeightsList( 
                WLUnit['otherinfo']['Params.LayerSameProb.NLayersWithWeights'],
                TupleType = AIParseUtils.TupleValues.INT_VALUE, 
                DefaultWeight = 1.0, ItemSeparator = ';', TupleItemSeparator=',' 
                )
        Params['LayerSameProb']['NLayersWithWeights'] = LayerSameProb_NLayersWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
        
    try:
        LayerSameProb_NLayerTasksWithWeights = \
            AIParseUtils.readTupleWithWeightsList( 
                WLUnit['otherinfo']['Params.LayerSameProb.NLayerTasksWithWeights'],
                TupleType = AIParseUtils.TupleValues.INT_VALUE, 
                DefaultWeight = 1.0, ItemSeparator = ';', TupleItemSeparator=',' 
                )
        Params['LayerSameProb']['NLayerTasksWithWeights'] = LayerSameProb_NLayerTasksWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
        
    try:
        LayerSameProb_pWithWeights = \
            AIParseUtils.readFloatWithWeightsList( 
                WLUnit['otherinfo']['Params.LayerSameProb.pWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['LayerSameProb']['pWithWeights'] = LayerSameProb_pWithWeights
    except:
        ##
        print traceback.print_exc()
        pass

    try:
        LayerSamePred_NLayersWithWeights = \
            AIParseUtils.readTupleWithWeightsList( 
                WLUnit['otherinfo']['Params.LayerSamePred.NLayersWithWeights'],
                TupleType = AIParseUtils.TupleValues.INT_VALUE, 
                DefaultWeight = 1.0, ItemSeparator = ';', TupleItemSeparator=',' 
                )
        Params['LayerSamePred']['NLayersWithWeights'] = LayerSamePred_NLayersWithWeights
    except:
        ##
        print traceback.print_exc()
        pass
        
    try:
        LayerSamePred_NLayerTasksWithWeights = \
            AIParseUtils.readTupleWithWeightsList( 
                WLUnit['otherinfo']['Params.LayerSamePred.NLayerTasksWithWeights'],
                TupleType = AIParseUtils.TupleValues.INT_VALUE, 
                DefaultWeight = 1.0, ItemSeparator = ';', TupleItemSeparator=',' 
                )
        Params['LayerSamePred']['NLayerTasksWithWeights'] = LayerSamePred_NLayerTasksWithWeights
    except:
        ##
        print traceback.print_exc()
        pass

    try:
        LayerSamePred_NTasksWithWeights = \
            AIParseUtils.readIntWithWeightsList( 
                WLUnit['otherinfo']['Params.LayerSamePred.NConnectWithWeights'],
                DefaultWeight = 1.0, ItemSeparator = ',' 
                )
        Params['LayerSamePred']['NConnectWithWeights'] = LayerSamePred_NTasksWithWeights
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
    
    TextGraphFileNamesList = []
    try:
        TextGraphFilters = WLUnit['otherinfo']['TextGraphFiles']
        TextGraphFilterList = TextGraphFilters.split(',')
        for Filter in TextGraphFilterList:
            CurrentTextGraphList = glob.glob(Filter)
            for TextGraphFileName in CurrentTextGraphList:
                if TextGraphFileName not in TextGraphFileNamesList:
                    TextGraphFileNamesList.append(TextGraphFileName)
                    #print "#### appending: " + TextGraphFileName
    except:
        TextGraphFileNamesList = []
        #print "### TextGraph exception"
        #print traceback.print_exc()
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
        GraphType = RandomGraphType.Names[GraphType]
        #print ">>>", "Selected", GraphType, "from", GraphTypesWithWeights
        
        
        GraphName = getRandomGraphTypeName(GraphType)
        GraphData = {}
        if GraphType == RandomGraphType.FromSTG:
            pass            
        elif GraphType == RandomGraphType.TaskSameProb:
            try:
                GraphData['NTasks'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['TaskSameProb']['NTasksWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
                GraphData['p'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['TaskSameProb']['pWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
            except Exception, e:
                print "Could not find a definition for", getRandomGraphTypeName(GraphType), "parameter", e
                continue
            GraphName = GraphName + ' NTasks=' + str(GraphData['NTasks']) + ' p=' + str(GraphData['p'])
        elif GraphType == RandomGraphType.TaskSamePred:
            try:
                GraphData['NTasks'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['TaskSamePred']['NTasksWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
                
                GraphData['NConnect'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['TaskSamePred']['NConnectWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
            except Exception, e:
                print "Could not find a definition for", getRandomGraphTypeName(GraphType), "parameter", e
                continue
            GraphName = GraphName + ' NTasks=' + str(GraphData['NTasks']) + ' NConnect=' + str(GraphData['NConnect'])
        elif GraphType == RandomGraphType.LayerSameProb:
            try:
                GraphData['NLayers'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['LayerSameProb']['NLayersWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
                GraphData['NLayerTasks'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['LayerSameProb']['NLayerTasksWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
                GraphData['p'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['LayerSameProb']['pWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
            except Exception, e:
                print "Could not find a definition for", getRandomGraphTypeName(GraphType), "parameter", e
                continue
            GraphName = GraphName + ' NLayers=' + str(GraphData['NLayers']) + ' NLayerTasks=' + str(GraphData['NLayerTasks']) + ' p=' + str(GraphData['p'])
        elif GraphType == RandomGraphType.LayerSamePred:
            try:
                GraphData['NLayers'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['LayerSamePred']['NLayersWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
                GraphData['NLayerTasks'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['LayerSamePred']['NLayerTasksWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            ) 
                GraphData['NConnect'] = \
                        AIRandomUtils.getRandomWeightedListElement(
                            Params['LayerSamePred']['NConnectWithWeights'],
                            ValuesKey = AIParseUtils.VALUES, TotalWeightKey = AIParseUtils.TOTAL_WEIGHT 
                            )
            except Exception, e:
                print "Could not find a definition for", getRandomGraphTypeName(GraphType), "parameter", e
                continue
            GraphName = GraphName + ' NLayers=' + str(GraphData['NLayers']) + ' NLayerTasks=' + str(GraphData['NLayerTasks']) + ' NConnect=' + str(GraphData['NConnect'])
        
        #--- generate structure
        CurrentData = {}
        CurrentData['GraphID'] = GraphID
        CurrentData['GraphName'] = GraphName
        CurrentData['GraphType'] = GraphType
        CurrentData['GraphData'] = GraphData
        CurrentData['STGFileNamesList'] = STGFileNamesList
        CurrentData['TextGraphFileNamesList'] = TextGraphFileNamesList
        CurrentData['OutDir'] = None
        CurrentData['OutFileName'] = None
        ListOfGraphs.append( generateRandomGraph(CurrentData) )
        
        #-- ack generated structure
        index = index + 1 
        
        #lumpy.class_diagram()
    
    return ListOfGraphs
  
if __name__ == "__main__":
    
    pass
    
