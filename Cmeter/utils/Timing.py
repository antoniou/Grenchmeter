"""
A module that helps to inject time profiling code
in other modules to measures actual execution times
of blocks of code.

"""

__author__ = "Anand B. Pillai"
__version__ = "0.1"

import time

def timeprofile():
    """ A factory function to return an instance of TimeProfiler """

    return TimeProfiler()

class TimeProfiler:
    """ A utility class for profiling execution time for code """
    
    def __init__(self):
        self.timedict = {}

    def mark(self, slot=''):
        
        self.timedict[slot] = time.time()

    def unmark(self, slot=''):
        if self.timedict.has_key(slot):
            del self.timedict[slot]

    def getValue(self, slot):
        return self.timedict[slot]
    
    def elapsed(self, slot=''):
        """ Get the time difference between now and a previous
        time slot named 'slot' """
        # Note: 'slot' has to be marked previously
        self.timedict[slot] = (time.time() - self.timedict.get(slot))#*1000 # millis
        return self.timedict[slot]

    def dumpTimeDict(self):
        for key, value in self.timedict.items():
            print (key + " took %f milliseconds.") % (value*1000)
