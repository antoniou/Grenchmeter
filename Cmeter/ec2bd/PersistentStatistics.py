import sys, time, datetime, os
from sqlite3 import dbapi2 as sqlite

import threading 
import logging
import AISQLiteUtils

class DatabaseStatistics:
    def __init__(self):
        self.statistics = {}
        self.lock = threading.Lock()
        

#
#jobName, stats.job_arrival, 
#                                stats.job_removed_from_queue, 
#                                stats.resource_scheduling_algorithm_overhead, 
#                                stats.ssh_session_begin, 
#                                stats.ssh_open_conn_begin, 
#                                stats.ssh_open_conn_end,
#                                stats.ssh_execute_begin,
#                                stats.ssh_execute_end,
#                                stats.ssh_close_conn_begin,
#                                stats.ssh_close_conn_end,
#                                stats.ssh_session_end,
#                                stats.job_statistics_received,
#                                stats.overall_execution_time,
#                                stats.job_execution_time,
#                                stats.file_transfer_time,
#                                stats.execution_machine  
                                
    def getStatistics(self, job_name):
            self.lock.acquire()
            try:      
                return self.statistics[job_name]
            finally:
                self.lock.release()       
                                               
    def updateStatistics(self, job_name, job_arrival, 
                                job_removed_from_queue, 
                                resource_scheduling_algorithm_overhead, 
                                ssh_session_begin, 
                                ssh_open_conn_begin, 
                                ssh_open_conn_end,
                                ssh_execute_begin,
                                ssh_execute_end,
                                ssh_close_conn_begin,
                                ssh_close_conn_end,
                                ssh_session_end,
                                job_statistics_received,
                                overall_execution_time,
                                job_execution_time,
                                file_transfer_time,
                                execution_machine
                                ):
        self.lock.acquire()
        try:
            try:
                stats = self.statistics[job_name]
            except KeyError:
                stats = JobStatistics(job_name)
                self.statistics[job_name] = stats
            
            if job_arrival != None:
                stats.job_arrival = job_arrival
                
            if job_removed_from_queue != None:
                stats.job_removed_from_queue = job_removed_from_queue
                
            if resource_scheduling_algorithm_overhead != None:
                stats.resource_scheduling_algorithm_overhead = resource_scheduling_algorithm_overhead
                
            if ssh_session_begin != None:
                stats.ssh_session_begin = ssh_session_begin
                
            if ssh_open_conn_begin != None:
                stats.ssh_open_conn_begin = ssh_open_conn_begin
                
            if ssh_open_conn_end != None:
                stats.ssh_open_conn_end = ssh_open_conn_end
                
            if ssh_execute_begin != None:
                stats.ssh_execute_begin = ssh_execute_begin
                
            if ssh_execute_end != None:
                stats.ssh_execute_end=ssh_execute_end
                
            if ssh_close_conn_begin != None:
                stats.ssh_close_conn_begin=ssh_close_conn_begin
                
            if ssh_close_conn_end != None:
                stats.ssh_close_conn_end=ssh_close_conn_end
                
            if ssh_session_end != None:
                stats.ssh_session_end=ssh_session_end
                
            if job_statistics_received != None:
                stats.job_statistics_received=job_statistics_received
                
            if overall_execution_time != None:
                stats.overall_execution_time=overall_execution_time
                
            if job_execution_time != None:
                stats.job_execution_time=job_execution_time  
                
            if file_transfer_time != None:
                stats.file_transfer_time=file_transfer_time 
                
            if execution_machine != None:
                stats.execution_machine=execution_machine                                                                                               
            
            self.statistics[job_name] = stats
        finally:
            self.lock.release()
    
    def addEmptyStats(self, job_name):
        self.lock.acquire()
        try:
            self.statistics[job_name] = JobStatistics(job_name)
        finally:
            self.lock.release()

    def dumpStatisticsToDb(self):
        conn = AISQLiteUtils.CMySQLConnection('job_stats.db3')
        cursor = conn.getCursor()
        print "Dumping statistics to DB, total number of statistics is %d " % len(self.statistics)
        try:
            for jobName,stats in self.statistics.items():
                buffer  = []
                buffer.append( (jobName, stats.job_arrival, 
                                stats.job_removed_from_queue, 
                                stats.resource_scheduling_algorithm_overhead, 
                                stats.ssh_session_begin, 
                                stats.ssh_open_conn_begin, 
                                stats.ssh_open_conn_end,
                                stats.ssh_execute_begin,
                                stats.ssh_execute_end,
                                stats.ssh_close_conn_begin,
                                stats.ssh_close_conn_end,
                                stats.ssh_session_end,
                                stats.job_statistics_received,
                                stats.overall_execution_time,
                                stats.job_execution_time,
                                stats.file_transfer_time,
                                stats.execution_machine                               
                                ) )
                cursor.executemany("""
                        insert into `Stats`(`job_name`, `job_arrival`, `job_removed_from_queue`, `resource_scheduling_algorithm_overhead`, \
                        `ssh_session_begin`, `ssh_open_conn_begin`, 'ssh_open_conn_end', 'ssh_execute_begin' , 'ssh_execute_end' , 'ssh_close_conn_begin' , 'ssh_close_conn_end' ,\
                        'ssh_session_end' , 'job_statistics_received' , 'overall_execution_time' , 'job_execution_time' , 'file_transfer_time' , 'execution_machine')
                        values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, buffer)
        finally:
            conn.commit()
            conn.close()  
        print "end of dump"

class JobStatistics:
    def __init__(self, job_name):
        self.job_name=job_name

def init_statistics_tables():
        DB_Name='job_stats.db3'
        logging.debug("Creating Database %s" % DB_Name)
        DB = AISQLiteUtils.CMySQLConnection(DB_Name)
        cursor = DB.getCursor()
        
        logging.debug("Creating table Stats")
        cursor.execute("""DROP TABLE IF EXISTS 'Stats'""")
        cursor.execute("""
            CREATE TABLE 'Stats' (
             'job_name' varchar(1000) PRIMARY KEY UNIQUE,                            
             'job_arrival' FLOAT unsigned default NULL,                              
              'job_removed_from_queue' FLOAT unsigned default NULL,                  
              'resource_scheduling_algorithm_overhead' FLOAT unsigned default NULL,  
               'ssh_session_begin' FLOAT unsigned default NULL,                      
               'ssh_open_conn_begin' FLOAT unsigned default NULL,                    
               'ssh_open_conn_end' FLOAT unsigned default NULL,                      
               'ssh_execute_begin' FLOAT unsigned default NULL,                      
               'ssh_execute_end' FLOAT unsigned default NULL,                        
                'ssh_close_conn_begin' FLOAT unsigned default NULL,                  
                'ssh_close_conn_end' FLOAT unsigned default NULL,                    
                'ssh_session_end' FLOAT unsigned default NULL,                       
              'job_statistics_received' FLOAT unsigned default NULL,                 
              'overall_execution_time' FLOAT unsigned default NULL,                  
              'job_execution_time' FLOAT unsigned default NULL,                      
              'file_transfer_time' FLOAT unsigned default NULL,                      
              'execution_machine' varchar(1000) default NULL                         
              )
            """)
        DB.commit()   
        DB.close()


#             'job_name' varchar(1000) PRIMARY KEY UNIQUE,                            # 0
#             'job_arrival' FLOAT unsigned default NULL,                              # 1
#              'job_removed_from_queue' FLOAT unsigned default NULL,                  # 2
#              'resource_scheduling_algorithm_overhead' FLOAT unsigned default NULL,  # 3
#               'ssh_session_begin' FLOAT unsigned default NULL,                      # 4
#               'ssh_open_conn_begin' FLOAT unsigned default NULL,                    # 5
#               'ssh_open_conn_end' FLOAT unsigned default NULL,                      # 6
#               'ssh_execute_begin' FLOAT unsigned default NULL,                      # 7
#               'ssh_execute_end' FLOAT unsigned default NULL,                        # 8
#                'ssh_close_conn_begin' FLOAT unsigned default NULL,                  # 9
#                'ssh_close_conn_end' FLOAT unsigned default NULL,                    # 10
#                'ssh_session_end' FLOAT unsigned default NULL,                       # 11
#              'job_statistics_received' FLOAT unsigned default NULL,                 # 12
#              'overall_execution_time' FLOAT unsigned default NULL,                  # 13
#              'job_execution_time' FLOAT unsigned default NULL,                      # 14
#              'file_transfer_time' FLOAT unsigned default NULL,                      # 15
#              'execution_machine' varchar(1000) default NULL                         # 16
