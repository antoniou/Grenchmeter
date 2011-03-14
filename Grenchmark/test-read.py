#!/usr/bin/python

""" """


__proggy = "wl-parse";
__rev = "0.15";
__proggy_stamp__ = "%s v%s" % (__proggy, __rev);
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'wl-parse.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:14:45 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python"  

#---------------------------------------------------
# Log:
# 15/09/2005 A.I. 0.16 Added the nobackground flag, so that threads could
#                      be blocked with long running jobs
# 16/08/2005 A.I. 0.15 Changed the time to be a float
# 08/08/2005 A.I. 0.13 Fixed minor bug: when the file was not valid, 
#                      the error was incorrectly displayed
# 08/08/2005 A.I. 0.1  Started this app
#---------------------------------------------------


import sys, string
import getopt
import os
from xml.sax import saxlib, saxexts
import time
import sys
if "utils" not in sys.path: sys.path.append("utils")
import AIStorageUtils 
import AISystemUtil
import ASPNThreadPool
import WLDocHandlers

ListOfApps = {}

def printWorkload( XMLhandler ):
    
    DictionaryOfApps = XMLhandler.getDictionaryOfApplications()
        
    ListOfApps = AIStorageUtils.dict_sortbyvalue_dict( DictionaryOfApps, 'jdf', 
                                                       AIStorageUtils.SORT_TYPE_STRING, 
                                                       AIStorageUtils.SORT_ASCENDING )
    NTotalJobs = len( ListOfApps )
    print "Found", NTotalJobs, "apps. Sorting...done."

    for (id, App) in ListOfApps:
        print id, App['jdf'],
        if 'dependsOn' in App:
            print 'dependsOn=', App['dependsOn']
        else:
            print
        
    print "--Full description----------"
        
    for (id, App) in ListOfApps:
        print id, App
        
def usage(progname):
    print __doc__ % vars() 

def version():
    print "Version: ", __version__
    print "Date: ", __date__
    print __copyright__, "(", __email__, ")"

def main(argv):                  

    try:                                
        opts, args = getopt.getopt(argv, "ht:", ["help", "threads=", "version", "nosubmit", "nobackground", "onefile"])
    except getopt.GetoptError:
        print "Error while converting options: unknown option(s) encountered.\n\n"
        usage(os.path.basename(sys.argv[0]))
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            usage(os.path.basename(sys.argv[0]))
            sys.exit()
        elif opt in ["--version"]:
            version()
            sys.exit()
        else:
            print "Unknown parameter", opt
    
    if len(args) < 1:
        print "Error: No workload file given.\n\n"
        usage(os.path.basename(sys.argv[0]))
        sys.exit(3)
        
    WorkloadFileName = args[0];
    if not os.path.isfile( WorkloadFileName ):
        print "Error: %s is not a valid file.\n\n" % WorkloadFileName
        usage(os.path.basename(sys.argv[0]))
        sys.exit(1)
        
    handlerXML = WLDocHandlers.readWorkloadSubmitFile( WorkloadFileName )
    printWorkload( handlerXML )


if __name__ == "__main__":

    main(sys.argv[1:]) 
    
    
