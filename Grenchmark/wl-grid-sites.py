#!/usr/bin/python

"""
NAME

    wl-grid-sites -- print the list of defined grid sites

SYNOPSIS
    %(progname)s [<Grid Sites file name>]

DESCRIPTION
    wl-gen-simple simply lists the list of defined grid sites, taken 
    from the input file given as parameter, or from grid-sites.xml, if
    no parameter is given.
             
OPTIONS:
    Arguments:
    --help 
      Print a summary of the wl-gen-simple options and exit.
    
    --version
      Display wl-gen-simple version and copyright.
    

SAMPLE RUN:

    $ ./wl-grid-sites.py
    
"""

__proggy = "wl-grid-sites";
__rev = "0.1";
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
# 08/08/2005 A.I. 0.1  Started this app
#---------------------------------------------------

import sys, string
import getopt
import os
import time

#---Import files from the utils directory
sys.path.append("utils")
import AIStorageUtils 
import WLDocHandlers


def usage(progname):
    print __doc__ % vars() 

def version():
    print "Version: ", __version__
    print "Date: ", __date__
    print __copyright__, "(", __email__, ")"

def main(argv):                  

    try:                                
        opts, args = getopt.getopt(argv, "h", ["help", "version"])
    except getopt.GetoptError:
        print "Error while converting options: unknown option(s) encountered.\n\n"
        usage(os.path.basename(sys.argv[0]))
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(os.path.basename(sys.argv[0]))
            sys.exit()
        elif opt in ["--version"]:
            version()
            sys.exit()
        else:
            print "Unknown parameter", opt
    
    if len(args) < 1:
        #print "Error: No sites file given.\n\n"
        #usage(os.path.basename(sys.argv[0]))
        #sys.exit(3)
        SitesFileName = "grid-sites.xml"
    else:
        SitesFileName = args[0];
        
    if not os.path.isfile( SitesFileName ):
        if os.path.exists( SitesFileName ):
            print "\n\n****\nError: %s is not a file!\n****\n" % SitesFileName
        else:
            print "\n\n****\nError: %s does not exist!\n****\n" % SitesFileName
        usage(os.path.basename(sys.argv[0]))
        sys.exit(1)
        
    #---Read a sites file
    #print "%s Parsing sites file %s" % \
    #      ( time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time())), SitesFileName )
    handlerXML = WLDocHandlers.readSiteFile(SitesFileName)
    #print "%s Sites file processed, proceeding to submission"  % \
    #      time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))  
    
    DictionaryOfSites = handlerXML.getDictionaryOfSites()
    ListOfSites = AIStorageUtils.dict_sortbykey( DictionaryOfSites, AIStorageUtils.SORT_DESCENDING )
    for (id, Site) in ListOfSites: 
        print id, Site['location'], Site['machines']
    print
    #fs4 fs4.das2.phys.uu.nl 32
    #fs3 fs3.das2.ewi.tudelft.nl 32
    #fs2 fs2.das2.nikhef.nl 32
    #fs1 fs1.das2.liacs.nl 32
    #fs0 fs0.das2.cs.vu.nl 72
    
    #---Generate a sites file
    ##WLDocHandlers.writeSiteFile( "test.xml", DictionaryOfSites )
    
    #---Check if sites are in the list
    ##CheckNames = ['fs3', 'fake']
    ##for Name in CheckNames:
    ##    print "'" + Name + "'", 
    ##    if Name not in DictionaryOfSites.keys():
    ##        print "not", 
    ##    print "found!"
    ###'fs3' found!
    ###'fake' not found!
        
    #print "%s All done" % time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))

if __name__ == "__main__":

    main(sys.argv[1:]) 
    
    
    
