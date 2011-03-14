import sys
import os
import socket

def main(argv):
    host=''
    backlog = 10000
    size = 1024*2
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host,3000))
    s.listen(backlog)
    host = socket.gethostname()
    print host
    client, address = s.accept()
    print 'connection from ' , client.getpeername()
    
if __name__ == "__main__":

    main(sys.argv[1:]) 