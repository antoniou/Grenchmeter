import os.path

import sys
if "utils" not in sys.path:
    sys.path.append("utils")
import WLDocHandlers

JDFGenerator="""
    Name=sge-jdf
    Info=Print to SGE Job Description File (http://cs.wisc.edu/condor)
    Author=C. Stratan
    Contact=email:corina@cs.pub.ro
    Copyright=copyright (C) 2005 Alexandru Iosup
    """

def writeOneStringValue( KeyName, DataName, Component, OutFile ):
    if (DataName in Component.keys()) and (len(str(Component[DataName])) > 0):
        OutFile.write( "%s = %s \n" % (KeyName, str(Component[DataName])) )

def generateJDF( OutFileName, ListOfComponents ):
    """
    Generate a SGE Job Description File for a given workload unit.

    In:
        OutFileName      -- the target file for writing the JDF of this workload unit
        ListOfComponents -- a list of components
                            Each component is a dictionary and has defined at
                            least the following keys:
                            id, executable, count, description, directory,
                            maxWallTime, arguments, env, stagein, stageout,
                            stdout, stderr
    """

    print "STATUS! Write SGE JDF file", OutFileName,
    OutFile = open( OutFileName, "w" )
    index = 0
    #if ListOfComponents is None:
    #    print ">>>>>>>>>> Empty ListOfComponents"
    #    return

    nComponents = len(ListOfComponents)
    for Component in ListOfComponents:
        #-- write unit component
        OutFile.write('#!/bin/bash\n')
        OutFile.write('#$ -S /bin/bash\n')
        
        OutFile.write('#$ -o %s -e %s \n' % (Component['stdout'], Component['stderr']))
        OutFile.write(Component['executable'] + ' ')
        for sserArg in Component['arguments']:
            OutFile.write(sserArg + ' ')
        OutFile.write('\n')

        #-- ack component
        index = index + 1

    OutFile.close()
    print "...done"