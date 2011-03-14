

#! /usr/bin/env python

__rev = "0.31";
__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'AIParseUtils.py';
__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:26:21 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python"  

#---------------------------------------------------
# Log:
# 13/09/2005 A.I. 0.2 Change in read*With WeightsList:
#                     values list does *not* have to contain at least
#                     one separator (;), as in the example:
#                     MyWeightedList=Key1/1 
#                     (note: no separator needed in a single value list)
# 28/08/2005 A.I. 0.1 Started this app
#---------------------------------------------------

import traceback

VALUES = 'Values'
TOTAL_WEIGHT = 'TotalWeight'

class TupleValues:
    INT_VALUE = 0
    FLOAT_VALUE = 1
    STRING_VALUE = 2

BooleanToIntDic = {'true':1, 'false':0 }
IntToBooleanDic = {1:'true', 0:'false' }

class ParseError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def readInt( Text, DefaultValue = 0 ):
    """ returns an int, or DefaultValue if a parsing error occurs """
    try:
        Value = int(Text.strip())
    except:
        Value = DefaultValue
    return Value

def readIntRange( Text, Separator = '-' ):
    """ returns a range from a text X-Y, X and Y integers and X<Y ([] for error)"""
    ValuesList = []
    try:
        if Text.find(Separator) >= 0: 
            Min, Max = Text.strip().split(Separator)
            Min = int(Min)
            Max = int(Max)
            if Min >= Max: raise Exception, "Error! X>=Y"
            ValuesList = xrange(Min,Max)
    except:
        ValuesList = []
    return ValuesList
    
def readStringList( Text, ItemSeparator = ';' ):
    """ returns a list of values from a text V1;V2;...;Vn, Vi string ([] for error)"""
    ValuesList = []
    try:
        if Text.find(ItemSeparator) >= 0: 
            ValuesList = Text.strip().split(ItemSeparator)
    except:
        pass
    return ValuesList
    
def readIntList( Text, ItemSeparator = ';' ):
    """ returns a list of values from a text V1;V2;...;Vn, Vi integer ([] for error)"""
    IntValues = []
    try:
        if Text.find(ItemSeparator) >= 0: 
            ValuesList = Text.strip().split(ItemSeparator)
            IntValues = []
            [IntValues.append(int(item)) for item in ValuesList]
    except:
        pass
    return IntValues
    
def readFloatList( Text, ItemSeparator = ';' ):
    """ returns a list of values from a text V1;V2;...;Vn, Vi float ([] for error)"""
    IntValues = []
    try:
        if Text.find(ItemSeparator) >= 0: 
            ValuesList = Text.strip().split(ItemSeparator)
            IntValues = []
            [IntValues.append(float(item)) for item in ValuesList]
    except:
        pass
    return IntValues
    
def readTuple( Text, ValueType = TupleValues.INT_VALUE, ItemSeparator = ',' ):
    """ 
    returns a tuple (V1,V2,..,Vn) from a text '(V1,..,Vn)'; 
    the type of the tuple elements is given as a parameter
    
    in case of error returns None
    """
    tupleValue = None
    ##print "in readTuple", Text
    try:
        if Text[0] != '(' or Text[len(Text)-1] != ')':
            return None
        Text = Text[1:len(Text)-1]
        if ValueType == TupleValues.INT_VALUE:
            Values = readIntList(Text, ItemSeparator=',')
            ##print "Values=", Values
        elif ValueType == TupleValues.FLOAT_VALUE:
            Values = readFloatList(Text, ItemSeparator=',')
            ##print "Values=", Values
        elif ValueType == TupleValues.STRING_VALUE:
            Values = readStringList(Text, ItemSeparator=',')
            ##print "Values=", Values
        if len(Values) > 0:
            tupleValue = tuple(Values)
    except:
        pass
    
    return tupleValue
    

def readIntWithWeightsList( Text, DefaultWeight = 1.0, ItemSeparator = ';', ValueWeightSeparator = '/' ):
    """ returns a list of values from a text V1[/W1];...;Vn[/Wn], Vi integer, Wi float default 1.0 """
    
    # steps:
    # 0. create and reset results list
    # 1. split the list in items
    # 2. foreach item
    #    2.1. try to split in value, weight
    #    2.2. if split correct
    #         then 
    #              try to convert value, weight values to respectively int, float
    #              quit parsing if conversion error
    #         else
    #              try to convert value to int & set weight to default
    #              quit parsing if conversion error
    #    2.3. add new value/weight tuple to results list
    # 3. return the results list and the total weight
    
    ##print '>>>>>>>>>>', "in readIntWithWeightsList", Text
    
    ValuesWidthWeights = []
    WeightSum = 0.0
    try:
        ###if Text.find(ItemSeparator) >= 0: 
        ValuesList = Text.strip().split(ItemSeparator)
        for item in ValuesList:
            ##print '>>>>> ', 'item', item
            item = item.strip()
            if len(item) <= 0:
                ##print "Empty item in "+Text+" weighted list"
                raise ParseError, "Empty item in "+Text+" weighted list"
                
            try:
                iValue, fWeight = item.split(ValueWeightSeparator,1)
                ##print '>>>>> ', "iValue", iValue, "fWeight", fWeight
                try:
                    iValue = int(iValue)
                    fWeight = float(fWeight)
                except ValueError, e:
                    ##print "conversion error: " + str(e)
                    raise ParseError, "conversion error: " + str(e)
                    
            except ValueError:
                try:
                    iValue = int(item)
                    fWeight = DefaultWeight # no weight info present, set to default weight
                except:
                    ##print "Wrong item '"+item+"' in "+Text+" weighted list" 
                    raise ParseError, "Wrong item '"+item+"' in "+Text+" weighted list" 
                
            ValuesWidthWeights.append( (iValue, fWeight) )
            WeightSum = WeightSum + fWeight
            ##print "Added", iValue, "new weight", WeightSum
        ##else:
        ##    print "Cannot find", ItemSeparator, "in", Text
    except:
        pass
    return {VALUES:ValuesWidthWeights, TOTAL_WEIGHT:WeightSum }
    
def readFloatWithWeightsList( Text, DefaultWeight = 1.0, ItemSeparator = ';', ValueWeightSeparator = '/' ):
    """ returns a list of values from a text V1[/W1];...;Vn[/Wn], Vi float, Wi float default 1.0 """
    
    # steps:
    # 0. create and reset results list
    # 1. split the list in items
    # 2. foreach item
    #    2.1. try to split in value, weight
    #    2.2. if split correct
    #         then 
    #              try to convert value, weight values to float, float
    #              quit parsing if conversion error
    #         else
    #              try to convert value to int & set weight to default
    #              quit parsing if conversion error
    #    2.3. add new value/weight tuple to results list
    # 3. return the results list and the total weight
    
    ##print '>>>>>>>>>>', "in readIntWithWeightsList", Text
    
    ValuesWidthWeights = []
    WeightSum = 0.0
    try:
        ###if Text.find(ItemSeparator) >= 0: 
        ValuesList = Text.strip().split(ItemSeparator)
        for item in ValuesList:
            ##print '>>>>> ', 'item', item
            item = item.strip()
            if len(item) <= 0:
                ##print "Empty item in "+Text+" weighted list"
                raise ParseError, "Empty item in "+Text+" weighted list"
                
            try:
                fValue, fWeight = item.split(ValueWeightSeparator,1)
                ##print '>>>>> ', "iValue", iValue, "fWeight", fWeight
                try:
                    fValue = float(fValue)
                    fWeight = float(fWeight)
                except ValueError, e:
                    ##print "conversion error: " + str(e)
                    raise ParseError, "conversion error: " + str(e)
                    
            except ValueError:
                try:
                    fValue = float(item)
                    fWeight = DefaultWeight # no weight info present, set to default weight
                except:
                    ##print "Wrong item '"+item+"' in "+Text+" weighted list" 
                    raise ParseError, "Wrong item '"+item+"' in "+Text+" weighted list" 
                
            ValuesWidthWeights.append( (fValue, fWeight) )
            WeightSum = WeightSum + fWeight
            ##print "Added", iValue, "new weight", WeightSum
        ##else:
        ##    print "Cannot find", ItemSeparator, "in", Text
    except:
        pass
    return {VALUES:ValuesWidthWeights, TOTAL_WEIGHT:WeightSum }
    
def readStringWithWeightsList( Text, DefaultWeight = 1.0, ItemSeparator = ';', ValueWeightSeparator = '/' ):
    """ returns a list of values from a text V1[/W1];...;Vn[/Wn], Vi string, Wi float default 1.0 """
    
    ##print '>>>>>>>>>>', "in readStringWithWeightsList", Text
    
    ValuesWidthWeights = []
    WeightSum = 0.0
    try:
        ###if Text.find(ItemSeparator) >= 0: 
        ValuesList = Text.strip().split(ItemSeparator)
        for item in ValuesList:
            ##print '>>>>> ', 'item', item
            item = item.strip()
            if len(item) <= 0:
                raise ParseError, "Empty item in "+Text+" weighted list"
                
            try:
                sValue, fWeight = item.split(ValueWeightSeparator,1)
                if len(sValue) <= 0:
                    raise ParseError, "Empty value in "+Text+" weighted list"
                try:
                    fWeight = float(fWeight)
                except ValueError, e:
                    ##print "conversion error: " + str(e)
                    raise ParseError, "conversion error: " + str(e)
                    
            except ValueError:
                try:
                    sValue = item
                    fWeight = DefaultWeight # no weight info present, set to default weight
                except:
                    raise ParseError, "Wrong item '"+item+"' in "+Text+" weighted list" 
                
            ValuesWidthWeights.append( (sValue, fWeight) )
            WeightSum = WeightSum + fWeight
            ##print "Added", sValue, "new weight", WeightSum
        ##else:
        ##    print "Cannot find", ItemSeparator, "in", Text
    except Exception, e:
        ##traceback.print_exc()
        pass
        
    return {VALUES:ValuesWidthWeights, TOTAL_WEIGHT:WeightSum }
    
def readTupleWithWeightsList( Text, TupleType = TupleValues.INT_VALUE, DefaultWeight = 1.0, ItemSeparator = ';', TupleItemSeparator=',', ValueWeightSeparator = '/' ):
    """ ... """
    
    ##print '>>>>>>>>>>', "in readTupleWithWeightsList", Text
    
    ValuesWidthWeights = []
    WeightSum = 0.0
    try:
        ###if Text.find(ItemSeparator) >= 0: 
        ValuesList = Text.strip().split(ItemSeparator)
        for item in ValuesList:
            ##print '>>>>> ', 'item', item
            item = item.strip()
            if len(item) <= 0:
                raise ParseError, "Empty item in "+Text+" weighted list"
                
            try:
                sValue, fWeight = item.split(ValueWeightSeparator,1)
                if len(sValue) <= 0:
                    raise ParseError, "Empty value in "+Text+" weighted list"
                try:
                    OneTuple = readTuple( sValue, TupleType, TupleItemSeparator )
                    fWeight = float(fWeight)
                except ValueError, e:
                    ##print "conversion error: " + str(e)
                    raise ParseError, "conversion error: " + str(e)
                    
            except ValueError:
                try:
                    sValue = item
                    OneTuple = readTuple( sValue, TupleType, TupleItemSeparator )
                    fWeight = DefaultWeight # no weight info present, set to default weight
                except:
                    raise ParseError, "Wrong item '"+item+"' in "+Text+" weighted list" 
                
            ValuesWidthWeights.append( (OneTuple, fWeight) )
            WeightSum = WeightSum + fWeight
            ##print "Added", OneTuple, "new weight", WeightSum
        ##else:
        ##    print "Cannot find", ItemSeparator, "in", Text
    except Exception, e:
        ##print traceback.print_exc()
        pass
        
    return {VALUES:ValuesWidthWeights, TOTAL_WEIGHT:WeightSum }    
    
    
def readBoolean( Text, DefaultValue = 1 ):
    try:
        Value = BooleanToIntDic[Text.strip().lower()]
    except Exception, e:
        #print "Wrong value ", "("+Text.strip().lower()+"). Expected true/false. Setting to default..."
        Value = DefaultValue
    return Value
