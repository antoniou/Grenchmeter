import sys

class LoadBalancingResourceSelectionPolicy:
    def __init__(self,listOfResources):
        self.name = "Load Based Resource Selection Policy"
        self.listOfResources = listOfResources
        
    def getName(self):
        return self.name
    
    def getNextResource(self):
        return self.findResourceWithMinLoad()
    
    def findResourceWithMinLoad(self):
        currentMin = sys.maxint
        minInstance = None
        for instance in self.listOfResources:
            nJobs = instance.getNumExecutingJobs()
            print "Instance {0} has {1} running jobs ".format(instance.getID(),nJobs)
            if nJobs < currentMin:
                minInstance = instance
                currentMin = nJobs
        
        return minInstance 
        
    
    