from PersistentStatistics import *
import workerpool
import time


class StatsUpdater(workerpool.Job):
    def __init__(self,statistics, dbStatisticsHolder, resourceManager): 
        self.statistics = statistics
        self.dbStats = dbStatisticsHolder
        self.resourceManager = resourceManager

    def run(self):
        stats = self.statistics
        for k in stats:
            if k == 'jobExec':
                jobExec = float(stats[k])
            if k == 'hashValue':
                hashValue = stats[k]
            if k == 'fileTransfer':
                fileTransfer = float(stats[k])
            if k == 'overAllExec':
                overAllExec = float(stats[k])
            if k == 'jobName':
                jobName = stats[k]
            if k == 'cpuTime':
                cpuTime = stats[k]
            if k == 'ded':
                dedicatedMode = stats[k]
            if k == 'instance':
                instanceId = stats[k]
                            
        
        if dedicatedMode == 'True':
#            self.dbStats.updateStatistics(jobName,ded_runtime = jobExec )
            self.dbStats.updateDedStatistics(hashValue,jobExec )
        else:
            job_statistics_received = time.time()
            arrivalTime = float(self.dbStats.getStatistics(jobName).job_arrival)
            response_time =  job_statistics_received - arrivalTime
            ded_runtime = self.dbStats.getKnownStats(hashValue)['jobExec']
            self.dbStats.updateStatistics(jobName,
                                          None,None,None,
                                          None,None,None,
                                          None,None,None,
                                          None,None,
                                          job_statistics_received,
                                          overAllExec,
                                          jobExec,
                                          fileTransfer,
                                          cpuTime,
                                          ded_runtime,
                                          None)    
        
            self.resourceManager.updateResourcePolicyStatus(instanceId,response_time)
                
