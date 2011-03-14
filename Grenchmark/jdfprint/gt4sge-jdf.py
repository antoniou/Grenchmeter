import os.path

import sys
if "utils" not in sys.path:
    sys.path.append("utils")
import WLDocHandlers

JDFGenerator="""
    Name=gt4sge-jdf
    Info=Print to GT4 WS-GRAM RSL file (http://www.globus.org)
    Author=C. Stratan
    Contact=email:corina@cs.pub.ro
    Copyright=copyright (C) 2005 Alexandru Iosup
    """

def writeOneStringValue( KeyName, DataName, Component, OutFile ):
    #if Component is None:
    #    print ">>>>>>>>>> Empty Component"
    #    return
    if (DataName in Component.keys()) and (len(str(Component[DataName])) > 0):
        OutFile.write( "<%s>%s</%s> \n" % (KeyName, str(Component[DataName]), KeyName) )

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

    print "STATUS! Write GT4 RSL file", OutFileName,
    OutFile = open( OutFileName, "w" )
    index = 0
    #if ListOfComponents is None:
    #    print ">>>>>>>>>> Empty ListOfComponents"
    #    return

    nComponents = len(ListOfComponents)
    for Component in ListOfComponents:
        #-- write unit component
        OutFile.write('<job> \n')
        writeOneStringValue( 'executable', 'executable', Component, OutFile )
        for sserArg in Component['arguments']:
            #OutFile.write(sserArg + " ")
            OutFile.write( "<argument>%s</argument> \n" % sserArg )
        #OutFile.write('\n')
        #writeOneStringValue( 'arguments', 'arguments', Component, OutFile )
        writeOneStringValue( 'stdout', 'stdout', Component, OutFile )
        writeOneStringValue( 'stderr', 'stderr', Component, OutFile )
        OutFile.write('</job> \n')
        
        #-- ack component
        index = index + 1

    OutFile.close()
    print "...done"