import sys, time, datetime, os, getopt
from pysqlite2 import dbapi2 as sqlite

if "..//utils" not in sys.path:
    sys.path.append("..//utils")

import AISQLiteUtils

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
    cursor.execute("select distinct execution_machine from Stats")
    machines = cursor.fetchall()
    #cursor.execute("select * from Stats")
    #allJobs = cursor.fetchall()
    dict = {}
    for machine in machines:
        cursor.execute("select * from  Stats where execution_machine='" + machine[0] + "'")
        dict[machine[0]] = cursor.fetchall()
    conn.close()
    total = 0 
    for (key,val) in dict.items():
        print key + " has " + str(len(val)) + " jobs"
        total+=len(val)
        val.sort(jobCompareSubmissionTime)
    
    predictionDict = {}
    for (key,val) in dict.items():
        print "processing %s " % key
#        for job in val:
#            print datetime.datetime.fromtimestamp(float(job[1]))
#        print "------------------------------------------------------------------"
        predictedValues = []
        numOfJobs = len(val)
        for i in range(numOfJobs):
            if i == 0 or i == 1:
                predictedValues.append(val[i][12]-val[i][1])
            else:
                lastResp = val[i-1][12]-val[i-1][1]
                last2Resp = val[i-2][12]-val[i-2][1]
                predictedValues.append(float(lastResp+last2Resp)/2)
        predictionDict[key] = predictedValues
    totalAcc = 0
    for machine,jobs in dict.items():
        predictedValues = predictionDict[machine]
        averageAccuracy = 0
        for i in range(len(jobs)):
            respTime = jobs[i][12] - jobs[i][1]
            if predictedValues[i] >= respTime:
                averageAccuracy+=float(respTime/predictedValues[i])
            else:
                averageAccuracy+=float(predictedValues[i]/respTime)
        totalAcc += averageAccuracy/len(jobs)
    print totalAcc/5
#    for machine,jobs in dict.items():
#        predictedValues = predictionDict[machine]
#        realValues= [] 
#        for job in jobs:
#            realValues.append(job[12] - job[1])
#        dumpToFile(predictedValues, machine + '_pred.dat')
#        dumpToFile(realValues, machine + '_real.dat')
#    print "done"
    
    
def dumpToFile(list, fileName):
    fp = open(fileName,'w')
    for i in range(len(list)):
        fp.write(str(i)) # submission time
        fp.write('\t')
        fp.write(str(list[i]))
        fp.write('\n')
    fp.close()
    
    
    
    
    
if __name__ == "__main__":

    main(sys.argv[1:])    