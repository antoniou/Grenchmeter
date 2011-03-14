#!/usr/bin/python

""" Document handlers for the Grenchmark project. """

__proggy = "WLDocHandlers";
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
# 03/04/2008 C.S. 0.3  + generate description files for multiple
#                        JDF generator types (not in a very elegant way for the moment)
#			Attention: the signature of the writeWorkloadSubmitFile function was modified
# 15/11/2005 A.I. 0.2  + composite applications
# 11/08/2005 A.I. 0.1  + Added grid sites XML docs handling
#                      + Added workload XML docs handling
# 11/08/2005 A.I. 0.0  Started this module
#---------------------------------------------------

import sys
from xml.sax import saxlib, saxexts
#from xml.sax import saxutils
if "utils" not in sys.path:
    sys.path.append("utils")
import AIRandomUtils
import traceback
import string

# tuple (immutable list) of keys required for GridSites
WLGridSiteKeys = ('id', 'location', 'machines')

WLSubmitSupportedVersion = ("2.0","2.1","2.0") # min, max, current
WLSubmitWorkloadEntryName = 'workload'
WLSubmitWorkloadKeys = ( 'version', 'name' )
WLSubmitJobEntryName = 'job'
WLSubmitJobKeys = ('id', 'name', 'description', 'jdf', 'composition-type', 'runTime', 'submitCommand')

WLDescTextFileMark = "text/wl-spec"

### from http://www.python.org/doc/current/tut/node10.html#SECTION0010400000000000000000
###      section 8.5 user-defined exceptions, Python Tutorial
class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

### based on http://www.rexx.com/~dkuhlman/pyxmlfaq.html
### need to get and install PyXML from http://sourceforge.net/projects/pyxml/
class GridSitesSaxDocumentHandler(saxlib.HandlerBase):                 
    def __init__(self, outfile):
        
        self.outfile = outfile
        self.level = 0
        self.inContent = 0
        self.contentData = []
        
        #-- register my scheme
        self.KnownAttributes = {}
        self.KnownAttributes['site'] = WLGridSiteKeys
        
        #-- init 
        self.DictionaryOfSites = {}
        
    def getDictionaryOfSites(self):
        return self.DictionaryOfSites
        
    def startDocument(self):                                    
        #print "--------  Document Start --------"
        pass
        
    def endDocument(self):                                      
        #print "--------  Document End --------"
        pass
        
    def startElement(self, name, attrs):
        
        for SchemeAttr in self.KnownAttributes.keys():
            if name == SchemeAttr:
                #print "Found new %s construct!" % SchemeAttr
                for attrName in attrs.keys():
                    if attrName not in self.KnownAttributes[SchemeAttr]:
                        print "*** Attribute %s (value='%s') is not valid inside the %s construct!\n" % \
                          ( attrName, attrs.get(attrName), SchemeAttr )
                CurrentSite = {}
                AnyError = 0
                for attrName in self.KnownAttributes[SchemeAttr]:
                    try:
                        if attrs.get(attrName) == None:
                            raise MyError(attrName)
                        CurrentSite[attrName] = attrs.get(attrName)
                    except:
                        print "*** ERROR! Could not find required %s attribute %s!" % \
                            ( SchemeAttr, attrName )
                        AnyError = AnyError + 1
                        pass
                
                if AnyError > 0:
                    if 'id' in CurrentSite:
                        SiteName = CurrentSite['id']
                    else:
                        SiteName = "(unknown)"
                    print "*** ERROR! There were %d errors parsing %s %s!" % \
                        ( AnyError, SiteName, SchemeAttr )
                else:
                    self.DictionaryOfSites[CurrentSite['id']] = CurrentSite
            
        if name == 'content':
            self.inContent = 1
            
    def endElement(self, name):                                 
        if name == 'content':
            self.inContent = 0
            content = string.join(self.contentData)
            self.printLevel()
            self.outfile.write('Content: ')
            self.outfile.write(content)
            self.outfile.write('\n')
            self.contentData = []
        self.level -= 1
        
    def characters(self, chrs, offset, length):                 
        if self.inContent:
            self.contentData.append(chars[offset:offset+length])
            
    def printLevel(self):                                       
        for idx in range(self.level):
            self.outfile.write('  ')

def readSiteFile(inFileName):
    """
    Reads site files from XML format
    """
    outFile = sys.stdout
    # Create an instance of the Handler.
    handler = GridSitesSaxDocumentHandler(outFile)
    # Create an instance of the parser.
    parser = saxexts.make_parser()
    # Set the document handler.
    parser.setDocumentHandler(handler)
    inFile = file(inFileName, 'r')
    # Start the parse.
    parser.parseFile(inFile)
    inFile.close()
    return handler
    
def writeSiteFile( OutFileName, DictionaryOfSites, GeneratorName = __proggy_stamp__): 
    """
    Writes site files into XML format
    
    In:
        OutFileName -- the output file name
        DictionaryOfSites  -- a dictionary of Site items, indexed by ID
        
        A Site item is a dictionary with at least 
        'id', 'location', 'machines' as keys.
    """
    
    OutFile = open( OutFileName, "w" )
    OutFile.write("<!-- File-type: xml/grid-desc -->\n")
    OutFile.write("<!-- Generator: %s -->\n" % GeneratorName )
    OutFile.write("<grid-sites>\n")

    for SiteID in DictionaryOfSites.keys():
        Site = DictionaryOfSites[SiteID]
        
        AnyErrors = 0
        for Key in Site.keys():
            if Key not in WLGridSitesApp:
                print "ERROR! Unavailable key %s" % Key
                AnyErrors = AnyErrors + 1        
        if AnyErrors > 0:
            continue
                
        OutFile.write("\t<site id=\"%s\" location=\"%s\" machines=\"%s\" />\n" % \
                      (Site['id'], Site['location'], Site['machines']) )
                    
    OutFile.write("</grid-sites>\n")
    OutFile.close()
    
### based on http://www.rexx.com/~dkuhlman/pyxmlfaq.html
### need to get and install PyXML from http://sourceforge.net/projects/pyxml/
class WorkloadSubmitSaxDocumentHandler(saxlib.HandlerBase):                 
    def __init__(self, outfile):
        
        self.outfile = outfile
        self.level = 0
        self.contentData = []
        
        self.inDependsOnContent = 0
        self.LastAppID = None
        
        #-- register my scheme
        self.KnownAttributes = {}
        self.KnownAttributes[WLSubmitJobEntryName] = WLSubmitJobKeys
        self.KnownAttributes[WLSubmitWorkloadEntryName] = WLSubmitWorkloadKeys
        
        #-- init 
        self.DictionaryOfApps = {}
        self._FileVersionSupported = 0
        
    def isFileVersionSupported(self):
        """ 0 if not supported; 1 otherwise """
        return self._FileVersionSupported 
        
    def getDictionaryOfApplications(self):
        return self.DictionaryOfApps
        
    def startDocument(self):                                    
        #print "--------  Document Start --------"
        pass
        
    def endDocument(self):                                      
        #print "--------  Document End --------"
        pass
        
    def startElement(self, name, attrs):
        ##print "WorkloadSubmitSaxDocumentHandler::name=", name
        
        if name == WLSubmitWorkloadEntryName:
            try:
                MinVersionList = WLSubmitSupportedVersion[0].split('.')
                MaxVersionList = WLSubmitSupportedVersion[1].split('.')
                CurrentVersionList = attrs.get('version').split('.')
                self._FileVersionSupported = 1
                for index in xrange(len(MinVersionList)):
                    if MinVersionList[index] > CurrentVersionList[index]:
                        self._FileVersionSupported = 0
                for index in xrange(len(MaxVersionList)):
                    if MaxVersionList[index] < CurrentVersionList[index]:
                        self._FileVersionSupported = 0
            except:
                self._FileVersionSupported = 0
            print "self._FileVersionSupported", self._FileVersionSupported
        
        if name == WLSubmitJobEntryName:
            #print "Found new %s construct!" % WLSubmitJobEntryName
            for attrName in attrs.keys():
                if attrName not in self.KnownAttributes[WLSubmitJobEntryName]:
                    print "*** Attribute %s (value='%s') is not valid inside the %s construct!\n" % \
                          ( attrName, attrs.get(attrName), WLSubmitJobEntryName )
            
            CurrentApp = {}
            AnyError = 0
            for attrName in self.KnownAttributes[WLSubmitJobEntryName]:
                try:
                    if attrs.get(attrName) == None:
                        raise MyError(attrName)
                    CurrentApp[attrName] = attrs.get(attrName)
                except:
                    print "*** ERROR! Could not find required %s attribute %s!" % ( WLSubmitJobEntryName, attrName )
                    AnyError = AnyError + 1
                    pass
                
            if AnyError > 0:
                if 'id' in CurrentSite:
                    AppName = CurrentApp['id']
                else:
                    AppName = "(unknown)"
                print "*** ERROR! There were %d errors parsing %s!" % ( AnyError, AppName )
            else:
                self.LastAppID = CurrentApp['id']
                self.DictionaryOfApps[self.LastAppID] = CurrentApp
                
        if name == 'dependsOn':
            if self.LastAppID is None: return # should NOT happen
            self.inDependsOnContent = 1
            if 'dependsOn' not in self.DictionaryOfApps[self.LastAppID]:
                self.DictionaryOfApps[self.LastAppID]['dependsOn'] = []
            
    def endElement(self, name):                                 
        if name == 'dependsOn':
            self.inDependsOnContent = 0
            content = string.join(self.contentData).replace(' ', '')
            #print ">>>>>", "found end of element", name, 'with data', content
            if self.LastAppID is not None:
                ListOfDependencies = content.split(',')
                for Dependency in ListOfDependencies:
                    if Dependency not in self.DictionaryOfApps[self.LastAppID]['dependsOn']:
                        self.DictionaryOfApps[self.LastAppID]['dependsOn'].append(Dependency)
            self.contentData = []
        
    def characters(self, chars, offset, length):                 
        if self.inDependsOnContent:
            self.contentData.append(chars[offset:offset+length])
            ##print ">>>>>", "found data", "'"+str(chars[offset:offset+length])+"'"

def readWorkloadSubmitFile(inFileName):
    """
    Reads workload submit files from XML format
    """
    outFile = sys.stdout
    # Create an instance of the Handler.
    handler = WorkloadSubmitSaxDocumentHandler(outFile)
    # Create an instance of the parser.
    parser = saxexts.make_parser()
    # Set the document handler.
    parser.setDocumentHandler(handler)
    inFile = file(inFileName, 'r')
    # Start the parse.
    parser.parseFile(inFile)
    inFile.close()
    return handler
    
def writeWorkloadSubmitFile( OutFileName, WLName, WLJobsList, JDFGeneratorType, Type = "root", GeneratorName = __proggy_stamp__ ):
    """
    Writes workload submit files into XML format
    
    In:
        OutFileName -- the output file name
        WLAppsList  -- a list of App items
        JDFGeneratorType - new parameter since v0.3; for single jobs it is a string representing the JDF generator, 
        e.g. 'condor-jdf', 'sge-jdf' etc.; for DAGs it is an integer representing an index in the DAG generators list
        
        An App item is a dictionary with at least 
        'id', 'name', 'description', 'jdf', 'runTime', 'submitCommand' as keys.
        
    See also:
        utils/WLDocHandlers.WLSubmitJobKeys
    """
    GeneratorCmdMap = {'condor-jdf':'wrapper_scripts/condor_submit_wrapper.sh', 'sge-jdf':'wrapper_scripts/sge_submit_wrapper.sh'}
    
    OutFile = open( OutFileName, "w" )
    OutFile.write("<!-- File-type: xml/wl-submit-desc -->\n")
    OutFile.write("<!-- Generated by %s-->\n" % GeneratorName )
    OutFile.write("<workload type=\"%s\" name=\"%s\" version=\"%s\">\n" % (Type, WLName, WLSubmitSupportedVersion[2]))
    
    #-- generate workload file content -- applications
    for Job in WLJobsList:
        ##print ">>>", "Printing", Job['id'], "to", OutFileName
        AnyErrors = 0
        for Key in WLSubmitJobKeys:
            if Key not in Job.keys():
                print "ERROR! Unavailable key %s" % Key
                AnyErrors = AnyErrors + 1        
        if AnyErrors > 0:
            continue
        OutFile.write("\t<%s \n" % WLSubmitJobEntryName)
        
        DirName = ''
        if isinstance(JDFGeneratorType, str):
            ResManagerName = JDFGeneratorType.replace('-jdf', '')
            DirName = "jdfs-%s" % ResManagerName
        
        for Key in WLSubmitJobKeys:
            if Key == 'jdf':                
                if isinstance(Job[Key], str):
                    # this is a simple job - we need to modify the path to the JDF file
                    #print 'string' 
                    FinalJDFName = Job[Key].replace('jdfs', DirName)
                    OutFile.write("\t\t%s=\"%s\" \n" % (Key, FinalJDFName))                                  
                elif isinstance(Job[Key], list):
                    OutFile.write("\t\t%s=\"%s\" \n" % (Key, Job[Key][JDFGeneratorType])) 
            elif Key == 'submitCommand': 
                Cmd =  Job[Key]                                                
                if isinstance(Job[Key], list):
                    Cmd = Job[Key][JDFGeneratorType]
                else:
                    CmdArray = Cmd.split(' ')
                    if JDFGeneratorType in GeneratorCmdMap.keys():
                        CmdArray[0] = GeneratorCmdMap[JDFGeneratorType]
                        Cmd = ''
                        for Comp in CmdArray:
                            Cmd = Cmd + Comp + ' '
                    else:
                        print('ERROR! [WlDocHandlers.py] Submit command not known for %s' % JDFGeneratorType)
                        
                if DirName != '':
                    Cmd = Cmd.replace('jdfs', DirName)
                OutFile.write("\t\t%s=\"%s\" \n" % (Key, Cmd))
            else:
                OutFile.write("\t\t%s=\"%s\" \n" % (Key, Job[Key]) )
            
        if 'dependsOn' in Job:
            NDeps = len(Job['dependsOn'])
            if NDeps > 0:
                OutFile.write("\t>\n")
                OutFile.write("\t\t<dependsOn>")
                WrittenDeps = 0
                LineDeps = 0
                for Dependency in Job['dependsOn']:
                    if LineDeps > 0: OutFile.write(",")
                    OutFile.write("%s" % Dependency)
                    LineDeps = LineDeps + 1
                    WrittenDeps = WrittenDeps + 1
                    if LineDeps == 5:
                        LineDeps = 0
                        OutFile.write("</dependsOn>\n")
                        if WrittenDeps < NDeps:
                            OutFile.write("\t\t<dependsOn>")
                if LineDeps > 0:
                    OutFile.write("</dependsOn>\n")
                OutFile.write("\t</%s>\n" % WLSubmitJobEntryName)
            else:
                OutFile.write("\t/>\n")
        else:
            OutFile.write("\t/>\n")
        
    OutFile.write("</workload>\n")
    OutFile.close()


def isTextWorkloadDescriptionFile( InFileName):
    """ Return 0 if InFileName is not a text workload description file, !0 otherwise """
    
    IsWLDescTextFile = 0
    InFile = open( InFileName ) 
    while 1:
        lines = InFile.readlines(100000) ## 100KB buffer
        if not lines:
            break
        #-- process lines
        for line in lines: 
            if (len(line) > 0) and (line[0] == '#'): 
                if line.find( WLDescTextFileMark ) >= 0:
                    IsWLDescTextFile = 1
                    break
        if IsWLDescTextFile != 0:
            break
    return IsWLDescTextFile



#--- READ WL Desc routines
def readTextOtherInfo_FromFile( InFileName ):
    """ read a listof OtherInfo blocks from a text file """
    OtherInfoBlocks = []
    InFile = open( InFileName ) 
    while 1:
        lines = InFile.readlines(100000) # buffered read
        if not lines:
            break
        #-- process lines
        for line in lines: 
            if len(line) > 0:
                line=line.strip() 
            if (len(line) > 0) and (line[0] != '#'): 
                #-- read a non-comment line; expect it to be Key=Value
                try:
                    OtherInfoName, OtherInfoValue = line.split("=",1)
                    # data ok, save this blockb (at least one Key=Value here)
                    OtherInfoBlocks.append(line)
                except: #ValueError
                    continue
                
    # close OtherInfo extra file
    InFile.close()
    return OtherInfoBlocks
    
def readTextOtherInfo_Blocks( OtherInfoBlocks, FileName = "main" ):
    if FileName != "main":
        print "...parsing other info from", FileName
        
    OtherInfoSpecialCasesList = ['ExternalFile', 'UseGenerator']
    OtherInfoDic = {}
    ElementNo = 0
    for OtherInfoBlock in OtherInfoBlocks:
        #print 'Block=', OtherInfoBlock
        if FileName == "main" or OtherInfoBlock.startswith('*'):
            if OtherInfoBlock.startswith('*'):
                OtherInfoBlock = OtherInfoBlock[1:]
                print 'multiline OtherInfoBlock is now', OtherInfoBlock
                
            OtherInfoDataList = OtherInfoBlock.split(",")
        else:
            OtherInfoDataList = [OtherInfoBlock.strip()]
            
        for OtherInfoData in OtherInfoDataList:
            #print 'Data=', OtherInfoData
            ElementNo = ElementNo + 1
            if len(OtherInfoData) <= 0:
                print "Empty OtherInfo element ", ElementNo, "of ", FileName, "...skipping element"
                continue
            
            OtherInfoData = OtherInfoData.strip()
            if len(OtherInfoData) <= 0:
                print "Empty OtherInfo element ", ElementNo, "of ", FileName, "...skipping element"
                continue
                
            try:
                OtherInfoName, OtherInfoValue = OtherInfoData.split("=",1)
                ### Note: CASE-SENSITIVE names
                ###OtherInfoName = OtherInfoName.strip().lower()
            except: #ValueError
                print "Cannot convert OtherInfo element", ElementNo, "'"+OtherInfoData+"'", "of ", FileName, "to (Name,Value)...skipping element"
                continue
                
            #print OtherInfoName, OtherInfoValue
            
            #--- treat OtherInfo special cases:
            #    'ExternalFile', 'UseGenerator'
            # TODO: treat OtherInfo special cases, if more than 3
            #       create a dictionary of special cases: key = special case name, 
            #       value = special case treatment function
            IsSpecialCase = 0
            if OtherInfoName in OtherInfoSpecialCasesList:
                IsSpecialCase = 1
            
            if IsSpecialCase == 0:
                if OtherInfoName in OtherInfoDic.keys():
                    print "Element", ElementNo, " of ", FileName, ":", OtherInfoName, "is already defined...replacing old value"
                ##if FileName != "main":
                ##    print '>>>>>', FileName, ": Found key-value pair", OtherInfoName, OtherInfoValue
                OtherInfoDic[OtherInfoName] = OtherInfoValue
                
            else:
                ##print OtherInfoName, ";OtherInfoName.find('ExternalFile')", OtherInfoName.find('ExternalFile')
                if OtherInfoName.find('ExternalFile') >= 0:
                    print "Reading other info from file", OtherInfoValue
                    NewOtherInfoBlocks = readTextOtherInfo_FromFile(OtherInfoValue)
                    #--- Other Info Blocks: recursive call
                    NewOtherInfoDic = readTextOtherInfo_Blocks( NewOtherInfoBlocks, OtherInfoValue )
                    #-- add new results
                    for OtherInfoName in NewOtherInfoDic.keys():
                        ##print "Found", OtherInfoName, "=", NewOtherInfoDic[OtherInfoName]
                        OtherInfoDic[OtherInfoName] = NewOtherInfoDic[OtherInfoName]
                    
                elif OtherInfoName.find('UseGenerator') >= 0:
                    # TODO: UseGenerator special case of Other Info data
                    pass
                
    ##if FileName.find("main") >= 0:
    ##    print ">>>>>"
    ##    for OtherInfoName in OtherInfoDic.keys():
    ##        print "     Found", OtherInfoName, "=", OtherInfoDic[OtherInfoName]
            
    return OtherInfoDic
    
#--- v1.1_: 
def getArrivalTimeDistribution( Text ):
    """ return the arrival time distribution specified by Text """ 
    
    ArrivalTimeDistr = Text
    
    pos = ArrivalTimeDistr.find("(")
    ArrivalTimeParamsList = []
    if pos >= 0:
        try:
            ArrivalTimeParamsList = ArrivalTimeDistr[pos+1:ArrivalTimeDistr.find(")")].split(",")
        except:
            ArrivalTimeParamsList = []
            pass
        ArrivalTimeName = ArrivalTimeDistr[0:pos]
        #print ArrivalTimeName, ArrivalTimeParamsList
        
    return (ArrivalTimeName, ArrivalTimeParamsList)
# _v1.1

#--- v1.1_: composite: added GeneratorType (one of composite:unitary)
def textWorkloadDescriptionLine_ToUnitDef( ID, GeneratorType, NTimes, UnitType, SiteType, \
                            NTotalJobs, SiteInfo, ArrivalTimeDistr, OtherInfo, \
                            LineNo, iMaxID, UniqueIDs, \
                            KnownJobNamesList, KnownWorkloadJobNamesList, KnownSiteNamesList ):
# _v1.1: composite: added GeneratorType (one of composite:unitary)
    
    DefsDic = {}
    
    OneDef = {}
                
    # data for ambiguous jobs assignment to Sites
    bSomeUnassignedJobs = 0 # any jobs SiteInfo Amounts specified as '?'
    
    #--- ID
    ID = ID.strip()
    if ID != '?':
        # check ID
        try:
            ID = int(ID)
            if ID > iMaxID:
                iMaxID = ID 
        except:
            print "Cannot convert to int the ID (", "'" + ID + "'", ") on line", LineNo, "...skipping line"
            raise Exception, "ID conversion."
            
        if ID in UniqueIDs:
            print "Already existing ID on line", LineNo, "...skipping line"
            raise Exception, "Already existent ID " + ID
            
    else:
        ID = iMaxID + 1
        iMaxID = ID
        print "Line", LineNo, "New ID", "("+str(ID)+")", "generated for this unit."
            
    
    #--- v1.1_: composite: added GeneratorType (one of composite:unitary)
    #--- composite?
    if GeneratorType.find('composite') >= 0:
        OneDef['composite'] = 1
    else:
        OneDef['composite'] = 0
    # _v1.1: composite: added GeneratorType (one of composite:unitary)
    
    #--- unit type parsing
    UnitType = UnitType.strip()
    UnitTypePrefix = None
    pos = UnitType.find(":")
    if pos >= 0:
        UnitTypePrefix = UnitType[0:pos]
        UnitType = UnitType[pos+1:]
        #print ">>>UnitType", UnitTypePrefix, UnitType
        
    
    if UnitTypePrefix == "wl" or OneDef['composite'] == 1:
        OneDef['IsWorkload'] = 1 # set workload flag
    else:
        OneDef['IsWorkload'] = 0
        
    if OneDef['composite'] == 0: # unitary app: problem
        if (OneDef['IsWorkload'] == 0 and UnitType not in KnownJobNamesList) or \
           (OneDef['IsWorkload'] == 1 and UnitType not in KnownWorkloadJobNamesList):
            print "Unknown Unit Type", "'"+UnitType+"'", "on line", LineNo, "...skipping line"
            raise Exception, "Unknown UnitType " + "'"+UnitType+"'"
    elif OneDef['composite'] == 1:
        OneDef['CompositionType'] = UnitType
    OneDef['apptype'] = UnitType
    
    
    #--- site info parsing
    SiteInfoList = []
    if ( len(SiteInfo) > 0 ) and ( len(SiteInfo.strip()) > 0 ) and \
       ( SiteInfo != "-" ):
        SiteInfoDataList = SiteInfo.split(",")
        ElementNo = 0
        for SiteInfoData in SiteInfoDataList:
            ElementNo = ElementNo + 1
            if len(SiteInfoData) <= 0:
                print "Empty SiteInfo element", ElementNo, "'"+SiteInfoData+"'", "on line", LineNo, "...skipping element"
                continue
            SiteInfoData = SiteInfoData.strip()
            if len(SiteInfoData) <= 0:
                print "Empty SiteInfo element", ElementNo, "'"+SiteInfoData+"'", "on line", LineNo, "...skipping element"
                continue
        
            #Allowed forms: *:?,fs3:?,fs2:10,*:5
            try:
                SiteInfoID, SiteInfoAmount = SiteInfoData.split(":",1)
            except: #ValueError
                print "Cannot convert SiteInfo element", ElementNo, "'"+SiteInfoData+"'", "on line", LineNo, "to (SiteName,Amount)...skipping element"
                continue
            
            # found possibly valid pair
            if not ((SiteInfoID == "*") or (SiteInfoID in KnownSiteNamesList)):
                print "Unknown name", "'"+SiteInfoID+"'", "in element", ElementNo, "'"+SiteInfoData+"'", "on line", LineNo, "...skipping element"
                continue
                
            if SiteInfoAmount == "?":
                bSomeUnassignedJobs = bSomeUnassignedJobs + 1
            else:
                try:
                    SiteInfoAmount = int(SiteInfoAmount)
                except:
                    print "Unknown amound", "'"+SiteInfoAmount+"'", "in element", ElementNo, "'"+SiteInfoData+"'", "on line", LineNo, "...skipping element"
                    continue
                    
            SiteInfoList.append( (SiteInfoID, SiteInfoAmount) )
        
    #--- other info parsing
    OtherInfoDic = {}
    if ( len(OtherInfo) > 0 ) and ( len(OtherInfo.strip()) > 0 ) and \
       ( OtherInfo != "-" ):
        OtherInfoBlocks = [OtherInfo]
        OtherInfoDic = readTextOtherInfo_Blocks( OtherInfoBlocks )
                
    #--- add all other info
    OneDef['otherinfo'] = OtherInfoDic
    
    if OneDef['IsWorkload'] == 0:
        # not a self-building workload
        #--- verify that ambiguous definitions can be solved
        if NTotalJobs == "?":
            if bSomeUnassignedJobs > 0:
                print "Both the Total job count and the SiteInfo amounts are ambiguous (they both have '?' definitions) on line", LineNo, "...skipping line"
                raise Exception, "Both Total job count and the SiteInfo amounts are ambiguous"
            else:
                NTotalJobs = 0
                for SiteInfoData in SiteInfoList:
                    NTotalJobs = NTotalJobs + SiteInfoData[1]
                print "Line", LineNo, "Total amount of jobs is computed to be", NTotalJobs
        else:
            try:
                NTotalJobs = int(NTotalJobs)
            except:
                print "Cannot convert to int", "'"+NTotalJobs+"'", "on line", LineNo, "...skipping line"
                raise Exception, "Total jobs amount must be integer (cannot convert to int)"
        OneDef['totaljobs'] = NTotalJobs
            
        #--- get job components, based on the SiteType
        ### Note: case-insensitive names
        SiteType = SiteType.strip().lower()
        # SiteType must be one of "single", "unordered", "ordered", "semi-ordered"
        OneDef['sitetype'] = SiteType
        DicComponents = {}
        if SiteType == "single":
            ComponentNo = 0
            for SiteInfoData in SiteInfoList:
                DicComponents[ComponentNo] = { 'location':SiteInfoData[0], 
                                               'amount':SiteInfoData[1] }
                ComponentNo = ComponentNo + 1
            if ComponentNo > 1:
                print "More than 1 component defined in a single job on line", LineNo, "...skipping line"
                raise Exception, "more than one component defined for a single job"
                
        elif SiteType == "unordered":
            try:
                NSites = OtherInfoDic['NSites']
            except:
                print "Could not find NSites in OtherInfo of an unordered job on line", LineNo, "...skipping line"
                raise Exception, "Could not find NSites in OtherInfo of an unordered job"
                
            try:
                NSites = int(NSites)
            except:
                print "NSites must be an integer value in OtherInfo on line", LineNo, "...skipping line"
                raise Exception, "NSites must be an integer value"
            
            ComponentNo = 0
            while ComponentNo < NSites:
                DicComponents[ComponentNo] = { 'location':'*', 
                                               'amount':'?' }
                ComponentNo = ComponentNo + 1
            
        elif SiteType == "ordered":
            ComponentNo = 0
            for SiteInfoData in SiteInfoList:
                DicComponents[ComponentNo] = { 'location':SiteInfoData[0], 
                                               'amount':SiteInfoData[1] }
                ComponentNo = ComponentNo + 1
            if ComponentNo == 0:
                raise Exception, "Could not find any components of an ordered job"
                
        elif SiteType == "semi-ordered":
            try:
                NSites = OtherInfoDic['NSites']
            except:
                print "Could not find NSites in OtherInfo of a semi-ordered job on line", LineNo, "...skipping line"
                raise Exception, "Could not find NSites in OtherInfo of a semi-ordered job"
            
            try:
                NSites = int(NSites)
            except:
                print "NSites must be an integer value in OtherInfo on line", LineNo, "...skipping line"
                raise Exception, "NSites must be an integer value in OtherInfo"
            
            SitesToGo = NSites - len(SiteInfoList)
            if SitesToGo < 0:
                print "NSites must be greater than the number of SiteInfo elements (", \
                      len(SiteInfoList), ")", LineNo, "...skipping line"
                raise Exception, "NSites must be greater than the number of SiteInfo elements (" + str(len(SiteInfoList)) + ")"
            
            #-- add unordered components first
            ComponentNo = 0
            while ComponentNo < SitesToGo:
                DicComponents[ComponentNo] = { 'location':'*', 
                                               'amount':'?' }
                ComponentNo = ComponentNo + 1
            
            #-- add ordered components last
            #   NOTE: ComponentNo keeps counting
            for SiteInfoData in SiteInfoList:
                DicComponents[ComponentNo] = { 'location':SiteInfoData[0], 
                                               'amount':SiteInfoData[1] }
                ComponentNo = ComponentNo + 1
            
        else:
            print "Unknown Site Type", SiteType, "on line", LineNo, "...skipping line"
            raise Exception, "Unknown Site Type " + "'"+SiteType+"'"
        
        OneDef['otherinfo']['NSites'] = ComponentNo
        OneDef['components'] = DicComponents
    
    #--- arrival time distribution
    OneDef['arrivaltimeinfo'] = getArrivalTimeDistribution(ArrivalTimeDistr)
    
    #--- Place this definition NTimes
    try:
        NTimes = int(NTimes)
    except:
        print "Wrong NTimes field", "("+NTimes+")", "...resetting to 1 (default)"
        NTimes = 1
        
    OneDef['multiplicity'] = NTimes
    OneDef['id'] = ID
    
    DefsDic[ID] = OneDef
    
    ##print 'Defined unit with ID', ID
    
    return (iMaxID, DefsDic)

def readTextWorkloadDescriptionFile( InFileName, \
    KnownJobNamesList, KnownWorkloadJobNamesList, KnownSiteNamesList ):
    
    print "In readTextWorkloadDescriptionFile(", InFileName, ", ...)"
    
    print "Identified", InFileName, "as text workload description file"
      
    ListOfDefs = []
    
    LineNo = 0
    UniqueIDs = {}
    iMaxID = -1
    
    DefaultVersion = 1.0
    Version = DefaultVersion
    
    InFile = open( InFileName ) 
    while 1:
        lines = InFile.readlines(100000) # buffered read
        if not lines:
            break
        #-- process lines
        for line in lines: 
            LineNo = LineNo + 1
            if len(line) > 0:
                line=line.strip() 
                
            #--- v1.1_: file version
            if (len(line) > 0) and (line[0] == '#'): 
                sFileVersion = 'file-version'
                pos = line.lower().find(sFileVersion)
                if pos >= 0:
                    try:
                        # pos + len *+1* -> skip ':' after sFileVersion
                        Version = float(line[pos + len(sFileVersion) + 1:]) 
                    except:
                        Version = DefaultVersion
            # _v1.1: file version
                
            if (len(line) > 0) and (line[0] != '#'): 
                #--- v1.1_: file version
                # TODO: based on the file version, have different read methods
                #       (version support; backwards compatibility) 
                # _v1.1: file version
                
                #-- read a non-comment line
                try:
                    # WL Unit ID<tab>Times this unit<tab>Job Type<Tab>
                    # Site structure type<Tab>Total # of jobs in this unit<tab>
                    # Detailed Site structure<Tab>
                    # Arrival time distribution<Tab>Other info
                    #--- v1.1_: composite: added GeneratorType (one of composite:unitary)
                    ID, GeneratorType, NTimes, UnitType, SiteType, \
                    NTotalJobs, SiteInfo, ArrivalTimeDistr, OtherInfo = \
                        line.split( '\t', 8 )
                    # _v1.1: composite: added GeneratorType (one of composite:unitary)
                    
                except: 
                    print "Erroneous line #", LineNo, "('" + line + "')", "...skipping"
                    print "Maybe you used spaces (' ') as separators, instead of tabs ('\t')?"
                    #print '>>>>>>', traceback.print_exc()
                    continue
                
                #--- process line
                try:
                    OldIMaxID = iMaxID
                    #--- v1.1_: composite: added GeneratorType (one of composite:unitary)
                    (iMaxID, NewDefsDic) = \
                        textWorkloadDescriptionLine_ToUnitDef( ID, GeneratorType, NTimes, UnitType, SiteType, \
                            NTotalJobs, SiteInfo, ArrivalTimeDistr, OtherInfo, \
                            LineNo, iMaxID, UniqueIDs, \
                            KnownJobNamesList, KnownWorkloadJobNamesList, KnownSiteNamesList )
                    # _v1.1: composite: added GeneratorType (one of composite:unitary)
                            
                    # if the definition was correct, add the newly created 
                    for ID in NewDefsDic.keys():
                        UniqueIDs[ID] = 1 
                        ListOfDefs.append( NewDefsDic[ID] ) 
                    
                except:
                    iMaxID = OldIMaxID
                    # print detailed traceback information
                    print "TRACEBACK::WL-DESCRIPTION LINE INTERPRETER EXCEPTION\n>>>\n", traceback.print_exc()
                    print "\n<<<\n"
                
    # close the WL desc file
    InFile.close()
                
    #--- Return the global list of *correct* definitions
    #print "!!!", ListOfDefs
    return ListOfDefs
    
def readWorkloadDescriptionFile( InFileName, KnownJobNamesList, KnownWorkloadJobNamesList, KnownSiteNamesList ):
    """
    Reads workload description files from Text/XML files
    """
    
    print "In readWorkloadDescriptionFile(", InFileName, ", ...)"
    
    if isTextWorkloadDescriptionFile( InFileName ):
        return readTextWorkloadDescriptionFile( InFileName, KnownJobNamesList, KnownWorkloadJobNamesList, KnownSiteNamesList )
    else:
        #TODO: text file parsing failed, might be an XML file
        # return handler.getListOfDefs()
        return []
        
    
