import os.path

import sys
if "utils" not in sys.path:
    sys.path.append("utils")
import WLDocHandlers

JDFGenerator="""
    Name=condor-jdf
    Info=Print to Condor Job Description File (http://cs.wisc.edu/condor)
    Author=C. Stratan
    Contact=email:corina@cs.pub.ro
    Copyright=copyright (C) 2005 Alexandru Iosup
    """

def writeOneStringValue( KeyName, DataName, Component, OutFile ):
    #if Component is None:
    #    print ">>>>>>>>>> Empty Component"
    #    return
    if (DataName in Component.keys()) and (len(str(Component[DataName])) > 0):
        OutFile.write( "%s = %s \n" % (KeyName, str(Component[DataName])) )

def generateJDF( OutFileName, ListOfComponents ):
    """
    Generate a Condor Job Description File for a given workload unit.

    In:
        OutFileName      -- the target file for writing the JDF of this workload unit
        ListOfComponents -- a list of components
                            Each component is a dictionary and has defined at
                            least the following keys:
                            id, executable, count, description, directory,
                            maxWallTime, arguments, env, stagein, stageout,
                            stdout, stderr
    """

    print "STATUS! Write Condor JDF file", OutFileName,
    OutFile = open( OutFileName, "w" )
    index = 0
    #if ListOfComponents is None:
    #    print ">>>>>>>>>> Empty ListOfComponents"
    #    return

    nComponents = len(ListOfComponents)
    for Component in ListOfComponents:
        #-- write unit component
        writeOneStringValue( 'executable', 'executable', Component, OutFile )
        OutFile.write('arguments = ')
        for sserArg in Component['arguments']:
            OutFile.write(sserArg + " ")
        OutFile.write('\n')
        #writeOneStringValue( 'arguments', 'arguments', Component, OutFile )
        writeOneStringValue( 'output', 'stdout', Component, OutFile )
        writeOneStringValue( 'error', 'stderr', Component, OutFile )
        writeOneStringValue( 'log', 'logfile', Component, OutFile )
        
        #TODO add a line for the log file!
        
        OutFile.write( 'universe = vanilla\n' )
        OutFile.write( 'should_transfer_files = YES\n' )
        OutFile.write( 'when_to_transfer_output = ON_EXIT\n' )
        OutFile.write( 'notification = NEVER\n' )
        OutFile.write( 'queue\n' )

        #-- ack component
        index = index + 1

    OutFile.close()
    print "...done"