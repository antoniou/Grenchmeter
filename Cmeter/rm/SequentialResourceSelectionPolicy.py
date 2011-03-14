import threading

class SequentialResourceSelectionPolicy:
    def __init__(self,listOfResources):
        self.name = "Sequential Resource Selection Policy"
        self.currentResourceIndex = 0
        self.listOfResources = listOfResources
        self.lock = threading.Lock()
        
    def getName(self):
        return self.name
    
    def getNextResource(self):
        self.lock.acquire()
        try:
            size =  len(self.listOfResources)
            nextResource = self.listOfResources[self.currentResourceIndex]
            self.currentResourceIndex = self.currentResourceIndex + 1
            if(self.currentResourceIndex == size): # reset index
                self.currentResourceIndex = 0
            return nextResource
        finally:
            self.lock.release()
        
    
    