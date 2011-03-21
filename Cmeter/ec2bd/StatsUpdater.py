from PersistentStatistics import *
import workerpool
import time


#        job_name, job_arrival, 
#                                job_removed_from_queue, 
#                                resource_scheduling_algorithm_overhead, 
#                                ssh_session_begin, 
#                                ssh_open_conn_begin, 
#                                ssh_open_conn_end,
#                                ssh_execute_begin,
#                                ssh_execute_end,
#                                ssh_close_conn_begin,
#                                ssh_close_conn_end,
#                                ssh_session_end,
#                                job_statistics_received,
#                                overall_execution_time,
#                                job_execution_time,
#                                file_transfer_time,
#                                execution_machine

class StatsUpdater(workerpool.Job):
    def __init__(self,statistics, dbStatisticsHolder, resourceManager): 
        self.statistics = statistics
        self.dbStats = dbStatisticsHolder
        self.resourceManager=resourceManager

    def run(self):
        strings = self.statistics.split(',')
        for s in strings:
            keyVal=s.split('=')
            if len(keyVal) == 1:
                continue
            if keyVal[0] == 'jobExec':
                jobExec = float(keyVal[1])
                print 'jobExec is %s' %  keyVal[1]
            if keyVal[0] == 'fileTransfer':
                fileTransfer = float(keyVal[1])
                print 'fileTransfer is %s' %  keyVal[1]            
            if keyVal[0] == 'overAllExec':
                overAllExec = float(keyVal[1])
                print 'overAllExec is %s' %  keyVal[1]
            if keyVal[0] == 'jobName':
                jobName = keyVal[1]
                print 'jobName is %s' %  keyVal[1]
            if keyVal[0] == 'instance':
                instanceId = keyVal[1]
                print 'instance is %s' %  instanceId   
                            
        job_statistics_received = time.time()
        arrivalTime = float(self.dbStats.getStatistics(jobName).job_arrival)
        response_time =  job_statistics_received - arrivalTime
        self.dbStats.updateStatistics(jobName,
                                    None,
                                     None,
                                      None,
                                     None,
                                      None,
                                     None,
                                      None,
                                      None,
                                   None,
                                   None,
                                   None,
                                      job_statistics_received,
                                      overAllExec,
                                      jobExec,
                                      fileTransfer,
                                     None)    
        
        self.resourceManager.updateResourcePolicyStatus(instanceId,response_time)
                
