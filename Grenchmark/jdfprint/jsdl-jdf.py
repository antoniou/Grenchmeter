
import os.path

import sys
if "utils" not in sys.path:
    sys.path.append("utils")
import WLDocHandlers
import AIRandomUtils
import time

JDFGenerator="""
    Name=jsdl-jdf
    Info=Print to KOALA Job Description File (http://www.st.ewi.tudelft.nl/koala/)
    Author=N. Yigitbasi
    Contact=email:M.N.Yigitbasip@tudelft.nl
    Copyright=copyright (C) 2008 M. Nezih YIGITBASI
    """

def writeApplicationArguments(OutFile, args):
    for argument in args:
        OutFile.write('<jsdl-posix:Argument>')
        OutFile.write(str(argument))
        OutFile.write('</jsdl-posix:Argument>\n')
             
def writeApplicationEnvVariables(OutFile, env):
    for (Name, Value) in env:
        OutFile.write('<jsdl-posix:Environment name=\"')
        OutFile.write(Name)
        OutFile.write('\">')
        OutFile.write(Value)
        OutFile.write('</jsdl-posix:Environment>\n')   
                  
def writeStageInFiles(OutFile, stageIn):
    for si in stageIn:
        if not si == '':
            OutFile.write('<jsdl:DataStaging>\n')
            OutFile.write('<jsdl:FileName>'+str(si)+'</jsdl:FileName>\n')
            OutFile.write('<jsdl:Source>\n')
            OutFile.write('<jsdl:URI>'+str(si)+'</jsdl:URI>\n')
            OutFile.write('</jsdl:Source>\n')
            OutFile.write('</jsdl:DataStaging>\n')
                          
def writeStageOutFiles(OutFile, stageOut):
    for so in stageOut:
        OutFile.write('<jsdl:DataStaging>\n')
        OutFile.write('<jsdl:FileName>'+str(si)+'</jsdl:FileName>\n')
        OutFile.write('<jsdl:Target>\n')
        OutFile.write('<jsdl:URI>'+str(si)+'</jsdl:URI>\n')
        OutFile.write('</jsdl:Target>\n')
        OutFile.write('</jsdl:DataStaging>\n')
                                  
def writeJsdlHeader(OutFile):
    OutFile.write('<jsdl:JobDefinition xmlns=\"http://www.example.org/\"\nxmlns:jsdl=\"http://schemas.ggf.org/jsdl/2005/11/jsdl\"\n')
    OutFile.write('xmlns:jsdl-posix=\"http://schemas.ggf.org/jsdl/2005/11/jsdl-posix\"\n')
    OutFile.write('xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">')  

def writeJsdlFooter(OutFile): 
    OutFile.write('</jsdl:JobDefinition>')


def generateJDF( OutFileName, ListOfComponents ):
    """ 
    Generate a OGF JSDL File for a given workload unit. 
    
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
    
    index = 0
    nComponents = len(ListOfComponents)
    Component = ListOfComponents[0] # one component 
    
    writeJsdlHeader(OutFile)
    OutFile.write('<jsdl:JobDescription>\n')
    
    """
    <jsdl:Application>
      <jsdl:ApplicationName>ls</jsdl:ApplicationName>
      <jsdl-posix:POSIXApplication>
        <jsdl-posix:Executable>/bin/ls</jsdl-posix:Executable>
        <jsdl-posix:Argument>-la file.txt</jsdl-posix:Argument>
        <jsdl-posix:Environment name="LD_LIBRARY_PATH">/usr/local/lib</jsdl-posix:Environment>
        <jsdl-posix:Input>/dev/null</jsdl-posix:Input>
        <jsdl-posix:Output>stdout.${JOB_ID}</jsdl-posix:Output>
        <jsdl-posix:Error>stderr.${JOB_ID}</jsdl-posix:Error>
      </jsdl-posix:POSIXApplication>
    </jsdl:Application>
    """
    OutFile.write('<jsdl:Application>\n')
    OutFile.write('<jsdl:ApplicationName>')
    OutFile.write("sser"+ str(AIRandomUtils.getRandomInt(0,int(2**64))))
    OutFile.write('</jsdl:ApplicationName>\n')
    
    OutFile.write('<jsdl-posix:POSIXApplication>\n')
    OutFile.write('<jsdl-posix:Executable>')
    OutFile.write(str(Component['executable']))
    OutFile.write('</jsdl-posix:Executable>\n')
    
    args = Component['arguments']
    writeApplicationArguments(OutFile, args)
    stdout = Component['stdout']
    OutFile.write('<jsdl-posix:Output>'+stdout+'</jsdl-posix:Output>\n')
    stderr = Component['stderr']
    OutFile.write('<jsdl-posix:Error>'+stderr+'</jsdl-posix:Error>\n')
    #OutFile.write('<jsdl-posix:Input></jsdl-posix:Input>\n')
    
    writeApplicationEnvVariables(OutFile, Component['env'])
    
       
    OutFile.write('<jsdl-posix:Environment name="LD_LIBRARY_PATH">/usr/local/lib</jsdl-posix:Environment>')
    
    OutFile.write('\n</jsdl-posix:POSIXApplication>\n')
             
    OutFile.write('</jsdl:Application>\n')
    
    
    """
        <jsdl:DataStaging>
      <jsdl:FileName>file.txt</jsdl:FileName>
      <jsdl:CreationFlag>overwrite</jsdl:CreationFlag>
      <jsdl:DeleteOnTermination>true</jsdl:DeleteOnTermination>
      <jsdl:Source>
        <jsdl:URI>gsiftp://hydrus.dacya.ucm.es/home/jose/file1.txt</jsdl:URI>
      </jsdl:Source>
    </jsdl:DataStaging>
    """
    stagein = Component['stagein']
    stageout = Component['stageout']
    writeStageInFiles(OutFile, stagein)
    writeStageOutFiles(OutFile, stageout)   
    
    
    OutFile.write('</jsdl:JobDescription>')
    writeJsdlFooter(OutFile)
    OutFile.close()
    print "...done"

    