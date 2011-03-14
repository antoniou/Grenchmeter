#!/usr/bin/python -tt
# -*- coding: UTF-8 -*-

__copyright__="""
#########################################################################
##
## ￂﾩ University of Southampton IT Innovation Centre, 2006
##
## Copyright in this library belongs to the IT Innovation Centre of
## 2 Venture Road, Chilworth Science Park, Southampton SO16 7NP, UK.
##
## This software may not be used, sold, licensed, transferred, copied
## or reproduced in whole or in part in any manner or form or in or
## on any media by any person other than in accordance with the terms
## of the Licence Agreement supplied with the software, or otherwise
## without the prior written consent of the copyright owners.
##
## This software is distributed WITHOUT ANY WARRANTY, without even the
## implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
## PURPOSE, except where stated in the Licence Agreement supplied with
## the software.
##
##      Created By :            Panos Melas
##      Created Date :          2007/01/11
##      Created for Project:    SIMDAT
##
#########################################################################
##
##      Dependencies : none
##
#########################################################################
##
##      Last commit info:       $Author: tal $
##                              $Date: 2007-11-29 12:43:49 +0000 (Thu, 29 Nov 2007) $
##                              $Revision: 8852 $
##
#########################################################################"""

import os
import sys

import XMLUtils

from xml.dom import minidom, Node

JSDL_NS = 'http://schemas.ggf.org/jsdl/2005/11/jsdl'
JSDL_POSIX_NS = 'http://schemas.ggf.org/jsdl/2005/11/jsdl-posix'

SUPPORTED_RANGE_RESOURCES = (
	"FileSystem"
	"IndividualCPUSpeed"
	"IndividualCPUCount"
	"IndividualCPUTime"
	"IndividualNetworkBandwidth"
	"IndividualPhysicalMemory"
	"IndividualVirtualMemory"
	"IndividualDiskSpace"
	"TotalCPUCount"
	"TotalCPUTime"
	"TotalPhysicalMemory"
	"TotalVirtualMemory"
	"TotalDiskSpace"
)

class DataStagingElement:
	#def __init__(self, fileName,source,target):
	#	self.fileName = fileName
		#self.creationFlag = creationFlag
		#self.deleteOnTermination = deleteOnTermination
	#	self.source = source
	#	self.target = target
	def __init__(self):
		self.fileName = ''
		self.source = ''
		self.target = ''
		self.creationFlag =''
		self.deleteOnTermination = ''
		
	def setFileName(self, fileName):
		self.fileName = fileName
		
	def setSource(self, source):
		self.source = source
		
	def setTarget(self, target):
		self.target = target
		
	def setCreationFlag(self, creationFlag):
		self.creationFlag = creationFlag
		
	def setDeleteOnTermination(self, deleteOnTermination):
		self.deleteOnTermination = deleteOnTermination				
				
class Job:
	""" Simple JSDL parser.  Job objects are typically passed to functions in
		L{RMConnector<RMConnector.RMConnector>}s, and contain information from the
		JSDL about the job in question.
	"""
	
	def __init__(self, jsdlFileName):
		self.arguments = []
		""" List of application arguments specified in the JSDL """
		
		self.candidateHosts = []
		""" List of hostnames the user has requested the job be run on """
		
		self.posixConstraints = {}
		""" Dictionary mapping from JSDL POSIXApplication element names to values """
		
		self.rangeResources = {}
		""" Dictionary mapping of JSDL Resources names to another dictionary with
			"lower" and "upper" keys, which either contain floating point values or
			None if not specified in the JSDL. """
		
		self.jobName = "GRIA Job Service job"
		""" The user-specified name of the job """
		
		self.operatingSystem = None
		""" The operating system name requested in the JSDL - takes values None if unspecified,
			or one of OperatingSystemTypeEnumeration from the JSDL spec """
		
		self.cpuArchitecture = None
		""" The processor architecture requested in the JSDL - takes values None if unspecified,
			or one of ProcessorArchitectureEnumeration from the JSDL spec """
			
		self.dataStaging = []
		""" List of data staging elements for the job to execute """
		
		if not os.path.exists(jsdlFileName):
			raise Exception('Cannot find JSDL file ' + jsdlFileName)
		
		self._parseJsdl(jsdlFileName)

	# Validation here is minimal as the job service has already validated the
	# JSDL against the XSD
	def _parseJsdl(self, fileName):
		doc = minidom.parse(fileName)
		jobDef = doc.documentElement
		jobDesc = jobDef.getElementsByTagNameNS(JSDL_NS, "JobDescription")[0]

		# Application element
		app = jobDesc.getElementsByTagNameNS(JSDL_NS, "Application")[0]
		self.applicationName = XMLUtils.getSingletonTextContents(app, JSDL_NS, "ApplicationName")
		self.applicationVersion = XMLUtils.getSingletonTextContents(app, JSDL_NS, "ApplicationVersion")
		
		jobId = jobDesc.getElementsByTagNameNS(JSDL_NS, "JobIdentification")
		if jobId.length > 0:
			self.jobName = XMLUtils.getSingletonTextContents(jobId[0], JSDL_NS, "JobName")
		
		# POSIXApplication element
		posix = app.getElementsByTagNameNS(JSDL_POSIX_NS, "POSIXApplication")
		if posix.length > 0:
			for node in posix[0].childNodes:
				if node.nodeType != Node.ELEMENT_NODE or node.namespaceURI != JSDL_POSIX_NS:
					continue
				data = XMLUtils.getElementTextContents(node)
				if node.localName == 'Argument':
					self.arguments.append(data)
				elif node.localName == 'Executable':
					self.executableName = data
					#platformUtils.formatCygwinPath(data)
				else:
					self.posixConstraints[node.localName] = data
		
		# Resources element
		resources = jobDesc.getElementsByTagNameNS(JSDL_NS, "Resources")
		if resources.length > 0:
			for node in resources[0].childNodes:
				if node.nodeType == Node.ELEMENT_NODE and node.namespaceURI == JSDL_NS:
					self._parseResourcesElement(node)
					
		# DataStaging element
		dataStaging = jobDesc.getElementsByTagNameNS(JSDL_NS, "DataStaging")
		if dataStaging.length > 0:
			dsIndex = 0
			for ds in dataStaging:
				dataStagingElement  =  DataStagingElement()
				for node in ds.childNodes:
					if node.nodeType == Node.ELEMENT_NODE and node.namespaceURI == JSDL_NS:
						self.parseDataStagingElement(node, dataStagingElement)
				self.dataStaging.append(dataStagingElement)	
				dsIndex = dsIndex + 1	
									
		# Application element
		application = jobDesc.getElementsByTagNameNS(JSDL_NS, "Application")
		for node in application[0].childNodes:
			if node.nodeType == Node.ELEMENT_NODE:
				self.parseApplicationElement(node)		
		#posixApplication = application.getElementsByTagNameNS(JSDL_POSIX_NS, "POSIXApplication")
		#targetUri = XMLUtils.getElementTextContents(posixApplication[0])							
	
	def parseApplicationElement(self, node):
		if node.localName == "ApplicationName":
			applicationName = XMLUtils.getElementTextContents(node)	
		elif node.localName == "POSIXApplication":
			for posixNode in node.childNodes:
				if node.nodeType == Node.ELEMENT_NODE and node.namespaceURI == JSDL_POSIX_NS and not node.localName == None:
					self.parsePosixApplicationElement(posixNode)

	
	def parsePosixApplicationElement(self, node):
		if node.localName == "Executable":
			execName = XMLUtils.getElementTextContents(node)
		elif node.localName == "Argument":
			argument = XMLUtils.getElementTextContents(node)
		elif node.localName == "Input":
			argument = XMLUtils.getElementTextContents(node)
		elif node.localName == "Output":
			argument = XMLUtils.getElementTextContents(node)
		elif node.localName == "Error":
			argument = XMLUtils.getElementTextContents(node)
		elif node.localName == "Environment":
			envVariableValue = XMLUtils.getElementTextContents(node)
			envVariableName = node.getAttribute('name')
														
			
	def parseDataStagingElement(self, node, dataStagingElement):
		if node.localName == "FileName":
			fileName = XMLUtils.getElementTextContents(node)	
			dataStagingElement.setFileName(fileName)
		elif node.localName == "DeleteOnTermination":
			deleteOnTermination = XMLUtils.getElementTextContents(node)
			dataStagingElement.setDeleteOnTermination(deleteOnTermination)
		elif node.localName == "CreationFlag":
			creationFlag = XMLUtils.getElementTextContents(node)
			dataStagingElement.setCreationFlag(creationFlag)
		elif node.localName == "Source":
			srcUriElement = node.getElementsByTagNameNS(JSDL_NS, "URI")
			srcUri = XMLUtils.getElementTextContents(srcUriElement[0])
			dataStagingElement.setSource(srcUri)
		elif node.localName == "Target":
			targetUriElement = node.getElementsByTagNameNS(JSDL_NS, "URI")
			targetUri = XMLUtils.getElementTextContents(targetUriElement[0])
			dataStagingElement.setTarget(targetUri)
			
	def _parseResourcesElement(self, node):
		if node.localName == "FileSystem":
			node = node.getElementsByTagNameNS(JSDL_NS, "DiskSpace")[0]
		if node.localName == "CPUArchitecture":
			self.cpuArchitecture = XMLUtils.getSingletonTextContents(node, JSDL_NS, "CPUArchitectureName")
		elif node.localName == "OperatingSystem":
			osType = XMLUtils.getSingletonElement(node, JSDL_NS, "OperatingSystemType")
			self.operatingSystem = XMLUtils.getSingletonTextContents(osType, JSDL_NS, "OperatingSystemName")	
		elif node.localName == "CandidateHost":
			hostNames = node.getElementsByTagNameNS(JSDL_NS, "HostName")
			for hostName in hostNames:
				self.candidateHosts.append(XMLUtils.getElementTextContents(hostName))
		elif node.localName in SUPPORTED_RANGE_RESOURCES:
			name = node.localName
			value = self._parseRangeElement(node)
			
			self.rangeResources[name] = {
				"lower": value["lower"],
				"upper": value["upper"]
			}
	
	def _parseSingletonRangeElement(self, parentElement, elementName):
		nodeList = parentElement.getElementsByTagNameNS(JSDL_NS, elementName)
		if nodeList.length == 0:
			return {"lower": None, "upper": None}
		return self._parseRangeElement(nodeList[0])
	
	# This is pretty nasty
	# It tries to parse the contents of a jsdl:RangeValue_Type element
	# It ignores all the complicated stuff and simply returns a lower and
	# upper bound in a dictionary.  Values are None if unspecified.
	def _parseRangeElement(self, rangeElement):
		lower = None
		upper = None
		for node in rangeElement.childNodes:
			if node.nodeType != Node.ELEMENT_NODE or node.namespaceURI != JSDL_NS:
				continue
			if node.localName == "LowerBoundedRange":
				val = float(XMLUtils.getElementTextContents(node))
				lower = _min(val, lower)
			elif node.localName == "UpperBoundedRange":
				val = float(XMLUtils.getElementTextContents(node))
				upper = max([val, upper])
			elif node.localName == "Exact":
				val = float(XMLUtils.getElementTextContents(node))
				lower = _min(val, lower)
				upper = max([val, upper])
			elif node.localName == "Range":
				val = float(XMLUtils.getSingletonTextContents(node, JSDL_NS, "LowerBound"))
				lower = _min(val, lower)
				val = float(XMLUtils.getSingletonTextContents(node, JSDL_NS, "UpperBound"))
				upper = max([val, upper])
		return {"lower": lower, "upper": upper}
	
	
