#!/usr/bin/python

""" Generators loader for the Grenchmark project. """

__proggy = "WLDocLoader";
__rev = "0.1";
__proggy_stamp__ = "%s v%s" % (__proggy, __rev);
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'WLDocHandlers.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:19:35 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python"  

#---------------------------------------------------
# Log:
# 15/11/2005 A.I. 0.1  + added hasGeneratorFunc
# 11/08/2005 A.I. 0.0  Started this module
#---------------------------------------------------


import sys
import os.path
import os
import glob
import string

class GeneratorLoaderError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class GeneratorsLoader:
    """ Dynamically load generator modules (*.py files) from a given directory. """
    
    KNOWN_GENERATOR = 1
    UNKNOWN_GENERATOR = 0
    
    def __init__( self, ModulesPath = "apps", AppGenSig = "Generator", 
                  AppGenFuncName = "generateWorkloadUnit", ErrPrefix = "WLUnit Generator:" ):
        """ 
        Inits the GeneratorsLoader class.
        
        In:
            ModulesPath -- the relative path to generator modules (default: "apps"). 
            AppGenSig   -- the attribute name that must exist in all generators 
                           (default: "Generator"). 
            AppGenFuncName -- the name of the workload unit generator function 
                           (default: "generateWorkloadUnit"). 
        """
        self.ModulesPath    = ModulesPath
        self.AppGenSig      = AppGenSig
        self.AppGenFuncName = AppGenFuncName
        self.ErrPrefix      = ErrPrefix
        
        #-- init 
        self.GeneratorsDictionary = {}
    
    
    def loadGenerators(self):
        """ Dynamically loads all generators stored as *.py files in the ModulesPath. """
        
        self.ModulesDir = os.path.join( os.getcwd(), self.ModulesPath )
        if self.ModulesDir not in sys.path:
            sys.path.append( self.ModulesDir )
            
        #-- clear known generators
        self.GeneratorsDictionary = {}
        
        PotentialGenerators = glob.glob( os.path.join( self.ModulesDir, "*.py" ) )
        for PyFile in PotentialGenerators:
            if os.path.isfile(PyFile):
                ModuleName = os.path.splitext(os.path.basename(PyFile))[0]
                print "Found module", ModuleName
                
                try:
                    #---load possible generator module
                    mod = __import__(ModuleName)
                    sys.modules[ModuleName] = mod
                except ImportError, e:
                    raise GeneratorLoaderError( self.ErrPrefix + "Module" + ModuleName + "not found\n\n" + str(e) )
                
                try:
                    mod = sys.modules[ModuleName]
                except:
                    raise GeneratorLoaderError( self.ErrPrefix + "Module" + ModuleName + "not registered correctly (our error)\n\n" + str(e) )
                
                #---check if module is a generator, by verifying that it has a valid
                #   generator field
                CurrentDictionaryName = None
                #if hasattr(mod, self.AppGenSig):
                #else: 
                #    print "Module %s is no generator" % ModuleName
                try:
                    #---check if the module has a valid Generator attribute
                    modGeneratorInfo = getattr( mod, self.AppGenSig )
                    for line in modGeneratorInfo.split("\n"):
                        try:
                            line = line.strip()
                            Key, Value = line.split( "=", 2 )
                            if Key.find("Name") >= 0:
                                CurrentDictionaryName = Value
                            else:
                                print Key, ":", Value
                        except ValueError, e:
                            pass
                            
                except AttributeError:
                    print "Module %s has no attribute named %s -- not counted as a generator" % \
                        (ModuleName, self.AppGenSig)
            
                if CurrentDictionaryName:
                    try:
                        #---load generator function
                        self.GeneratorsDictionary[CurrentDictionaryName] = \
                            getattr(mod, self.AppGenFuncName)
                        print "Module", ModuleName, "generates entities of type", CurrentDictionaryName
                    except AttributeError, e:
                        print e
                print
        print "Got", len(self.GeneratorsDictionary), "generators!\n"
        
    def getGeneratorsDictionary(self):
        """ Returns the generators dictionary, or None. """
        return self.GeneratorsDictionary
        
    def getKnownGenerators(self):
        """ Returns all known generators names, or None. """
        return self.GeneratorsDictionary.keys()
        
    def getGeneratorFunc(self, AppName):
        """ Returns the generator func registered for the application name, or None. """
        if AppName in self.GeneratorsDictionary.keys():
            return self.GeneratorsDictionary[AppName]
        else:
            return None
            
    def hasGeneratorFunc(self, AppName):
        """ returns 1 if AppName is a valid generator name; 0 otherwise """
        if AppName in self.GeneratorsDictionary.keys():
            return GeneratorsLoader.KNOWN_GENERATOR
        else:
            return GeneratorsLoader.UNKNOWN_GENERATOR
            

if __name__ == "__main__":
    
    myLoader = GeneratorsLoader
    myLoader.loadGenerators()
    
    GensDic = myLoader.getGeneratorsDictionary()
    for Key in GensDic.keys():
        print GensDic[Key], ",", 
    print "."
    
    for Key in GensDic.keys():
        print myLoader.getGeneratorFuncGensDic(Key), ",", 
    print "."
    
    print "Done!"
    
    
