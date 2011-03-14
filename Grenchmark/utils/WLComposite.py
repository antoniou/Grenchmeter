#!/usr/bin/python

""" Grenchmark composite applications main functions """

__proggy = "Grenchmark/WLComposite";
__rev = "0.11";
__proggy_stamp__ = "%s v%s" % (__proggy, __rev);
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'WLComposite.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:19:35 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python" 

#---------------------------------------------------
# Log:
# 03/11/2005 A.I. 0.1  Started this app
#---------------------------------------------------

import sys
import traceback
import os.path
from time import time, gmtime, strftime 
if "utils" not in sys.path:sys.path.append("utils")
import WLCompositeGenGraphs
import WLCompositeGenBPatterns


class CompositeTypes:
    # 1. each Name maps to a composite generator module
    # 2. the generator module has a generateRandomStructures function, which
    #    calls the generator module's specific generator function
    #    (the generator's module wrapper function)
    # 3. each specific generator function returns an object which presents
    #    the following interface:
    #  o getNNodes: returns the number of nodes in this composite structure 
    #  o getMaxLevels(self):
    #           returns the maximum levels in a topological sort of the nodes 
    #           in this composite structure 
    #  o getNodeDepth(self, nodeid): returns the node's depth or -1
    #  o getNodeData(self, nodeid): returns the node's data or None
    #  o setNodeData(self, nodeid, data): sets the node's data
    #  o getNodeSuccessors(self, nodeid): 
    #           returns a list of successors of the given node, or []
    #  o getNodePredecessors(self, nodeid):
    #           returns a list of predecessors of the given node, or []
    CompositeGens = { 'DAG': WLCompositeGenGraphs, 'BPatternDAG': WLCompositeGenBPatterns }
    
    def generateComposite( self, WLOutDir, WLUnitID, WLUnit, SubmitDurationMS, bGenerateRandom ):
        
        #--- verify that this composite generator is supported
        if 'CompositionType' not in WLUnit:
            print "No CompositionType specified in OtherInfo"
            print "Please add an entry CompositionType=Value in OtherInfo; possible values are", self.CompositeGens.keys()
            return None
            
        if WLUnit['CompositionType'] not in self.CompositeGens:
            print "Illegal CompositionType value ", '('+WLUnit['CompositionType']+')', "; possible values are", self.CompositeGens.keys()
            return None
            
        CompositeStructuresList = []
        try:
            #--- get the generator's module wrapper function
            CompositeGen = self.CompositeGens[WLUnit['CompositionType']].generateRandomStructures
            
            #--- generate all composite structures
            index = 0
            maxIndex = WLUnit['multiplicity'] # number of structures to generate
            while index < maxIndex:
                CurrentWLUnitID = "%s-%d" % (WLUnitID, index)
                OneGenCompositeStructureList = CompositeGen(WLOutDir, CurrentWLUnitID, WLUnit, SubmitDurationMS)
                for CompositeStructure in OneGenCompositeStructureList:
                    CompositeStructuresList.append(CompositeStructure)
                index = index + 1           
            
        except Exception, e:
            print "The generator for unit", WLUnit['id'], "/ AppType=", WLUnit['apptype'], "is incorrect...skipping unit"
            print "\tAn error occured while generating structure", CurrentWLUnitID
            print "\tReason:", e
            print "TRACEBACK::COMPOSITE::GENERATOR>>>\n", traceback.print_exc()
            print "\n<<<\n"
            CompositeStructuresList = []
        
        return CompositeStructuresList
        

