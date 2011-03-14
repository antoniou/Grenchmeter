#! /usr/bin/env python

__author__ = 'Alexandru Iosup'
__email__ = 'A.Iosup at ewi.tudelft.nl'
__file__ = 'AISystemUtil.py'
__version__ = '1.0'
#__name__ = 'Gnutella Crawler Test' 
#! /usr/bin/env python

__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'AISystemUtil.py';
__version__ = '1.0';
#__name__ = 'System Utils'
 
import sys
import os 

# Brent Burley's recipe: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52296
# executes a command and returns its output
# the error stream is redirected to /dev/null -> gets lost
def getCommandOutput2(command, hide_errors = 0):
    if hide_errors == 0:
        child = os.popen(command)
    else:
        child = os.popen(command + ' 2> /dev/null')
    data = child.read()
    err = child.close()
    if err:
        raise RuntimeError, '%s failed w/ exit code %d' % (command, err)
    return data
 
if __name__ == '__main__': 
    
    if ( len( sys.argv ) == 2 ) :
        Command = sys.argv[1];
    else:
        Command = "dir"; 
        
    data = getCommandOutput2( Command );
    print data;
    