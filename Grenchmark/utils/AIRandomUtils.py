#! /usr/bin/env python

__rev = "0.31";
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'AIRandomUtils.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:24:41 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python"  

#---------------------------------------------------
# Log:
# 28/08/2005 A.I. 0.3
#    Added getRandomWeightedListElement
# 12/08/2005 A.I. 0.21
#    Added constant distributions: Constant
# 12/08/2005 A.I. 0.2 
#    Added random distributions: Uniform, Normal, Exponential, 
#    Poisson, HyperExp2, HyperPoisson2, Weibull, LogNormal, Gamma;
#    Gamma is NOT available yet -- untested, build according to Jain
# 11/08/2005 A.I. 0.1 Started this app
#---------------------------------------------------

import random
import math

def getRandomInt( min, max ):
    """ 
    returns a random integer X, min <= X <= max 
    
    NOTE: X can also be min or max
    """
    return random.randint(min, max)

def getRandomListElement( ListParam ):
    """ returns a random element from the list """
    return ListParam[ getRandomInt(0, len(ListParam) - 1) ]
    
def getRandomWeightedListElement( WeightedList, ValuesKey = 'Values', TotalWeightKey = 'TotalWeight' ):
    """ returns a random element from a weighted list: the chance of getting an element is proportional to element's weight and total list weight """
    ConstFactor = 1
    if WeightedList[TotalWeightKey] < 1000:
        ConstFactor = 1000
    MaxVal = int(WeightedList[TotalWeightKey]*ConstFactor)
    rnd = getRandomInt(0, MaxVal)
    index = 0
    while 1:
        (Value, fWeight) = WeightedList[ValuesKey][index]
        if rnd <= fWeight * ConstFactor:
            break
        rnd = rnd - fWeight * ConstFactor
        index = index + 1
    return Value
    
def initRandom():
    random.seed()
    
class AIRandomError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class AIRandom(random.Random):
    
    #--- init
    def __init__(self, x=None):
        """Initialize an instance.

        Optional argument x controls seeding, as for Random.seed().
        """
        random.Random.__init__(self, x)
        #-- add another random variable, to be used if needed
        self.AuxRandom = random.Random(x)
        #-- available random functions
        self.RandomFuncs = { 
            'C':self.nextConstant, 
            'U':self.nextUniform, 
            'N':self.nextNormal, 
            'Poisson':self.nextPoisson,
            'Exp':self.nextExponential,
            'HPoisson2':self.nextHyperPoisson2,
            'HExp2':self.nextHyperExponential2,
            'W':self.nextWeibull,
            'LogNorm':self.nextLogNormal,
            'Zero':self.nextZero
            }

    
    #--- general tools
    def getRandomInt( self, min, max ):
        """ 
        returns a random integer X, min <= X <= max 
        
        NOTE: X can also be min or max
        """
        return self.randint(min, max)

    def getRandomListElement( self, ListParam ):
        """ returns a random element from the list """
        return ListParam[ self.getRandomInt(0, len(ListParam) - 1) ]
        
    def getRandomWeightedListElement( self, WeightedList, ValuesKey = 'Values', TotalWeightKey = 'TotalWeight' ):
        """ returns a random element from a weighted list: the chance of getting an element is proportional to element's weight and total list weight """
        """ returns a random element from a weighted list: the chance of getting an element is proportional to element's weight and total list weight """
        ConstFactor = 1
        if WeightedList[TotalWeightKey] < 1000:
            ConstFactor = 1000
        MaxVal = int(WeightedList[TotalWeightKey]*ConstFactor)
        rnd = self.getRandomInt(0, MaxVal)
        index = 0
        while 1:
            (Value, fWeight) = WeightedList[ValuesKey][index]
            if rnd <= fWeight * ConstFactor:
                break
            rnd = rnd - fWeight * ConstFactor
            index = index + 1
        return Value
    
    def isDistributionName( self, Name ):
        """ returns > 0 if the distribution name is defined, <= 0 otherwise """
        if Name not in self.RandomFuncs.keys():
            return -1
        else: 
            return 1
    
    def randomVariable( self, Name, ParamsList ):
        """ returns the random variable from the distribution given as Name, 
        with parameters given in the ParamsList list """
            
        if Name not in self.RandomFuncs.keys():
            raise AIRandomError("Name " + "'"+Name+"'" + " not found in the list of available distribution generators!") 
            
        # TODO: check at least that the ParamsList has enough parameters
            
        return self.RandomFuncs[Name](ParamsList)
    
    #--- various distributions
    def nextZero( self, ParamList ):
        """ always return 0 """
        return 0
        
    def nextConstant( self, ParamList ):
        """ returns the value given in the parameter list """
        a = float(ParamList[0])
        return a
        
    def nextUniform( self, ParamList ):
        """ returns a random variable with Uniform distribution in the interval [a,b] """
        a = float(ParamList[0])
        b = float(ParamList[1])
        return self.uniform( a, b )
        
    def nextNormal( self, ParamList ):
        """ 
        returns a random variable with Normal (Gaussian) distribution 
        of mean mu and standard deviation sigma 
        """
        mu = float(ParamList[0])
        sigma = float(ParamList[1])
        return self.normalvariate(mu, sigma)
        
    def nextExponential( self, ParamList ):
        """
        returns a random variable with Exponential distribution 
        with scale parameter a. 
        
        Note that a is 1 per desired mean. Use Poisson to pass the 
        mean value directly.
        """
        a = float(ParamList[0])
        return self.expovariate(a)
        
    def nextPoisson( self, ParamList ):
        """
        returns a random variable with Poisson distribution 
        of mean mean.  
        """
        mean = float(ParamList[0])
        return self.expovariate(1.0/mean)
        
    def nextHyperExponential2( self, ParamList ):
        """
        returns a random variable with HyperExponential distribution 
        with 2 branches. The probability of choosing branch 1 is 
        Branch1Probability; the probability of choosing branch 2 is
        1.0 - Branch1Probability. The branch <i> scale parameter is 
        Branch<i>A. 
        
        Note that A is 1 per desired mean. Use HyperPoisson2 to pass
        the mean values directly.
        """
        Branch1Probability = float(ParamList[0])
        Branch1A = float(ParamList[1])
        Branch2A = float(ParamList[2])
        
        if self.AuxRandom.random() < Branch1Probability:
            return self.expovariate(Branch1A)
        else:
            return self.expovariate(Branch2A)
        
    def nextHyperPoisson2( self, ParamList ):
        """
        returns a random variable with Poisson distribution 
        with 2 branches. The probability of choosing branch 1 is 
        Branch1Probability; the probability of choosing branch 2 is
        1.0 - Branch1Probability. The branch <i> mean parameter is 
        Branch<i>Mean. 
        """
        Branch1Probability = float(ParamList[0])
        Branch1Mean = float(ParamList[1])
        Branch2Mean = float(ParamList[2])
        
        if self.AuxRandom.random() < Branch1Probability:
            return self.expovariate(1.0/Branch1Mean)
        else:
            return self.expovariate(1.0/Branch2Mean)
    
    def nextWeibull( self, ParamList ):
        """ 
        returns a random variable with Weibull distribution 
        of scale parameter alpha and shape parameter beta.
        
        Note that both alpha and beta must be greater than 0.
        """
        alpha = float(ParamList[0])
        beta = float(ParamList[1])
        return self.weibullvariate( alpha, beta )
        
    def nextLogNormal( self, ParamList ):
        """ 
        returns a random variable with LogNormal distribution 
        of ln(x) mean mu and of ln(x) standard deviation sigma.
        
        Note that both mu and sigma must be greater than 0.
        """
        mu = float(ParamList[0])
        sigma = float(ParamList[1])
        return self.lognormvariate( mu, sigma )
        
    def nextBetaLessOne( self, a, b ):
        """
        UNTESTED 
        returns a random variable with Beta distribution 
        of scale parameters a and b.
        
        Note that both a and b must be greater than 0, but smaller than 1.
        
        Reference:
        This is the Python implementation as described in 
        Raj Jain, The Art of Computer Systems Performance Analysis,
        John Wiley and Sons, 1991, ISBN-0-471-50336-3,
        Chapter 29. Commonly Used Distributions, pp.485-486 (Beta)
        """
        Done = 0
        while Done == 0:
            u1 = self.AuxRandom.random()
            u2 = self.AuxRandom.random()
            x = math.pow(u1, 1.0/a)
            y = math.pow(u2, 1.0/b)
            if x + y <= 1.0:
                Done = 1
        return x/(x+y)
        
    def nextGamma( self, ParamList ):
        """ 
        UNTESTED
        returns a random variable with Gamma distribution 
        of scale parameter a and of shape parameter b.
        
        Note that both a and b must be greater than 0.
        
        Reference:
        This is the Python implementation as described in 
        Raj Jain, The Art of Computer Systems Performance Analysis,
        John Wiley and Sons, 1991, ISBN-0-471-50336-3,
        Chapter 29. Commonly Used Distributions, 490-491(Gamma)
        """
        a = float(ParamList[0])
        b = float(ParamList[1])
        
        intb = math.floor(b)
        diffbintb = b - math.floor(b)
        
        fGamma = 0.0
        if b >= 1:
            index = 1
            product = 0
            while index <= math.floor(b):
                product = product + self.AuxRandom.random()
                index = index + 1
            fGamma = fGamma + (-a) * math.log(product)
            
        if diffbintb > 0:
            x = self.nextBetaLessOne(diffbintb,1.0-diffbintb) # Beta(b,1-b)
            y = -math.log(self.AuxRandom.random()) # exp(1)
            fGamma = fGamma + a * x * y
            
        return fGamma
