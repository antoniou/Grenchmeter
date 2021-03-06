import threading
import random
import math
    
class PredictiveResourceSelectionPolicy:
    
    def __init__(self,listOfResources):
        self.name = "Predictive Resource Selection Policy"
        self.listOfResources = []
        for instance in listOfResources:
            self.listOfResources.append(Resource(instance))
        self.lock = threading.Lock()
        
    def getNextResource(self):
        self.lock.acquire()
        try:
            return self.getResourceWithMinimumPredictedResponseTime()
        finally:
            self.lock.release()
            
    def getName(self):
        return self.name            
        
    def comparisonFunction(self, r1, r2):
        if r1.lastPredictedResponseTime == r2.lastPredictedResponseTime:
            return 0
        elif r1.lastPredictedResponseTime < r2.lastPredictedResponseTime:
            return -1
        else:
            return 1
    
    def getResourceWithMinimumPredictedResponseTime(self):
        self.listOfResources.sort(self.comparisonFunction)
        unusedResources = []
        for r in self.listOfResources: # determine unused resources 
            if r.lastPredictedResponseTime == -1:
                unusedResources.append(r)
        if len(unusedResources) > 0:
            return self.getRandomElement(unusedResources).instance
        return self.listOfResources[0].instance
    
    def getRandomElement(self, listParameter):
        return listParameter[ random.randint(0, len(listParameter) - 1) ]

    def updateResourceState(self, instanceId, responseTime):
        self.lock.acquire()
        try:
            for resource in self.listOfResources:
                if resource.instance.id == instanceId:
                    resource.update(responseTime)
        finally:
            self.lock.release()        
            

class Resource: 
    def __init__(self, instance):                              
        self.instance = instance # ec2 instance 
        # self.last2ResponseTimes[1] n-1. response time
        # self.last2ResponseTimes[0] n-2. response time
        self.last2ResponseTimes = [-1,-1]
        self.lastPredictedResponseTime = -1
    
    def update(self, responseTime):
        self.last2ResponseTimes[0] = self.last2ResponseTimes[1]
        self.last2ResponseTimes[1] = float(responseTime)
        self.lastPredictedResponseTime = float(self.last2ResponseTimes[0] + self.last2ResponseTimes[1])/2
    
    def __str__(self):
        string = 'instanceid  = ' + str(self.instance.id) + ' lastPredictedResponseTime = ' + str(self.lastPredictedResponseTime)  
        
    
    