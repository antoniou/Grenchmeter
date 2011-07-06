
"""  

NAME

    Grenchmeter -- Cloud Performance Analysis tool

SYNOPSIS
    %(progname)s [OPTIONS]

DESCRIPTION
             

OPTIONS:

"""

__proggy = "grenchmeter";
__rev = "0.01";
__proggy_stamp__ = "%s v%s" % (__proggy, __rev);
__author__ = 'Athanasios Antoniou';
__email__ = 'A.Antoniou at ewi.tudelft.nl';
__file__ = 'Grenchmeter.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2011/04/04 14:12:39 $"
__copyright__ = "Copyright (c) 2011 Athanasios Antoniou"
__license__ = "Python" 

import os
import sys
import getopt
import threading
import socket
import time
import smtplib
import signal
from email.mime.text import MIMEText
from time import gmtime, strftime

if "Cmeter/ec2bd" not in sys.path:
    sys.path.append("Cmeter/ec2bd")
if "Cmeter/analysis/" not in sys.path:
    sys.path.append("Cmeter/analysis/")

import GrenchmarkController
import analyze
from ec2bd import Cmeter

DEFAULT_CONFIG_FILE   = 'Cmeter/config/das4.config'
DEFAULT_WORKLOAD_FILE = 'Grenchmark/wl-desc.in'
WORKLOAD_OUTDIR       = 'wload_out'

def version():
    print "Version: ", __version__
    print "Date: ", __date__
    print __copyright__, "(", __email__, ")"

def usage(progname):
    print __doc__ % vars() 

def sendExperimentCompletionEmail(email):

    # Open a plain text file for reading.  For this example, assume that
    # the text file contains only ASCII characters.

    msg = MIMEText("The performance analysis experiment has concluded on {0}".format(strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())))

    # me == the sender's email address
    # you == the recipient's email address
    msg['Subject'] = 'Experiment completion notification'
    msg['From'] = "Grenchmeter"
    msg['To'] = email
    
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP()
    s.connect()
    s.sendmail("Grenchmeter", [email], msg.as_string())
    s.quit()


def getcmdLineArguments(argv):
    cMeterConfigFile = DEFAULT_CONFIG_FILE
    workloadFile     = DEFAULT_WORKLOAD_FILE

    try:                                
        opts, args = getopt.getopt(argv, "c:w:h", ["config=,workload=,help"])
    except getopt.GetoptError:
        usage(os.path.basename(sys.argv[0]))
        sys.exit(2)
        
    for opt, arg in opts:   
        if opt in ("-c", "--config"):
            cMeterConfigFile = arg
            print "Cmeter configuration file: %s" % cMeterConfigFile
        elif opt in ("-w","--workload"):
            workloadFile = arg
            print "Workload file: %s" % workloadFile
        elif opt in ("-h","--help"):
            usage(os.path.basename(sys.argv[0]))
            sys.exit()
    
    return cMeterConfigFile, workloadFile
            
def submitWorkloadDedicated(Grenchmark, cMeter):
    workloadSubmitFile = Grenchmark.workloadConfig.getWorkloadOutDir() + "/wl-to-submit.wl00"
    
    # Submit workload in dedicated mode. Results
    # will be stored in the used DB"    
    submitArgs = { workloadSubmitFile:'',
                   '--dedicated':''}
    
    print "!STATUS Submitting workload in DEDICATED mode"
    Grenchmark.submitWorkload(submitArgs)
    
    cMeter.storeDedStatsToDB()

def generateFixedUtilizationWorkload(Grenchmark, workloadOutDir):
    Grenchmark.defineArrivalDistrParameters()
    
    Grenchmark.verifyUtilization()
    
    while not Grenchmark.utilSatisfied():
        print "!STATUS: Utilization factor not satisfied. Re-generating workload"
        # Generate workload using the distribution with the estimated parameters
        Grenchmark.generateWorkload({"--outdir":workloadOutDir},useArrivalDistribution = True)
    
        Grenchmark.verifyUtilization()
                
def submitWorkload(Grenchmark, cMeter):
    # Now submit the actual workload
    print "!STATUS Submitting actual workload"
    workloadSubmitFile = Grenchmark.workloadConfig.getWorkloadOutDir() + "/wl-to-submit.wl00"
    submitArgs = { workloadSubmitFile:''}
    submitStart = time.time()
    Grenchmark.submitWorkload(submitArgs)
    submitDuration = time.time() - submitStart
    cMeter.storeStatsToDB()

    print "Real workload duration: ",submitDuration
    
def analyzeData():
    analysis = analyze.Analysis()
    analysis.analyze() 
    
def initServices(argv, workloadOutDir):       
    cMeterConfigFile, workloadFile = getcmdLineArguments(argv)
    
    workloadConfig = GrenchmarkController.WorkloadConfig(workloadFile, workloadOutDir)
    # initialize Cmeter thread
    cMeter = Cmeter(cMeterConfigFile)
    cMeter.initDaemon()
    
    Grenchmark = GrenchmarkController.GrenchmarkController(cMeter, workloadConfig)
    
    return Grenchmark, cMeter, workloadConfig
    
def main(argv):  
    
    workloadOutDir   = WORKLOAD_OUTDIR
    Grenchmark, cMeter, workloadConfig = initServices(argv, workloadOutDir)
    
    # Generate workload using workloadFile
    Grenchmark.generateWorkload({"--outdir":workloadOutDir}, useArrivalDistribution = False)
    
#    submitWorkloadDedicated(Grenchmark, cMeter)
    
    if workloadConfig.systemUtilizationMode():
        generateFixedUtilizationWorkload(Grenchmark, workloadOutDir)
        
    submitWorkload(Grenchmark, cMeter)
    
    analyzeData()
    
    cMeter.stopDaemon()
    
    #sendExperimentCompletionEmail(cMeter.configurationManager.getEmail())    

if __name__ == "__main__":
    main(sys.argv[1:])
