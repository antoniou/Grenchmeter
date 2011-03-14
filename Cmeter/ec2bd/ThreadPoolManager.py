import sys

import workerpool

class ThreadPoolManager:
    
    def __init__(self, poolSize):
        self.workerPool = workerpool.WorkerPool(size=int(poolSize), maxjobs=-1)
        
    def shutdown(self):
        self.workerPool.shutdown()
        self.workerPool.wait()
        
    def processJob(self, job): # job is of type workerpool.Job
        self.workerPool.put(job)
        