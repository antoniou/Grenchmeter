
JDFGenerator="""
    Name=exe-jdf
    Info=Does not print anything :)
    Copyright=copyright (C) 2005 Alexandru Iosup
    """
    
def generateJDF( OutFileName, ListOfComponents ):
    """ 
    Does not print anything
    
    In:
        OutFileName      -- the target file for writing the JDF of this workload unit
        ListOfComponents -- a list of components
                            Each component is a dictionary and has defined at 
                            least the following keys:
                            id, executable, count, description, directory, 
                            maxWallTime, arguments, env, stagein, stageout,
                            stdout, stderr
    """
    pass
    
    