"""
NAME
    analyze -- Cmeter job sumbitter
    
SYNOPSIS
    %(progname)s [OPTIONS]
    
DESCRIPTION
    Post execution analusis based on statistics
    collected in databases
    
OPTIONS
    Arguments
        --help
            Print this help and exit
            
        --db <db_path>
            Path of the DB where the statistics 
            of the actual workload execution have been saved 
            
"""
    
import sys, time, datetime, os, getopt
import operator
#from pysqlite2 import dbapi2 as sqlite
import pysqlite2

if "../utils" not in sys.path:
    sys.path.append("../utils")
if "Cmeter/utils" not in sys.path:
    sys.path.append("Cmeter/utils")

import AISQLiteUtils
import GnuplotUtils
from cstats import *
 
validMetricIndex = ["ded_runtime"]

columns = { 'job_name':0     ,
            'job_arrival':1 ,
            'job_removed_from_queue':2, 
            'resource_scheduling_algorithm_overhead':3, 
            'ssh_session_begin':4, 
            'ssh_open_conn_begin':5, 
            'ssh_open_conn_end':6,
            'ssh_execute_begin':7,
            'ssh_execute_end':8,
            'ssh_close_conn_begin':9,
            'ssh_close_conn_end':10,
            'ssh_session_end':11,
            'job_statistics_received':12,
            'overall_execution_time':13,
            'job_execution_time':14,
            'file_transfer_time':15,
            'cpu_time':16,
            'ded_runtime':17,
            'execution_machine':18
          }

dedColumns = {'hash_key':0,
              'ded_runtime':1
              }

def usage(progname):
    print __doc__ % vars() 

class Analysis:
    def __init__(self,workloadDB=None):
        self.workloadDB = "job_stats.db3"
        if workloadDB!=None:
            self.workloadDB=workloadDB
        
    def analyze(self):
        # Get results from supplied databases
        workload_stats  = self.getStats(self.workloadDB, 'Stats' )
        
        # Sort statistics based on job name, so that
        # the two dbs are correctly aligned
#        workload_stats.sort(self.jobCompareName)
#        averageSlowdown,slowdown2 = self.calculateSlowDown2(workload_stats)
        
        workload_stats.sort(self.jobCompareSubmissionTime)
    
        slowdownOne,slowdownInf = self.calculateSlowdownOne(workload_stats)
        
        response = self.calculateResponseTimes(workload_stats)
        #tput = self.calculateThroughput(workload_stats)
        slowdown = self.calculateSlowDown(workload_stats)
        qwait = self.calculateQWaitTimes(workload_stats)
        
        new_result_set = self.moveStartTimeOnAxis(workload_stats)
        
        # job run times
        histo = CHistogram()
        for row in new_result_set:
            histo.addValue(row[13])
        histo.computeCDF()
        
        self.dumpToFile(new_result_set, self.getJobExecutionTimes(workload_stats), 'exec_time.dat')
        self.dumpToFile(new_result_set, response, 'response.dat')
        self.dumpToFile(new_result_set, slowdown, 'slowdown.dat')
        self.dumpToFile(new_result_set, slowdownOne, 'slowdownOne.dat')
        self.dumpToFile(new_result_set, slowdownInf, 'slowdownInf.dat')
        self.dumpSlowdownToFile(new_result_set, 'slowdown2.dat')
        self.dumpToFile(new_result_set, qwait, 'qwait.dat')
        self.dumpStatisticsToFile("stats.txt", new_result_set, response , slowdown, qwait)
#        GnuplotUtils.plotJobStats(new_result_set)
    #    GnuplotUtils.plotQueueWaitTime(new_result_set, qwait)
    #    GnuplotUtils.plotResponseTimes(new_result_set, response)`
        GnuplotUtils.plotSlowdowns(new_result_set, slowdownOne,slowdownInf)
    #    GnuplotUtils.plotFileTransferTimes(new_result_set)
    #    GnuplotUtils.plotSshTimes(new_result_set)
    #    GnuplotUtils.plotCdf(histo.CDF)
    #    GnuplotUtils.plotHistogram(histo.Values)
    #  
    
    def moveStartTimeOnAxis(self,workload_stats):
        """ modify stats so that initial submission starts from 0 """
        base = workload_stats[0]
        new_result_set = []
        for row in workload_stats:
            new_row = list(row)
            new_row[1] = float(row[1] - base[1])
            new_result_set.append(new_row)
            
        return new_result_set
    
    def getAverage(self,metric):
        if metric in validMetricIndex:
            # Get results from supplied databases
            workload_stats  = self.getStats(self.workloadDB ,'dedicatedStats')
            # Sort statistics based on job name, so that
            # the two dbs are correctly aligned
            workload_stats.sort(self.jobCompareName)
            avgMetric = 0
            for row in workload_stats:
                avgMetric += row[dedColumns[metric]]
                
            avgMetric= avgMetric / len(workload_stats)
            return avgMetric
        else:
            print "ERROR: Metric '{0}' is invalid".format(metric)
            
        return None
    
    def jobCompareSubmissionTime(self,x,y):
        xs = float(x[1])
        ys = float(y[1])
        xs = datetime.datetime.fromtimestamp(xs)
        ys= datetime.datetime.fromtimestamp(ys)
        if xs==ys:
            return 0
        elif xs < ys:
            return -1
        else:
            return 1
        
    def jobCompareName(self,x,y):
        name1 = x[0]
        name2 = y[0]
    
        if name1 == name2:
            return 0
        elif name1 < name2:
            return -1
        else:
            return 1
    
    def dump(self,result_set):
        total = 0
        finishTime = result_set[0][1] + result_set[0][7]
        for row in result_set:
            print "started %d finished %f " %  (row[1],row[1]+row[7])
            if row[1] == row[1]+row[7]:
                print "------------"
            total+=1
        print total
    
    def calculateThroughput(self, result_set):
        base = result_set[0]
        lastSubmissionTime = result_set[len(result_set)-1][1]
        ws = base[1]
        we = ws + 100
        interval  = 0
        completedJobs = 0
        cumulativeCompleted=20
        data=[]
        cumulData=[]
        wsList=[]
        while ws <= lastSubmissionTime:
            completedJobs = 0
            for row in result_set:
                if ws <= row[1] and row[1] <= we:
                    if row[12] <= we:
                        completedJobs += 1
    #        total += completedJobs
            data.append(completedJobs)
            wsList.append(we)
            ws = we
            we = ws + 100
            cumulativeCompleted+=completedJobs
            cumulData.append(cumulativeCompleted)
        GnuplotUtils.plotTPut(data,wsList)
        GnuplotUtils.plotCumul(cumulData,wsList)
        return data
    
    
    def calculateResponseTimes(self,result_set):  
        turnaroundTimes = []
        for row in result_set:
            turnaroundTimes.append(row[12]-row[1])
        return turnaroundTimes
    
    def calculateSlowdownOne(self,workloadStats):
        """
                    Workload_Makespan
            SD1 = -------------------
                    Sigma Ri
                    
            The Workload_Makespan is the time from the 
            first submission until the last results come in.
            Ri is the runtime for job i in the workload
        """
        
        makespan = self.getWLMakespan(workloadStats)
        print "WORKLOAD MAKESPAN IS {0}".format(makespan)

        runtimes = []
        for job in workloadStats:
            runtimes.append(job[columns['ded_runtime']])
            response_time = job[columns['job_statistics_received']] - job[columns['job_arrival']]
#            print "For job {0}: response_time = {1} , run_time = {2}".format(job[columns['job_name']],response_time,job[columns['ded_runtime']]) 
        
        sigmaRi = [runtimes[0]]
        maxRi   = [runtimes[0]]
        for i in range(1,len(runtimes)):
            sigmaRi.append( runtimes[i] + sigmaRi[i-1])
            maxRi.append(max(runtimes[0:i+1]))
            
#        sigmaResponse = [workloadStats[0][12]-workloadStats[0][1] ]
#        for i in range(1,len(workloadStats)):
#            sigmaResponse.append( workloadStats[i][12]-workloadStats[i][1] + sigmaResponse[i-1])
            
#        print "Sigma(Ri)= ",sigmaRi
#        print "SigmaResponse= ",sigmaResponse
#        print "max(Ri)= ",maxRi
        
#        jobSlowdownOne = [m/max(s,1) for m,s in zip(makespan,sigmaRi)]
#        jobSlowdownInf = [m/max(r,1) for m,r in zip(makespan,maxRi)]    
        jobSlowdownOne = [m/s for m,s in zip(makespan,sigmaRi)]
        jobSlowdownInf = [m/r for m,r in zip(makespan,maxRi)]    
        print "SlowdownOne= ",jobSlowdownOne
        print "SlowdownInf= ",jobSlowdownInf
#        jobSlowdownRe = [max(m/s,1) for m,s in zip(sigmaResponse,sigmaRi)]
#        print "SlowdownResponse= ",jobSlowdownRe
        
        return jobSlowdownOne,jobSlowdownInf 
        
    def getWLMakespan(self,workloadStats):
        
        makespan = []
        workloadSubmitTime = workloadStats[0][1]
        workloadEndTime = [workloadStats[0][12] for i in range(len(workloadStats))]
        
#        for i in range(len(workloadStats)):
#            print "Time from start {0}, submittion time {1}, duration {2}".format(workloadStats[i][12]-workloadStats[0][1],workloadStats[i][1]-workloadStats[0][1],workloadStats[i][12]-workloadStats[i][1])
        for i in range(len(workloadStats)):
            for j in range(i+1):
                if workloadStats[j][12] > workloadEndTime[i]:
                    workloadEndTime[i] = workloadStats[j][12]
            makespan.append(workloadEndTime[i] - workloadSubmitTime) 

        return makespan   
              
        
    def calculateSlowDown2(self,workloadStats): 
        """                 (Sigma Ri)/n
        Average Slowdown = ---------------
                                MS
        where Ri = Runtime for Jobi in Workload
              n  = number of jobs in cloud
              MS = MakeSpan of Workload
        """
        slowdown = []
        numRows = len(workloadStats)
        dRunTime, wRunTime = 0,0
        
        for row in range(numRows):
            wRow = workloadStats[row]
            dRow = dedicatedStats[row]
    
            jobSlowdown = max(wRow[14]/dRow[14],1)
            slowdown.append(jobSlowdown)
            
            # Append slowdown in the workloadStats structure,
            # since a later sort based on job Submission time
            # will shuffle the order
            listwRow = list(wRow)
            listwRow.append(jobSlowdown)
            workloadStats[row]=tuple(listwRow)
    
            dRunTime+= dRow[14] 
            wRunTime+= wRow[14]
        
        totalSlowdown = wRunTime / dRunTime
        #slowdownPerJob = totalSlowdown / num_rows
        averageSlowdown = 0
        for sl in slowdown:
            averageSlowdown += sl
        averageSlowdown/= numRows
        
        print "Total= ", totalSlowdown," Average= ", averageSlowdown         return (averageSlowdown,slowdown)
    
    def calculateSlowDown(self,workload_stats): 
        slowdown = []
        for row in workload_stats:
            # 1 is supposed to represent the mean execution time of the workload applications
            # Slowdown = Sigma ( (t_job_stats_received - t_job_arrival)/ t_r)
            slowdown.append(max((row[12]-row[1])/max(row[14],1),1))
        return slowdown
    
    def calculateQWaitTimes(self,result_set): 
        qwait = []
        for row in result_set:
            qwait.append(row[7]-row[1])
        return qwait 
       
    def getJobExecutionTimes(self,result_set): 
        execTimes = []
        for row in result_set:
            execTimes.append(row[14])
        return execTimes    
    
    def getStats(self,dbName,table):
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
    
    def dumpToFile(self,new_result_set, list, fileName):
        fp = open(fileName,'w')
        for i in range(len(new_result_set)):
            fp.write(str(new_result_set[i][1])) # submission time
            fp.write('\t')
            fp.write(str(list[i]))
            fp.write('\n')
        fp.close()
        
    def dumpSlowdownToFile(self,new_result_set, fileName):
        fp = open(fileName,'w')
        for i in range(len(new_result_set)):
            fp.write(str(new_result_set[i][1])) # submission time
            fp.write('\t')
            fp.write(str(new_result_set[i][18]))# slowdown
            fp.write('\n')
        fp.close()

    def dumpStatisticsToFile(self,file,new_result_set,responseTimes , slowdownTimes, qwait):
        fp = open(file,'a')
        
        execTime = CStats()
        fp.write("EXEC TIME\n")
        for row in new_result_set:
            execTime.addValue(row[14])
        execTime.doComputeStats()
        execTime.dump(fp)
        fp.write("\n\n")
            
        fileTx = CStats()
        fp.write("FILE TRANSFER\n")
        for row in new_result_set:
            fileTx.addValue(row[15]) # file tx
        fileTx.doComputeStats()
        fileTx.dump(fp)
        fp.write("\n\n")
        
        response = CStats()
        fp.write("RESPONSE TIME\n")
        for resp in responseTimes:
            response.addValue(resp) 
        response.doComputeStats()
        response.dump(fp)
        fp.write("\n\n")    
        
#        qWaitTimes = CStats()
#        fp.write("QWAIT TIME\n")
#        for q in qwait:
#            qWaitTimes.addValue(q) 
#        qWaitTimes.doComputeStats()
#        qWaitTimes.dump(fp)
#        fp.write("\n\n")      
        
        
    #    throughput = CStats()
    #    fp.write("THROUGHPUT\n")
    #    for t in tput:
    #        throughput.addValue(t) 
    #    throughput.doComputeStats()
    #    throughput.dump(fp)
    #    fp.write("\n\n")        
        
        slowdown = CStats()
        fp.write("SLOWDOWN\n")
        for sd in slowdownTimes:
            slowdown.addValue(sd) 
        slowdown.doComputeStats()
        slowdown.dump(fp)
        fp.write("\n\n")
            
        fp.write("SSH\n")
        ssh = CStats()
        for row in new_result_set:
            ssh.addValue(row[11]-row[4]) 
        ssh.doComputeStats()
        ssh.dump(fp)
        fp.write("\n\n")
        fp.close()

def main(argv):
      
    #Default DB files
    workload_db  = "job_stats.db3"
    opts, args = getopt.getopt(argv, "d:w:", ["db=","help"])
    for opt, arg in opts:
        if opt in ("--help"):
            usage(os.path.basename(sys.argv[0]))
            sys.exit()  
        elif opt in ("--db"):
            workload_db = arg
            print "DB %s" % workload_db
    
    if not os.path.exists(workload_db):
        print "Workload db %s does not exist." % workload_db
        sys.exit(0)
    
    analysis = Analysis(workload_db)
    
    analysis.analyze()
    
if __name__ == "__main__":

    main(sys.argv[1:])