"""
NAME
    ec2br -- Cmeter job sumbitter
    
SYNOPSIS
    %(progname)s [OPTIONS]
    
DESCRIPTION
    ec2br submits a job to the Cmeter daemon
    
OPTIONS
    Arguments
        --help
            Print this help and exit
            
        --url <cmeter_url>, -u <cmeter_url> 
            Url of the Cmeter process
            
        --port <cmeter_port>, -p <cmeter_port>
            Port that the Cmeter process is listening to
            
        --cmd <command>, -c <command>
            Send a command to Cmeter,where command is:
                dump : dump previously collected statistics
                       to DB file
                stop : dump previously collected statistics
                       to DB file and stop the Cmeter daemon
                       
"""

import sys
import os
import getopt
import socket

def usage(progname):
    print __doc__ % vars() 
    
def forceSend(string, host, port):
    sent = False
    while not sent:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.send(string)
            s.close()
            sent = True
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print s
            if s != None:
                try:
                    s.close()
                except:
                    pass
    if sent != True:
        raise "COULD NOT SENT ...."

def main(argv):
    try:   
        opts, args = getopt.getopt(argv, "p:j:c:u:d", ["help","port=","jsdl=","cmd=","url=","dedicated"])
    except getopt.GetoptError:
        print "Error while converting options: unknown option(s) encountered.\n\n"
        usage(os.path.basename(sys.argv[0]))
        sys.exit(2)
    cmdExists = False
    # Default arguments
    url  = "localhost"
    port = "3000"
     
    dedicatedMode=False
    for opt, arg in opts:   
        if opt in ("--help"):
            usage(os.path.basename(sys.argv[0]))
            sys.exit()
        if opt in ("-u", "--url"):
            url = arg
#            print "url %s" % url
        elif opt in ("-p", "--port"):
            port = arg
#            print "port %s" % port
        elif opt in ("-j", "--jsdl"):
            jsdlFile = arg
#            print "jsdlFile %s " % jsdlFile
        elif opt in ("-c", "--cmd"):
            cmd = arg
#            print "cmd %s" % cmd
            cmdExists = True
        elif opt in ("-d","--dedicated"):
            dedicatedMode=True
#            print "Dedicated Mode On"
        else:
#            print "Unknown parameter", opt
            pass
    
    if cmdExists:
        stringToSend="cmd:"+cmd
    else:
        stringToSend=jsdlFile
        
    if dedicatedMode==True:
        stringToSend=stringToSend+" dedicated"
        
    sent=forceSend(stringToSend, url, int(port))
                   
if __name__ == "__main__":

    main(sys.argv[1:]) 
