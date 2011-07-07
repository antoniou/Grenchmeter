#!/usr/bin/python
 
import xml.sax.handler
import os

class OneInfoParser:
	def __init__(self, oneConnection, credentials):
		self.oneConnection = oneConnection
		self.handler = OneInfoHandler()
		self.credentials = credentials
		 
	def getOneInfo(self,imageID):
		self.__parseVMInfo(imageID)
		state = self.__getState() 
		IP = self.__getIP()
		ID = self.__getID()
		
		return (state,IP,ID)
		
	def __parseVMInfo(self,imageID):
		vminfo = self.oneConnection.one.vm.info(self.credentials,imageID)
		print  vminfo[1]
		xml.sax.parseString(vminfo[1],self.handler)
		
		
	def __getState(self):
		return int(self.handler.state)
	
	def __getIP(self):
		return self.handler.IP
	
	def __getID(self):
		return self.handler.ID
		
class OneInfoHandler(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.state=0
		self.inState = 0
		self.inIP = 0
		self.inID = 0
		
	def startElement(self,name,attributes):
		if name=="LCM_STATE":
			self.buffer=""
			self.inState = 1
		if name=="IP":
			self.buffer=""
			self.inIP = 1
		if name=="ID":
			self.buffer=""
			self.inID = 1

	def endElement(self,name):
		if name=="LCM_STATE":
			self.inState = 0
			self.state=self.buffer
		if name=="IP":
			self.inIP = 0
			self.IP=self.buffer
		if name=="ID":
			self.inIP = 0
			self.ID=self.buffer
			

	def characters(self, data):
		if self.inState or self.inIP or self.inID:
			self.buffer += data

