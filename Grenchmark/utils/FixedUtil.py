

"""
 When a utilization factor is given as input,
 the distribution parameters must be defined
 and subsequently verified, through the functionality
 provided by this file.
"""
__rev = "0.01";
__author__ = 'Athanasios Antoniou';
__email__ = 'A.Antoniou@student.tudelft.nl';
__file__ = 'FixedUtil.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2011/04/04 12:05:41 $"
__copyright__ = "Copyright (c) 2011 Athanasios Antoniou"
__license__ = "Python"

def calculateDistributionParameters(ConfigDic):
    """
    Given a utilization factor and a job mean cpu
    time, calculate the appropriate distribution parameters,
    such that the wanted utilization is achieved
    """
    nc = ConfigDic['Util']
    mi_cpu = ConfigDic['MeanCpuTime']
    tt = ConfigDic['TotalRuntime']
    ConfigDic['MeanArrivalTime'] = mi_cpu * tt / nc 

def verifyDistributionParameters(ConfigDic):
    """
    Verify that the selected distribution parameters
    indeed achieve the given Utilization factor.
    In any other case, the mean arrival time must
    be recalculated 
    """
    pass