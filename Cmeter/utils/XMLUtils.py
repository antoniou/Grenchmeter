#!/usr/bin/python -tt
# -*- coding: UTF-8 -*-

__copyright__="""
#########################################################################
##
## © University of Southampton IT Innovation Centre, 2006
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
##      Created By :            David Sansome
##      Created Date :          2007/08/15
##      Created for Project:    SIMDAT
##
#########################################################################
##
##      Dependencies : none
##
#########################################################################
##
##      Last commit info:       $Author: ds $
##                              $Date: 2007-08-24 13:44:36 +0100 (Fri, 24 Aug 2007) $
##                              $Revision: 8206 $
##
#########################################################################"""

def getSingletonTextContents(parentElement, namespaceURI, elementName):
	nodeList = parentElement.getElementsByTagNameNS(namespaceURI, elementName)
	if nodeList.length == 0:
		return ""
	return getElementTextContents(nodeList[0])

def getSingletonElement(parentElement, namespaceURI, elementName):
	nodeList = parentElement.getElementsByTagNameNS(namespaceURI, elementName)
	if nodeList.length == 0:
		return None
	return nodeList[0]

def getElementTextContents(ele):
	ele.normalize()
	return ele.firstChild.data
