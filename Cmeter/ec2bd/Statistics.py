import threading

class Statistics:
    def __init__(self):
        self.statistics ={}
        # no need for fine grained lock ..
        # use this lock for all variables
        self.incrementLock = threading.Lock() 
        
        self.statistics['totalResourceSelectionAlgorithmTime']=0
        self.totalResourceSelectionTimeCount = 0 # for calculating averages
        
        self.statistics['totalSshBegin']=0
        self.totalSshBeginCount = 0
        
        self.statistics['totalSshEnd']=0
        self.totalSshEndCount = 0

        self.statistics['totalSsh']=0
        self.totalSshCount = 0
                
        self.statistics['totalResourceManagerConnect']=0
        self.totalResourceManagerConnectCount = 0
        
        self.statistics['totalResourceManagerGetListOfImages']=0
        self.totalResourceManagerGetListOfImagesCount = 0
        
        self.statistics['totalResourceReservationTime']=0
        self.totalResourceReservationTimeCount = 0
        
        self.statistics['totalResourceReleaseTime']=0
        self.totalResourceReleaseTimeCount = 0
        
        self.statistics['totalSshOverheadWhilePollingIfResourcesAreRunning']=0
        self.totalSshOverheadWhilePollingIfResourcesAreRunning = 0        
 
    def addTotalSshOverheadWhilePollingIfResourcesAreRunning(self, timeToAdd):
        try:
            self.incrementLock.acquire()
            self.statistics['totalSshOverheadWhilePollingIfResourcesAreRunning']+= timeToAdd
            self.totalSshOverheadWhilePollingIfResourcesAreRunning += 1
        finally:
            self.incrementLock.release()
                
    def addToTotalResourceSelectionAlgorithmTime(self, timeToAdd):
        try:
            self.incrementLock.acquire()
            self.statistics['totalResourceSelectionAlgorithmTime']+= timeToAdd
            self.totalResourceSelectionTimeCount += 1
        finally:
            self.incrementLock.release()
            
    def addToTotalSshBeginTime(self, timeToAdd):
        try:
            self.incrementLock.acquire()
            self.statistics['totalSshBegin']+= timeToAdd
            self.totalSshBeginCount += 1
        finally:
            self.incrementLock.release()
            
    def addToTotalSshEndTime(self, timeToAdd):
        try:
            self.incrementLock.acquire()
            self.statistics['totalSshEnd']+= timeToAdd
            self.totalSshEndCount += 1
        finally:
            self.incrementLock.release()  
       
    def addToTotalSshTime(self, timeToAdd):
        try:
            self.incrementLock.acquire()
            self.statistics['totalSsh']+= timeToAdd
            self.totalSshCount += 1
        finally:
            self.incrementLock.release()            
    def addToTotalResourceManagerConnectTime(self, timeToAdd):
        try:
            self.incrementLock.acquire()
            self.statistics['totalResourceManagerConnect']+= timeToAdd
            self.totalResourceManagerConnectCount += 1
        finally:
            self.incrementLock.release()                                              

    def addToTotalResourceManagerGetListOfImagesTime(self, timeToAdd):
        try:
            self.incrementLock.acquire()
            self.statistics['totalResourceManagerGetListOfImages']+= timeToAdd
            self.totalResourceManagerGetListOfImagesCount += 1
        finally:
            self.incrementLock.release()
            
    def addToTotalResourceReservationTime(self, timeToAdd):
        try:
            self.incrementLock.acquire()
            self.statistics['totalResourceReservationTime']+= timeToAdd
            self.totalResourceReservationTimeCount += 1
        finally:
            self.incrementLock.release()
            
    def addToTotalResourceReleaseTime(self, timeToAdd):
        try:
            self.incrementLock.acquire()
            self.statistics['totalResourceReleaseTime']+= timeToAdd
            self.totalResourceReleaseTimeCount += 1
        finally:
            self.incrementLock.release()
    
    def printStatistics(self):
        print "[Total Time For The Resource Selection Algorithm]"
        print "\tTotal Time For The Resource Selection Algorithm is %4.3f" % (self.statistics['totalResourceSelectionAlgorithmTime'])
        if self.totalResourceSelectionTimeCount != 0:
            print "\tAverage Time For The Resource Selection Algorithm is %4.3f" % (self.statistics['totalResourceSelectionAlgorithmTime']/self.totalResourceSelectionTimeCount)
        
        print "[Total Time For Beginning SSH Sessions]"
        print "\tTotal Time For Beginning SSH Sessions is %4.3f" % (self.statistics['totalSshBegin'])
        if self.totalSshBeginCount != 0:
            print "\tAverage Time For Beginning SSH Sessions is %4.3f" % (self.statistics['totalSshBegin']/self.totalSshBeginCount)
        
        print "[Total Time For Ending SSH Sessions]"
        print "\tTotal Time For Ending SSH Sessions is %4.3f" % (self.statistics['totalSshEnd'])
        if self.totalSshEndCount != 0:
            print "\tAverage Time For Ending SSH Sessions is %4.3f" % (self.statistics['totalSshEnd']/self.totalSshEndCount)
            
        print "[Total Time For SSH Sessions <whole sessions>]"
        print "\tTotal Time For SSH Sessions <whole sessions> is %4.3f" % (self.statistics['totalSsh'])
        if self.totalSshCount != 0:
            print "\tAverage Time For SSH Sessions <whole sessions> is %4.3f" % (self.statistics['totalSsh']/self.totalSshCount)            
        
        print "[Total Time For Connecting To The EC2]"
        print "\tTotal Time For Connecting To The EC2 is %4.3f" % (self.statistics['totalResourceManagerConnect'])
        if self.totalResourceManagerConnectCount != 0:
            print "\tAverage Time For Connecting To The EC2 is %4.3f" % (self.statistics['totalResourceManagerConnect']/self.totalResourceManagerConnectCount)
        
        print "[Total Time For Retrieving The Public Image List From The EC2]"
        print "\tTotal Time For Retrieving The Public Image List From The EC2 is %4.3f" % (self.statistics['totalResourceManagerGetListOfImages'])
        if self.totalResourceManagerGetListOfImagesCount != 0:
            print "\tAverage Time For Retrieving The Public Image List From The EC2 is %4.3f" % (self.statistics['totalResourceManagerGetListOfImages']/self.totalResourceManagerGetListOfImagesCount)
        
        print "[Total Time For Reserving Resources on EC2]"
        print "\tTotal Time For Reserving Resources on EC2 is %4.3f" % (self.statistics['totalResourceReservationTime'])
        if self.totalResourceReservationTimeCount != 0:
            print "\tAverage Time For Reserving Resources on EC2 is %4.3f" % (self.statistics['totalResourceReservationTime']/self.totalResourceReservationTimeCount)
            
        print "[Total SSH Overhead While Polling Whether Resources Are in \'Running\' State"
        print "\tTotal SSH Overhead While Polling Whether Resources Are in \'Running\' State is %4.3f" % (self.statistics['totalSshOverheadWhilePollingIfResourcesAreRunning'])
        if self.totalSshOverheadWhilePollingIfResourcesAreRunning != 0:
            print "\tTotal SSH Overhead While Polling Whether Resources Are in \'Running\' State is %4.3f" % (self.statistics['totalSshOverheadWhilePollingIfResourcesAreRunning']/self.totalSshOverheadWhilePollingIfResourcesAreRunning)
        
        print "[Total Time For Releasing Resources on EC2]"
        print "\tTotal Time For Releasing Resources on EC2 is %4.3f" % (self.statistics['totalResourceReleaseTime'])
        if self.totalResourceReleaseTimeCount != 0:
            print "\tAverage Time For Releasing Resources on EC2 is %4.3f" % (self.statistics['totalResourceReleaseTime']/self.totalResourceReleaseTimeCount)
