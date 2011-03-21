import sys, time, datetime, os, getopt
from pysqlite2 import dbapi2 as sqlite

if "../utils" not in sys.path:
    sys.path.append("../utils")

import AISQLiteUtils
import GnuplotUtils
from cstats import *
 
def jobCompareSubmissionTime(x,y):
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

def dump(result_set):
    total = 0
    finishTime = result_set[0][1] + result_set[0][7]
    for row in result_set:
        print "started %d finished %f " %  (row[1],row[1]+row[7])
        if row[1] == row[1]+row[7]:
            print "------------"
        total+=1
    print total

def calculateThroughput(result_set):
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


def calculatResponseTimes(result_set):  
    turnaroundTimes = []
    for row in result_set:
        turnaroundTimes.append(row[12]-row[1])
    return turnaroundTimes

def calculateSlowDown(result_set): 
    slowdown = []
    for row in result_set:
        # 1 is supposed to represent the mean execution time of the workload applications
        slowdown.append(max((row[12]-row[1])/max(row[14],1),1))
    return slowdown

def calculateQWaitTimes(result_set): 
    qwait = []
    for row in result_set:
        qwait.append(row[7]-row[1])
    return qwait 

   
def getJobExecutionTimes(result_set): 
    execTimes = []
    for row in result_set:
        execTimes.append(row[14])
    return execTimes    

def main(argv):  
    opts, args = getopt.getopt(argv, "d:", ["db="])
    for opt, arg in opts:   
        if opt in ("-d", "--db"):
            db = arg
            print "db %s" % db
    
    if db == None:
        print "Please supply an SQLite DB file."
        sys.exit(0)
    
    # Get results from supplied database
    conn = AISQLiteUtils.CMySQLConnection(db)
    cursor = conn.getCursor()
    cursor.execute("select * from Stats")
    result_set = cursor.fetchall()
    conn.close()
    
    result_set.sort(jobCompareSubmissionTime)
    response = calculatResponseTimes(result_set)
    slowdown = calculateSlowDown(result_set)
    #tput = calculateThroughput(result_set)
    qwait = calculateQWaitTimes(result_set)
    
    
    # shift so that initial submission starts from 0
    base = result_set[0]
    new_result_set = []
    for row in result_set:
        new_row = list(row)
        new_row[1] = float(row[1] - base[1])
        new_result_set.append(new_row)
    
    # job run times
    histo = CHistogram()
    for row in new_result_set:
        histo.addValue(row[13])
    histo.computeCDF()
    
    submission_of_first_job = result_set[0][1]
    # find last finished job
    end_of_latest = 0
    for row in result_set:
        if row[12] > end_of_latest:
            end_of_latest = row[12]
    
    print end_of_latest
    print submission_of_first_job
    print end_of_latest - submission_of_first_job
    
    dumpToFile(new_result_set, getJobExecutionTimes(result_set), 'exec_time.dat')
    dumpToFile(new_result_set, response, 'response.dat')
    dumpToFile(new_result_set, slowdown, 'slowdown.dat')
    dumpToFile(new_result_set, qwait, 'qwait.dat')
    dumpStatisticsToFile("stats.txt", new_result_set, response , slowdown, qwait)
#    GnuplotUtils.plotJobStats(new_result_set)
#    GnuplotUtils.plotQueueWaitTime(new_result_set, qwait)
#    GnuplotUtils.plotResponseTimes(new_result_set, response)`
    GnuplotUtils.plotSlowdowns(new_result_set, slowdown)
#    GnuplotUtils.plotFileTransferTimes(new_result_set)
#    GnuplotUtils.plotSshTimes(new_result_set)
#    GnuplotUtils.plotCdf(histo.CDF)
#    GnuplotUtils.plotHistogram(histo.Values)
#  


def dumpToFile(new_result_set, list, fileName):
    fp = open(fileName,'w')
    for i in range(len(new_result_set)):
        fp.write(str(new_result_set[i][1])) # submission time
        fp.write('\t')
        fp.write(str(list[i]))
        fp.write('\n')
    fp.close()
    
def dumpStatisticsToFile(file,new_result_set,responseTimes , slowdownTimes, qwait):
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
    
    qWaitTimes = CStats()
    fp.write("QWAIT TIME\n")
    for q in qwait:
        qWaitTimes.addValue(q) 
    qWaitTimes.doComputeStats()
    qWaitTimes.dump(fp)
    fp.write("\n\n")      
    
    
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
    
    
    
if __name__ == "__main__":

    main(sys.argv[1:])