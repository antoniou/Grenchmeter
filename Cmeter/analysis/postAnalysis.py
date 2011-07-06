"""
NAME
    postAnalysis -- 
    
SYNOPSIS
    %(progname)s [OPTIONS]
    
DESCRIPTION
    Post execution analysis based on statistics
    collected in databases
    
OPTIONS
    Arguments
        --help
            Print this help and exit
"""

import sys
import Gnuplot
import Gnuplot.funcutils

if "../utils" not in sys.path:
    sys.path.append("../utils")
if "Cmeter/utils" not in sys.path:
    sys.path.append("Cmeter/utils")

class PlotConfiguration:
    def __init__(self):
        self.plotCommand = ""
        self.xlabel = ""
        self.ylabel = ""
        self.title = ""
        self.isLogScaleX = False
        self.isLogScaleY = False
        self.keyTitle = ""
        self.keyBox = True 
        self.savePlotToFile = "slowdowns.eps"

def gnuplotData(plotConfiguration):
    g = Gnuplot.Gnuplot(debug=1)
#    g("set ytics " + ytics + " font \"Arial,20\"")
    g("set grid")
    xlabel = "\""+plotConfiguration.xlabel+ "\"" + " font \"Arial,20\""
    g("set xlabel " + xlabel)
    ylabel = "\"" + plotConfiguration.ylabel + "\"" + " font \"Arial,20\""
    g("set ylabel " + ylabel)
    if plotConfiguration.isLogScaleY:
        g("set logscale y")
        
    g("set key title \'" + plotConfiguration.keyTitle + "\'")
    if plotConfiguration.keyBox:
        g("set key box")
    g("set title " + "\"" + plotConfiguration.title + "\"" + " font \"Arial,20\"")
    g.plot(plotConfiguration.plotCommand)
    g.hardcopy(plotConfiguration.savePlotToFile, enhanced=1, color=1)
    raw_input('Please press return to continue...\n')
    
def getPlotConfiguration(fileNames):
    config = PlotConfiguration()
    config.plotCommand = createPlotCommand(fileNames)
    config.isLogScaleY = False
    config.xlabel = "Arrival Time (seconds)"
    config.ylabel = " Slowdown"
    config.title = "Slowdown"
    config.keyTitle = "VM instances"
    config.keyBox = False
    return config
    
def createPlotCommand(fileNames):
    plotCommand = ""
#    datasetTitles = ["{0}%".format(u) for u in range(50,111,10)]
    datasetTitles = ["{0}".format(u) for u in [1,2,4,8,16]]
    for i in range(len(fileNames)):
        plotCommand += "\'{0}\' using 1:2 title \'{1}\' with lines,".format(fileNames[i],datasetTitles[i])
    plotCommand = plotCommand.rstrip(',')
    
    return plotCommand
    
def constructDataFileNames(slowdownFilename):
    filenames = []
    utilizationRates = range(50,111,10)
    
    for util in utilizationRates:
        directoryName = "3000sser_{0}util_1small_sequential".format(util)
        currentFilename = "{0}/{1}".format(directoryName,slowdownFilename)
        filenames.append(currentFilename)
        
    return filenames
    
def plotSlowdownOne():     
    fileNames = constructDataFileNames("slowdownOne.dat")
    plotConfiguration = getPlotConfiguration(fileNames)
    plotConfiguration.savePlotToFile = "slowdownOne.eps"
    plotConfiguration.title = 'Slowdown One'
    gnuplotData(plotConfiguration)
    
def plotSlowdownInf():     
    fileNames = constructDataFileNames("slowdownInf.dat")
    plotConfiguration = getPlotConfiguration(fileNames)
    plotConfiguration.savePlotToFile = "slowdownInf.eps"
    plotConfiguration.title = 'Slowdown Inf'
    gnuplotData(plotConfiguration)
    
def constructFileNamesVariableVM():
    filenames = []
    directoryName = "variableVMs_70util_sequential"
#    directoryName = "variableVMs_Poisson1000"
#    vmNumber=[1,2,4,8,16]
    vmNumber=[1,2,4,8,16]
    for vm in vmNumber:
        currentFilename = "{0}/slowdownInf_{1}vm.dat".format(directoryName,vm)
        filenames.append(currentFilename)
        
    return filenames
        
def plotSlowdownVariableVMNumber():
    fileNames = constructFileNamesVariableVM()
    plotConfiguration = getPlotConfiguration(fileNames)
    plotConfiguration.savePlotToFile = "slowdownInf_variableVMs_util70.eps"
    plotConfiguration.title = 'Slowdown Inf'
    gnuplotData(plotConfiguration)
    
def plotSlowdowns():
#   plotSlowdownOne()
#   plotSlowdownInf()
    plotSlowdownVariableVMNumber()
    
def main(argv):
    plotSlowdowns()

if __name__ == "__main__":
    main(sys.argv[1:])