####################################################
#  Step 4: This source file is the execution agent 
#          running on the virtual resource, responsible
#          for running the executable.
#          This execution agent runs the executable and reports
#          the gathered statistics back to C-meter.
####################################################

import sys
import os
import getopt
import time
import subprocess
import socket
import math

 # Number of iterations for dedicated mode
ITERATIONS = 50

class ElapsedTimes(list):
    
    " Returns the median of a list of numeric values"    
    def getMedian(self):
      if len(self) % 2 == 1:
        return self[(len(self)+1)/2-1]
      else:
        lower = self[len(self)/2-1]
        upper = self[len(self)/2]
      return (float(lower + upper)) / 2
  
    def getQuartile(self,quartile):
        
        if quartile == 'upper':
            q = 0.75
        else:
            q = 0.25
        # If size is odd        
        if len(self) % 2 == 1:
            return self[round(q*len(self))]
        else:
            lower =  self[int(math.floor(q * len(self)))-1]
            upper =  self[int(math.floor(q * len(self)))]
            return (lower + upper)/2

    def removeOutliers(self):
        #Find outlier values
        self.sort()
        median = self.getMedian()
        
        # Find outliers
        upperQuartile = self.getQuartile('upper')
        lowerQuartile = self.getQuartile('lower')
        
        iq_range = upperQuartile -  lowerQuartile
        upperBound = upperQuartile + iq_range * 1.5
        lowerBound = lowerQuartile - iq_range * 1.5
        print "Upper =", upperQuartile, " lower =",lowerQuartile
        print "UpperBound =", upperBound, " lower =",lowerBound
        
        # Remove all lower outliers
        for value in self:
            if value < lowerBound:
                self.remove(value)
            else:
                break
            
        self.reverse()
        # Remove all higher outliers
        for value in self:
            if value > upperBound:
                self.remove(value)
            else:
                break
            
    "Finds the average of the list values"
    def average(self):
        avg = 0
        for value in self:
            avg +=value
        
        return avg/len(self)
    
    def processData(self):
        self.removeOutliers()
        return self.average()
        
####################################################
# forceSend connects to the C-meter server and sends  
# "string" containing the results of the job execution
####################################################
def forceSend(cmeterHost,string):
    sent = False
    while not sent:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(cmeterHost)
            s.send(string)
            print 'String sent:',string
            s.close()
            sent = True
        except:
            print "Unexpected error:", sys.exc_info()[0]
            if s != None:
                try:
                    s.close()
                except:
                    pass 
    
    return sent

def main(argv):  
    
    dedicatedMode=False
    # Command line options
    opts, args = getopt.getopt(argv, "u:c:p:e:f:j:i:d:h:", ["url=","cmeterurl=","cmeterport=","exec=","files=","job=","hash=","instance=","dedicated"])
    for opt, arg in opts:   
        if opt in ("-u", "--url"):
            url = arg
            print "url %s" % url
        if opt in ("-c","--cmeterurl"):
            cmeterUrl = arg
            print "cmeter Url %s" % cmeterUrl
        if opt in ("-p","--cmeterport"):
            cmeterPort = int(arg)
            print "cmeter Port %s" % cmeterPort    
        if opt in ("-e", "--exec"):
            commandToExec = arg
            print "commandToExec %s" % commandToExec
        if opt in ("-f", "--files"):
            filesToDownload = arg
            print "filesToDownload ", filesToDownload            
        if opt in ("-j", "--job"):
            jobName = arg
            print "jobName ", jobName 
        if opt in ("-h", "--hash"):
            hashValue = arg
            print "hashValue ", hashValue 
        if opt in ("-i", "--instance"):
            instance = arg
            print "instance ", instance
        if opt in ("-d", "--dedicated"):
            dedicatedMode=True
            print "Running in Dedicated mode"
    
    startOverallExec = time.time()
    os.chdir(jobName)
    
    startFileTransfer = time.time()
    
    # Files are downloaded from the http server
    files = filesToDownload.split(',')
    for file in files:
        start = time.time()
        file.strip()
        wgetCmd = "wget %s "  % (url+'/'+file)
        result=os.system (wgetCmd)
        
        #For files of zero size that are not downloadable!
        if result!=0:
            os.system("touch %s " % file)
        
#        os.system("mv %s %s " % (file,jobName))

    endFileTransfer = time.time()  
    
    
    if dedicatedMode:
        iter = ITERATIONS
    else:
        iter = 1
        
    print "Files to download", filesToDownload.replace(',',' ')
    #execution
    os.system("chmod a+x " + filesToDownload.replace(',',' '))
    
    
    elapsed = ElapsedTimes()
    elapsedCPUtime = ElapsedTimes()
    for i in range(iter):
        #Start of execution phase
        startExec = time.time()
        startCPUtime = time.clock()
        #Execute command
        os.system("./"+commandToExec)
        
        endExec = time.time()
        endCPUtime = time.clock()
        elapsed.append(endExec - startExec)
        elapsedCPUtime.append(endCPUtime - startCPUtime)
    
        
    endOverallExec = time.time()
    elapsedOverall = endOverallExec - startOverallExec
    fileTransferElapsed = endFileTransfer - startFileTransfer
    
    if dedicatedMode:
        avg_elapsed = elapsed.processData()
        avg_elapsedCPU = elapsedCPUtime.average()
    else:
        avg_elapsed = elapsed[0]
        avg_elapsedCPU = elapsedCPUtime[0]
    
    # Report sent back to C-meter
    strToSend = 'cmd:stats,jobName='+str(jobName)+ ',hashValue=' + str(hashValue)+ ',jobExec='+str(avg_elapsed)+\
                ',fileTransfer='+str(fileTransferElapsed)+',overAllExec='+\
                str(elapsedOverall) + ",cpuTime=" + str(avg_elapsedCPU) +\
                ',instance='+str(instance) + ',ded='+ str(dedicatedMode)
    # Send back to C-meter
    forceSend((cmeterUrl,cmeterPort),strToSend)
    
    
if __name__ == "__main__":
    main(sys.argv[1:])