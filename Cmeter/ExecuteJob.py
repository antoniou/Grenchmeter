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
            
            
def main(argv):  
    # Command line options
    opts, args = getopt.getopt(argv, "u:c:p:e:f:j:i:", ["url=","cmeterurl=","cmeterport=","exec=","files=","job=","instance="])
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
        if opt in ("-i", "--instance"):
            instance = arg
            print "instance ", instance            

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
    
    #Start of execution phase
    startExec = time.time()
    
    print "Files to download", filesToDownload.replace(',',' ')
    #execution
    os.system("chmod a+x " + filesToDownload.replace(',',' '))
    os.system("./"+commandToExec)
    
    endExec  = time.time()
    elapsed = endExec -  startExec
    endOverallExec = time.time()
    elapsedOverall = endOverallExec - startOverallExec
    fileTransferElapsed = endFileTransfer - startFileTransfer
    
    # Report sent back to C-meter
    strToSend = 'cmd:stats,jobName='+str(jobName)+',jobExec='+str(elapsed)+',fileTransfer='+str(fileTransferElapsed)+',overAllExec='+str(elapsedOverall) + ',instance='+str(instance)
    # Send back to C-meter
    forceSend((cmeterUrl,cmeterPort),strToSend)
    
if __name__ == "__main__":
    main(sys.argv[1:]) 
