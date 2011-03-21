"""
A module with commonly used statistical tools.
"""

__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at tudelft.nl';
__file__ = 'AIStatistics.py';
#__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:19:35 $"
__copyright__ = "Copyright (c) 2006 Alexandru IOSUP"
__license__ = "Python"  

import math
import sys

class CStats:
    """ a class for quickly summarizing comparable (e.g., numeric) data """
    def __init__(self, bIsNumeric = True, bKeepValues = True, bAutoComputeStats = True):
        self.Min = None
        self.Max = None
        self.Sum = 0
        self.SumOfSquares = 0
        self.Avg = None        # arithmetic mean
        self.StdDev = None     # standard deviation
        self.COV = None     # coefficient of variation
        self.NItems = 0
        self.Values = []
        self.bIsNumeric = bIsNumeric
        self.bKeepValues = bKeepValues
        self.bAutoComputeStats = bAutoComputeStats
        
    def addValue(self, Value):
        self.NItems += 1
        if self.bKeepValues: self.Values.append(Value)
        if self.Min is None or self.Min > Value: self.Min = Value
        if self.Max is None or self.Max < Value: self.Max = Value
        if self.bIsNumeric:
            self.Sum += Value
            self.SumOfSquares += Value * Value
            if self.bAutoComputeStats:
                self.Avg = float(self.Sum) / self.NItems 
                if self.NItems -1 > 0:
                    Diff = (self.NItems * self.SumOfSquares - self.Sum * self.Sum)
                    self.StdDev = math.sqrt( Diff / (self.NItems * (self.NItems - 1)) )
                else:
                    self.StdDev = 0.0
                if abs(self.Avg) > 0.0001:
                    self.COV = self.StdDev / self.Avg
                else:
                    self.COV = 0.0
                
    def doComputeStats( self ):
        if self.NItems > 0:
            self.Avg = float(self.Sum) / self.NItems 
            if self.NItems -1 > 0:
                Diff = (self.NItems * self.SumOfSquares - self.Sum * self.Sum)
                if Diff < 0.0: Diff = 0.0 # adding small figures may lead to a diff ~0.0..1)
                self.StdDev = math.sqrt( Diff / (self.NItems * (self.NItems - 1)) )
            else:
                self.StdDev = 0.0
            if abs(self.Avg) > 0.0001:
                self.COV = self.StdDev / self.Avg
            else:
                self.COV = 0.0
        else:
    		self.Min = 0
    		self.Max = 0
    		self.Avg = 0
    		self.StdDev = 0
    		self.COV = 0
    		self.Sum = 0
    
    def dump(self, fp):
        fp.write("NItems =%30.3f\n" % (float(self.NItems)))
        fp.write("Sum    =%30.3f\n" % (float(self.Sum)))
        fp.write("Avg    =%30.3f\n" % (float(self.Sum/self.NItems)))
        fp.write("Sum^2  =%30.3f\n" % (float(self.Sum*self.Sum)))
        fp.write("SumSq  =%30.3f\n" % (float(self.SumOfSquares)))
        fp.write("N*SumSq=%30.3f\n" % (float(self.NItems * self.SumOfSquares)))
        fp.write("Std-dev =%30.3f\n" % self.StdDev)
        fp.write("COV =%30.3f\n" % self.COV)
        fp.write("Diff   =%30.3f\n" % (float(self.NItems * self.SumOfSquares - self.Sum * self.Sum)))
		
            
class CHistogram:
    """ a class for creating histograms of comparable (e.g., numeric) data """
    def __init__(self, bIsNumeric = True, bKeepValues = True):
        self.Stats = CStats(bIsNumeric, bKeepValues, bAutoComputeStats = False)
        self.NItems = 0
        self.Values = {}
        self.MaxHeight = 0
        self.CDF = None
        
    def addValue(self, Value):
        self.NItems += 1 
        Value = int(Value)
        #-- map value to histogram
        if Value not in self.Values: self.Values[Value] = 0
        self.Values[Value] += 1
        if self.MaxHeight < self.Values[Value]: self.MaxHeight = self.Values[Value]
        #-- create value statistics
        self.Stats.addValue(Value)
        
    def getMinValue(self):
        return self.Stats.Min
        
    def getMaxValue(self):
        return self.Stats.Max
        
    def computeCDF(self, StepSize = 1, bMustRecompute = True):
        if bMustRecompute or self.CDF is None:
            self.Stats.doComputeStats()
            self.CDF = {}
            if self.NItems > 0:
                Counter = 0
                for Value in xrange(self.Stats.Min, self.Stats.Max + 1, StepSize):
                    if Value in self.Values:
                        Counter += self.Values[Value]
                    self.CDF[Value] = float(Counter) / self.NItems
        return self.CDF

# What is this for????
#import Gnuplot, Gnuplot.funcutils
#hist = CHistogram()
#plotData=[]
#for i in range(0,100):
#    data=[]
#    data.append(i)
#    val = float(0.25*math.exp(-1*0.25*i)) 
#    data.append(val)
#    hist.addValue(val)
#    plotData.append(data)
#
#cdf = hist.computeCDF()
#for k,v in cdf.items():
#    print "%d -> %d" % (k,v)
