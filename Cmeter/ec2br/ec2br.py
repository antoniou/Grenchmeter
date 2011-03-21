import sys
import os
import getopt
import socket


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
	opts, args = getopt.getopt(argv, "p:j:c:u:", ["port=","jsdl=","cmd=","url="])
	cmdExists = False
	
	for opt, arg in opts:   
		if opt in ("-u", "--url"):
			url = arg
			print "url %s" % url
		if opt in ("-p", "--port"):
			port = arg
			print "port %s" % port
		elif opt in ("-j", "--jsdl"):
			jsdlFile = arg
			print "jsdlFile %s " % jsdlFile
		elif opt in ("-c", "--cmd"):
			cmd = arg
			print "cmd %s" % cmd
			cmdExists = True			

	if cmdExists:
         sent = forceSend("cmd:"+cmd, url, int(port))
	else:
         sent = forceSend(jsdlFile, url, int(port))


if __name__ == "__main__":

    main(sys.argv[1:]) 
