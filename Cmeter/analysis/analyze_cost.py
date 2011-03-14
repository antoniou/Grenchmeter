import sys, time, datetime, os, getopt
from pysqlite2 import dbapi2 as sqlite

if "..//utils" not in sys.path:
    sys.path.append("..//utils")

import AISQLiteUtils
import GnuplotUtils
from cstats import *
import math

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

def main(argv):  
    opts, args = getopt.getopt(argv, "d:", ["db="])
    for opt, arg in opts:   
        if opt in ("-d", "--db"):
            db = arg
            print "db %s" % db
    
    if db == None:
        sys.exit(0)
    
    conn = AISQLiteUtils.CMySQLConnection(db)
    cursor = conn.getCursor()
    cursor.execute("select min(job_arrival) from Stats")
    first_job_arrival = float(cursor.fetchall()[0][0])
    cursor.execute("select max(job_statistics_received) from Stats")
    last_stats_received = float(cursor.fetchall()[0][0])
    conn.close()
    
#    result_set.sort(jobCompareSubmissionTime)
#    arrival_of_first = result_set[0][1]
#    last_stats_received = -1
#    for row in result_set:
#        stats_received = row[12]
#        if(stats_received > last_stats_received):
#            last_stats_received = stats_received
    print last_stats_received
    print first_job_arrival
    duration =  float(last_stats_received) - float(first_job_arrival)
    print math.ceil(duration/3600)
        
        
        

    # shift so that initial submission starts from 0
#===============================================================================
#    base = result_set[0]
#    new_result_set = []
#    for row in result_set:
#        new_row = list(row)
#        new_row[1] = float(row[1] - base[1])
#        new_result_set.append(new_row)
#    
#===============================================================================
    
if __name__ == "__main__":

    main(sys.argv[1:])