import paramiko
import socket
import sys
import time

class SshUtils:
    def __init__(self, host=None, user=None, password=None, keyFileName=None):
        if keyFileName==None:
            self.pKey = None
        else:
            self.pKey = paramiko.RSAKey(None, None, keyFileName, password, None, None)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.host = host
        self.user = user
        self.password = password
        self.keyFileName= keyFileName

    def doConnect(self):
        try:
            self.client.connect(self.host, 22, self.user, self.password, self.pKey, None, 180, True,True)
            return True
        except:
            #print sys.exc_info()
            return False

    def reset(self):
        self.disconnect()
        connected = self.doConnect()
        while not connected:
            time.sleep(0.2)
            print "Connection failed. Retrying..."
            connected = self.doConnect()
        
    def executeCommand(self,cmd):
        MAX_RETRIES = 100
        executed = False
        attempt = 0
        
#        while not executed and attempt < MAX_RETRIES:
        while not executed:
            executed = self.__execute(cmd)
            if not executed:
                time.sleep(0.1)
            attempt += 1
            
        return executed 
              
    def __execute(self, cmd):
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd)
            return True
        except: # can not open session to server
            return False
            
    def disconnect(self):
        self.client.close()
        
"""
    utils = SshUtils(host='fs3.das3.tudelft.nl', user='yigitbas', password='xWXP96m7')
    utils.doConnect()
    utils.executeCommand('ls')
    utils.disconnect()
"""