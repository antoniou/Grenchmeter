from numpy import *
import sys
import os
import Gnuplot, Gnuplot.funcutils
from datetime import datetime

def plotResponseTimes(result_set, response):
    plotData=[]
    for i in range(len(result_set)):
        row = result_set[i]
        data=[]
        data.append(row[1]) # submission time
        data.append(response[i])
        plotData.append(data)
    plotJobExecTimes(plotData, 'Arrival Time' , 'Response Time (s)' , 'Response Time'  , 'resp_time.eps', "25", "5", True , "lines lw 1 lc  rgb \"black\"")



def plotQueueWaitTime(result_set, qwait):
    plotData=[]
    for i in range(len(result_set)):
        row = result_set[i]
        data=[]
        data.append(row[1]) # submission time
        data.append(qwait[i])
        plotData.append(data)
    plotJobExecTimes(plotData, 'Arrival Time' , 'Wait Time (s)' , 'Queue Wait Time'  , 'qwait.eps', "25", "20", False, 'lines lw 1 lc  rgb \"black\"')   
    
    
def plotSlowdowns(result_set, slowdown):
    plotData=[]
    for i in range(len(result_set)):
        row = result_set[i]
        data=[]
        data.append(row[1]) # submission time
        data.append(slowdown[i]) 
        plotData.append(data)
    plotJobExecTimes(plotData, 'Arrival Time' , 'Slowdown' , 'Bounded Slowdown'  , 'slowdown.eps', "25", "5", True, 'lines lw 1 lc  rgb \"black\"')    
    
def plotJobStats(result_set):
    plotData=[]
    for row in result_set:
        data=[]
        data.append(row[1]) # submission time
        data.append(row[13]) # overall exec time
        plotData.append(data)
    plotJobExecTimes(plotData, 'Arrival Time' , 'Execution Time (s)' , 'Execution Time'  , 'exec_time.eps', "50", "25", False, "lines lw 1 lc  rgb \"black\"")

def plotFileTransferTimes(result_set):
    plotData=[]
    for row in result_set:
        data=[]
        data.append(row[1]) # submission time
        data.append(row[15]) # file tx
        plotData.append(data)
    plotJobExecTimes(plotData, 'Arrival Time' , 'File Transfer Time (s)' , 'File Transfer Time'  , 'file_tx.eps', "25", "1", False, 'lines lw 1 lc  rgb \"black\"') 
       
def plotSshTimes(result_set):
    plotData=[]
    for row in result_set:
        data=[]
        data.append(row[1]) # submission time
        data.append(row[11]-row[4]) # ssh
        plotData.append(data)
    plotJobExecTimes(plotData, 'Arrival Time' , 'SSH Time (s)' , 'SSH Session Time'  , 'ssh.eps', "25", "50", False, 'lines lw 1 lc  rgb \"black\"')   


def plotTPut(dataList,wsList):
    plotData=[]
    for i in range(len(dataList)):
        data=[]
        data.append(wsList[i])
        data.append(dataList[i])
        plotData.append(data)   
    g = Gnuplot.Gnuplot(debug=1)
    g("set grid")
    g("set xtics 10")
    g("set xtics nomirror out rotate by 90,graph -0.15 scale 2")
    g("set xrange [0:*]")
    g.xlabel('Time')
    g.ylabel('Throughput')
    g.title('Throughput (Jobs/s)')
    plot2 = Gnuplot.PlotItems.Data(plotData,using="1:2", with="lines lw 1 lc rgb \"black\"")  # No title
    g.plot(plot2)
    g.hardcopy('tput.png', terminal='png')        
    raw_input('Please press return to continue...\n')
    
def plotCumul(dataList,wsList):
    plotData=[]
    for i in range(len(dataList)):
        data=[]
        data.append(wsList[i])
        data.append(dataList[i])
        plotData.append(data)   
    g = Gnuplot.Gnuplot(debug=1)
    g("set grid")
    g("set xtics 10")
    g("set xrange [0:*]")
    g.xlabel('Time')
    g("set xtics nomirror out rotate by 90,graph -0.15 scale 2")
    g.ylabel('Jobs')
    g.title('Completed Jobs')
    plot2 = Gnuplot.PlotItems.Data(plotData,using="1:2", with="lines lw 1 lc rgb \"black\"")  # No title
    g.plot(plot2)
    g.hardcopy('jobs.png', terminal='png')        
    raw_input('Please press return to continue...\n') 
    
    
def plotJobExecTimes(data, xlabel, ylabel, title, fileName, xtics, ytics, isLogScale, typeOfPlot):
    g = Gnuplot.Gnuplot(debug=1)
    g("set ytics " + ytics + " font \"Arial,20\"")
    g("set grid")
    xlabel = "\""+xlabel+ "\"" + " font \"Arial,20\""
    g("set xlabel " + xlabel)
    ylabel = "\"" + ylabel + "\"" + " font \"Arial,20\""
    g("set ylabel " + ylabel)
    if isLogScale:
        g("set logscale y")
    g("set xtics 20 border in scale 3,2.5 nomirror out rotate by 90  offset character 0, 0, 0 font \"Arial,20\"")
    g("set title " + "\"" + title + "\"" + " font \"Arial,20\"")
    plot2 = Gnuplot.PlotItems.Data(data,using="1:2", with=typeOfPlot)  # 
    g.plot(plot2)
    g.hardcopy(fileName, enhanced=1, color=0)
    #g.hardcopy(fileName, terminal='jpg')
    raw_input('Please press return to continue...\n')
    

def plotCdf(cdf):
    plotData=[]
    for x,y in cdf.items():
        data=[]
        data.append(x)
        data.append(y)
        plotData.append(data)
    rawPlot(plotData,'Execution Time','CDF' , 'CDF of Job Execution Time', 'cdf.png')
    
    
def plotHistogram(valueDict):
    plotData=[]
    for x,y in valueDict.items():
        data=[]
        data.append(x)
        data.append(y)
        plotData.append(data)
    plotHisto(plotData, 'Execution Time','Count' , 'Histogram of Job Execution Time', 'histo.png')

def plotHisto(data,xlabel, ylabel, title, fileName):
    g = Gnuplot.Gnuplot(debug=1)
    g("set style histogram clustered gap 1 title  offset character 0, 0, 0")
    g("set xtics nomirror out rotate by 90,graph -0.15 scale 2")
    g("set style fill  solid 1.00 noborder")
    g("set boxwidth 0.8 absolute")
    g("set style data histograms")
    g("set datafile missing '-'")
    g("set grid")
    g("set yrange [0:1000]")
    g.xlabel(xlabel)
    #g("set xtics nomirror out rotate by 90 offset 0,graph -0.05 scale 2")
    g.ylabel(ylabel)
    g.title(title)
    plot2 = Gnuplot.PlotItems.Data(data,using="2:xtic(1)")  # No title
    g.plot(plot2)
    g.hardcopy(fileName, terminal='png')
    raw_input('Please press return to continue...\n')  
    
        
def rawPlot(data,xlabel, ylabel, title, fileName):
    g = Gnuplot.Gnuplot(debug=1)
    g("set yrange [0:1]")
    g("set grid")
    g("set xtics nomirror out rotate by 90,graph -0.15 scale 2")
    g.xlabel(xlabel)
    g.ylabel(ylabel)
    g.title(title)
    plot2 = Gnuplot.PlotItems.Data(data,using="1:2", with="lines lw 1 lc rgb \"black\"")  # No title
    g.plot(plot2)
    g.hardcopy(fileName, terminal='png')        
    raw_input('Please press return to continue...\n')    
    
        
def compareFunction(x,y):
    a=int(x[0])
    b=int(y[0])
    if a==b:
        return 0
    elif a < b:
        return -1
    else:
        return 1
