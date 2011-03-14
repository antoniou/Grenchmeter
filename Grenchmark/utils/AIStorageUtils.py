#! /usr/bin/env python


__author__ = 'Alexandru Iosup';
__email__ = 'A.Iosup at ewi.tudelft.nl';
__file__ = 'AIStorageUtils.py';
#__version__ = '$Rev: %s$' % __rev;
__date__ = "$Date: 2006/10/21 14:19:35 $"
__copyright__ = "Copyright (c) 2005 Alexandru IOSUP"
__license__ = "Python"  

#---------------------------------------------------
# Log:
# 15/10/2007 C.S. 1.11 Commented line 7 (does not work with the python 2.3.4 version installed on the
#			cluster from P.U.B.)
# 27/01/2005 A.I. 1.1 Added method dict_sortbyvalue_dict
# 27/01/2005 A.I. 1.0 Finished version used in Delft's BitTorrent measurements 2004
# 01/09/2004 A.I. 0.1 Started this app
#---------------------------------------------------
 
SORT_ASCENDING  = 0
SORT_DESCENDING = 1

SORT_LOSSY      = 0
SORT_NONLOSSY   = 1

SORT_TYPE_INT     = 0
SORT_TYPE_STRING  = 1
SORT_TYPE_FLOAT   = 2

# Hans Nowak, Snippet 174, Python Snippet Support Team
# http://www.faqts.com/knowledge_base/view.phtml/aid/4364/fid/541
#
_swap2 = lambda (x,y): (y,x)
_swap3 = lambda (x,y): (y[_swap3_id],x)
_swap3_noloss = lambda (x,y): (y[_swap3_id],(x,y))
_unswap3_noloss = lambda (x,y): (y[0],y[1])

def dict_sortbyvalue(dict, direction = SORT_ASCENDING):
    """ 
    Returns a list of (key, value) pairs, sorted by value. 
    Set the direction to SORT_ASCENDING for an ascending sort, 
    and to SORT_DESCENDING for a descending sort.
    """
    mdict = map(_swap2, dict.items())
    if direction == SORT_ASCENDING:
        mdict.sort() # sort ascending
    else: 
        mdict.sort( lambda x, y: -cmp(x, y) ) # sort descending
    mdict = map(_swap2, mdict)
    return mdict
    
def dict_sortbykey(dict, direction = SORT_ASCENDING):
    """ 
    Returns a list of (key, value) pairs, sorted by keys. 
    Set the direction to SORT_ASCENDING for an ascending sort, 
    and to SORT_DESCENDING for a descending sort.
    """
    mdict = map(lambda (x,y): (x,y), dict.items())
    if direction == SORT_ASCENDING:
        mdict.sort() # sort ascending
    else: 
        mdict.sort( lambda x, y: -cmp(x, y) ) # sort descending
    return mdict

def mycmp(id, a, b ):
    print a, b
    if a[id] < b[id]:
        return -1
    elif a[id] > b[id]:
        return 1
    else: 
        return 0

def dict_sortbyvalue_tuples(dict, sortID = 0, direction = SORT_ASCENDING, loss_strategy = SORT_LOSSY):
    """ 
    Returns a list of (key, value) pairs, sorted by value, given the loss strategy.

    If loss_strategy is LOSSY:
    The original dictionary contains a tuple associated with each
    key. The value in the (key, value) pairs list is selected
    using the ID and serves as the sorting key. No other value
    from the tuples is returned/used.

    If loss_strategy is NON-LOSSY:
    The original dictionary contains a tuple associated with each
    key. The returned list contains tuples with the original keys
    as the first value, then the sort key (identified by the sortID),
    and then the other values from the tuple associated with the
    key in the input dictionary.    
    
    Set sortID to the ID of the sort key in the tuple 
       (e.g. ('Name', 123) -> sortID=0 => sort after name, 
                              sortID=1 => sort after numerical value )
                              
    Set the direction to SORT_ASCENDING for an ascending sort, and to SORT_DESCENDING for a descending sort.

    Set the loss_strategy to SORT_LOSSY for a return list with just the keys
    and the sort key or to SORT_NONLOSSY for a return list with the keys and
    all the data associated with that key in the original dictionary.
    """
    global _swap3_id

    _swap3_id = sortID

    if loss_strategy == SORT_LOSSY:
        mdict = map(_swap3, dict.items())
    else:
        mdict = map(_swap3_noloss, dict.items())
        
    if direction == SORT_ASCENDING:
        mdict.sort() # sort ascending
    else:
        mdict.sort( lambda x, y: -cmp(x, y) ) # sort descending

    if loss_strategy == SORT_LOSSY:
        mdict = map(_swap2, mdict)
    else:
        mdict = map(_unswap3_noloss, mdict)

    return mdict

def my_cmpint( id, a, b ):
    # ( sortIDValue, ( OldDicKey, {Key1: Value1, ..., sortID:sortIDValue, ...}))
    # -> a[1][1] = {...}; a[1][1][id] = sortIDValue
    #DEBUG: print id, ":", a[1][1][id], "?", b[1][1][id]
    if int(a[1][1][id]) < int(b[1][1][id]):
        return -1
    elif int(a[1][1][id]) > int(b[1][1][id]):
        return 1
    else: 
        return 0
        
def my_cmpfloat( id, a, b ):
    if float(a[1][1][id]) < float(b[1][1][id]):
        return -1
    elif float(a[1][1][id]) > float(b[1][1][id]):
        return 1
    else: 
        return 0

def dict_sortbyvalue_dict(dict, sortID, sortIDType = SORT_TYPE_INT, direction = SORT_ASCENDING):
    """ 
    Suppose you have a dictionary with each value a dictionary: a dictionary
    of subdictionaries. 
    
    D = { SD1, SD2, ..., SD_n}. 
    SD_i = { SubKey1:SubValue1, ..., SubKey_m:SubValue_m}
    
    You want to sort this dictionary by SubValue_k of SubKey_k, and get back
    a dictionary indexed by SubKey_k, with values sub-dictionaries.
    
    RET= { SubKey_Sort1:SD_Sort1, ... }
    
    
    Set the direction to SORT_ASCENDING for an ascending sort, 
    and to SORT_DESCENDING for a descending sort.

    """
    global _swap3_id

    _swap3_id = sortID

    mdict = map(_swap3_noloss, dict.items())
        
    if sortIDType == SORT_TYPE_STRING:
        if direction == SORT_ASCENDING:
            mdict.sort() # sort ascending
        else:
            mdict.sort( lambda x, y: -cmp(x, y) ) # sort descending
            
    elif sortIDType == SORT_TYPE_INT:
        if direction == SORT_ASCENDING:
            mdict.sort( lambda x, y: my_cmpint(sortID, x, y) ) # sort ascending
        else:
            mdict.sort( lambda x, y: -my_cmpint(sortID, x, y) ) # sort descending
            
    elif sortIDType == SORT_TYPE_FLOAT:
        if direction == SORT_ASCENDING:
            mdict.sort( lambda x, y: my_cmpfloat(sortID, x, y) ) # sort ascending
        else:
            mdict.sort( lambda x, y: -my_cmpfloat(sortID, x, y) ) # sort descending
            
    mdict = map(_unswap3_noloss, mdict)

    return mdict
    
# based on Pawel Garbacki's function
def list_merge(list1, list2):
    """ merge two lists removing double occurences of the same value """
    
    if len(list1) > 0: # merge the two lists
        
        merged_list = []
        new = 0
        for elem in list2:
            if not elem in list1:            
                merged_list.append(elem)
                new = new + 1
        if new > 0: # found new elements
            merged_list.extend(list1)
            return merged_list
        else: # no new element
            return list1
            
    else: # it's just the 2nd list
        return list2
        
if __name__ == "__main__":

    dict = {
        'a': 1,
        'b': 7,
        'c': 3,
        'd': -2,
        'e': 5,
        'f': -6,
        'g': 3.5,
    }

    print dict_sortbyvalue(dict)
    
