import sys, time, datetime, os
from sqlite3 import dbapi2 as sqlite

import threading 
import logging
import AISQLiteUtils

class DatabaseStatistics:
    def __init__(self):
        self.statistics = {}
        self.knownDedicatedStats = {}
        self.lock = threading.Lock()
        
    def getStatistics(self, job_name):
            self.lock.acquire()
            try:      
                return self.statistics[job_name]
            finally:
                self.lock.release()       
                                               
    def updateStatistics(self, job_name, job_arrival = None, 
                                job_removed_from_queue = None, 
                                resource_scheduling_algorithm_overhead = None, 
                                ssh_session_begin = None, 
                                ssh_open_conn_begin = None, 
                                ssh_open_conn_end = None,
                                ssh_execute_begin = None,
                                ssh_execute_end = None,
                                ssh_close_conn_begin = None,
                                ssh_close_conn_end = None,
                                ssh_session_end = None,
                                job_statistics_received = None,
                                overall_execution_time = None,
                                job_execution_time = None,
                                file_transfer_time = None,
                                cpu_time = None,
                                ded_runtime = None,
                                execution_machine = None
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
                
            if cpu_time != None:
                stats.cpu_time = cpu_time
                
            if ded_runtime != None:
                stats.ded_runtime = ded_runtime
                
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
            
    def clearStats(self):
        self.lock.acquire()
        try:
            self.statistics = {} 
        finally:
            self.lock.release()

    def dumpDedStatisticsToDb(self,databaseName=None):
        if databaseName != None:
            dbName = databaseName
        else:
            dbName = 'job_stats.db3'
            
        conn = AISQLiteUtils.CMySQLConnection(dbName)
        cursor = conn.getCursor()
        print "Total number of dedicated statistics is ", len(self.knownDedicatedStats)
        print "Dumping ded statistics to DB \'", dbName,"\'" ,
        try:
            for key,dedStat in self.knownDedicatedStats.items():
                try:
                    cursor.executemany("insert into 'DedicatedStats'('hash_key', 'ded_runtime' ) values (?,?) ", [(unicode(key),dedStat.ded_runtime)])
                except sqlite.IntegrityError:
                    # Statistics have been previously submitted under the same job name
                    continue
        finally:
            conn.commit()
            conn.close()
            
        print "DONE"
        return dbName
    
    def dumpStatisticsToDb(self,databaseName=None):
        if databaseName != None:
            dbName = databaseName
        else:
            dbName = 'job_stats.db3'
            
        conn = AISQLiteUtils.CMySQLConnection(dbName)
        cursor = conn.getCursor()
        print "Total number of statistics is ", len(self.statistics)
        print "Dumping statistics to DB \'", dbName,"\'" ,
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
                                stats.cpu_time,
                                stats.ded_runtime,
                                stats.execution_machine                               
                                ) )
                cursor.executemany("""
                        insert into `Stats`(`job_name`, `job_arrival`, `job_removed_from_queue`, `resource_scheduling_algorithm_overhead`, \
                        `ssh_session_begin`, `ssh_open_conn_begin`, 'ssh_open_conn_end', 'ssh_execute_begin' , 'ssh_execute_end' , 'ssh_close_conn_begin' , 'ssh_close_conn_end' ,\
                        'ssh_session_end' , 'job_statistics_received' , 'overall_execution_time' , 'job_execution_time' , 'file_transfer_time' ,'cpu_time','ded_runtime', 'execution_machine')
                        values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, buffer)
        except sqlite.IntegrityError:
            # Statistics have been previously submitted under the
            # same job name
            pass
        finally:
            conn.commit()
            conn.close()  
        print "DONE"
        return dbName

    def updateDedStatistics(self, hashKey, ded_runtime):
        self.knownDedicatedStats[hashKey] = DedicatedStatistics(ded_runtime)
        
    
    def getKnownStats(self,hashKey):
        try:
            stats = self.knownDedicatedStats[hashKey]
            return { 'jobExec':stats.ded_runtime }
        except:
            return None
        
    def init_statistics_tables(self):
        """ Create databases that hold statistics."""
        self.initDB('job_stats.db3')
        
    def initDB(self,DB_Name):
        if os.path.exists(DB_Name):
            logging.debug("Database %s already exists." % DB_Name)
            self.populateDedStats(DB_Name)
            
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
              'cpu_time' FLOAT unsigned default NULL,                      
              'ded_runtime' FLOAT unsigned default NULL,                      
              'execution_machine' varchar(1000) default NULL                         
              )
            """)
        
        logging.debug("Creating table DedicatedStats")
#        cursor.execute("""DROP TABLE IF EXISTS 'DedicatedStats'""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS'DedicatedStats' (
             'hash_key' varchar(1000) PRIMARY KEY UNIQUE,                            
              'ded_runtime' FLOAT unsigned default NULL                      
              )
            """)
        DB.commit()   
        DB.close()
        
    def populateDedStats(self,dbName):
        print "Populating from DB {0}".format(dbName)
        dedStats = self.getStatsfromDB(dbName, 'DedicatedStats')
        for row in dedStats:
            self.updateDedStatistics(row[0],row[1])
            
        print "\t Found ", len(self.knownDedicatedStats)," dedicated statistics."
            
    def getStatsfromDB(self,dbName,table):
        """Connect to db dbName and 
           retrieve statistics from table.
           Return statistics
        """
    
        conn = AISQLiteUtils.CMySQLConnection(dbName)
        cursor = conn.getCursor()
        cursor.execute("select * from {0}".format(table))
        result_set = cursor.fetchall()
        conn.close()
        
        return result_set
    
class DedicatedStatistics:
    def __init__(self,runtime):
        self.ded_runtime = runtime
        
class JobStatistics:
    def __init__(self, job_name):
        self.job_name=job_name
        self.job_arrival = None
        self.job_removed_from_queue = None
        self.resource_scheduling_algorithm_overhead = None 
        self.ssh_session_begin = None
        self.ssh_open_conn_begin = None
        self.ssh_open_conn_end = None
        self.ssh_execute_begin = None
        self.ssh_execute_end = None
        self.ssh_close_conn_begin = None
        self.ssh_close_conn_end = None
        self.ssh_session_end = None
        self.job_statistics_received = None
        self.overall_execution_time = None
        self.job_execution_time = None
        self.file_transfer_time = None
        self.cpu_time = None
        self.ded_runtime = None
        self.execution_machine = None  



    
