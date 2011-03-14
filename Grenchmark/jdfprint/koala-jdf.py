
import os.path

import sys
if "utils" not in sys.path:
    sys.path.append("utils")
import WLDocHandlers

JDFGenerator="""
    Name=koala-jdf
    Info=Print to KOALA Job Description File (http://www.st.ewi.tudelft.nl/koala/)
    Author=A. Iosup
    Contact=email:A.Iosup@ewi.tudelft.nl
    Copyright=copyright (C) 2005 Alexandru Iosup
    """
    
def writeOneStringValue( KeyName, DataName, Component, OutFile ):
    #if Component is None:
    #    print ">>>>>>>>>> Empty Component"
    #    return 
    if (DataName in Component.keys()) and (len(str(Component[DataName])) > 0):
        OutFile.write( "   ( %s = \"%s\" ) \n" % (KeyName, str(Component[DataName])) )
            
def writeOneTuples2List( KeyName, DataName, Component, OutFile ):
    if (DataName in Component.keys()) and (len(Component[DataName]) > 0):
        OutFile.write( "   ( %s = \n" % KeyName )
        for (Name, Value) in Component[DataName]:
            OutFile.write( "        ( \"%s\" \"%s\" ) \n" % (Name, Value) )
        OutFile.write( "   )\n" )
        
def writeOneValuesList( KeyName, DataName, Component, OutFile, ReturnAfterEach = 0 ):
    if (DataName in Component.keys()) and (len(Component[DataName]) > 0):
        OutFile.write( "   ( %s = " % KeyName )
        if ReturnAfterEach > 0: OutFile.write( "\n      ")
        for Value in Component[DataName]:
            OutFile.write( " \"%s\" " % Value )
            if ReturnAfterEach > 0: OutFile.write( "\n      ")
        OutFile.write( "   )\n" )
         

def generateJDF( OutFileName, ListOfComponents ):
    """ 
    Generate a KOALA Job Description File for a given workload unit. 
    
    In:
        OutFileName      -- the target file for writing the JDF of this workload unit
        ListOfComponents -- a list of components
                            Each component is a dictionary and has defined at 
                            least the following keys:
                            id, executable, count, description, directory, 
                            maxWallTime, arguments, env, stagein, stageout,
                            stdout, stderr
    """
    
    print "STATUS! Write JDF file", OutFileName, 
    OutFile = open( OutFileName, "w" )
    OutFile.write( "+" )
    index = 0
    #if ListOfComponents is None:
    #    print ">>>>>>>>>> Empty ListOfComponents"
    #    return 
        
    nComponents = len(ListOfComponents)
    for Component in ListOfComponents:
        #-- write unit component
        OutFile.write( " ( \n" )
        OutFile.write( " & ")
        writeOneStringValue( 'count', 'count', Component, OutFile )
        writeOneStringValue( 'directory', 'directory', Component, OutFile )
        writeOneStringValue( 'executable', 'executable', Component, OutFile )
        writeOneStringValue( 'maxWallTime', 'maxWallTime', Component, OutFile )
        
        if ('label' in Component.keys()) and (len(Component['label']) > 0):
            OutFile.write( "   ( label = \"%s\" ) \n" % str(Component['label']) )
        else:
            OutFile.write( "   ( label = \"subjob %d\" ) \n" % index )
        
        writeOneStringValue( 'jobtype', 'jobtype', Component, OutFile )
        writeOneStringValue( 'stdout', 'stdout', Component, OutFile )
        writeOneStringValue( 'stderr', 'stderr', Component, OutFile )
        
        if ('location' in Component.keys()) and (Component['location'].find('*') < 0):
            OutFile.write( "   ( resourceManagerContact = \"%s\" ) \n" % Component['location'] )
        
        writeOneTuples2List( 'environment', 'env', Component, OutFile )
        writeOneValuesList( 'arguments', 'arguments', Component, OutFile )
        writeOneValuesList( 'stagein', 'stagein', Component, OutFile, ReturnAfterEach = 1 )
        writeOneValuesList( 'stageout', 'stageout', Component, OutFile, ReturnAfterEach = 1 )
            
        OutFile.write( " )\n" )
        
        #-- ack component
        index = index + 1
        
    OutFile.close()
    print "...done"

    