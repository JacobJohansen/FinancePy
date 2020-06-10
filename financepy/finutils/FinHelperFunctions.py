##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

import numpy as np
from numba import njit
from typing import get_origin, get_args, List, Union
from .FinDate import FinDate
from .FinGlobalVariables import gDaysInYear
from .FinError import FinError

##########################################################################

def checkDate(d):

    if isinstance(d, FinDate) is False:
        raise FinError("Should be a date dummy!")

##########################################################################

def dump(obj):
    ''' Get a list of all of the attributes of a class (not built in ones) '''

    attrs = dir(obj)

    non_function_attributes = [attr for attr in attrs
                               if not callable(getattr(obj, attr))]

    non_internal_attributes = [attr for attr in non_function_attributes
                               if not attr.startswith('__')]

    private_attributes = [attr for attr in non_internal_attributes
                          if attr.startswith('_')]

    public_attributes = [attr for attr in non_internal_attributes
                         if not attr.startswith('_')]

    print("PRIVATE ATTRIBUTES")
    for attr in private_attributes:
        x = getattr(obj, attr)
        print(attr, x)

    print("PUBLIC ATTRIBUTES")
    for attr in public_attributes:
        x = getattr(obj, attr)
        print(attr, x)

##########################################################################


def printTree(array, depth=None):
    ''' Function that prints a binomial or trinonial tree to screen for the
    purpose of debugging. '''
    n1, n2 = array.shape

    if depth is not None:
        n1 = depth

    for j in range(0, n2):
        for i in range(0, n1):
            x = array[i, n2-j-1]
            if x != 0.0:
                print("%10.5f" % x, end="")
            else:
                print("%10s" % '-', end="")
        print("")

##########################################################################


def inputFrequency(f):
    ''' Function takes a frequency number and checks if it is valid. '''
    if f in [-1, 0, 1, 2, 3, 4, 6, 12]:
        return f
    else:
        raise ValueError("Unknown frequency" + str(f))

###############################################################################


def inputTime(dt, curve):
    ''' Validates a time input in relation to a curve. If it is a float then
    it returns a float as long as it is positive. If it is a FinDate then it
    converts it to a float. If it is a Numpy array then it returns the array
    as long as it is all positive. '''

    small = 1e-8

    def check(t):
        if t < 0.0:
            raise ValueError("Date " + str(dt) +
                             " is before curve date " + str(curve._curveDate))
        elif t < small:
            t = small
        return t

    if isinstance(dt, float):
        t = dt
        return check(t)
    elif isinstance(dt, FinDate):
        t = (dt - curve._curveDate) / gDaysInYear
        return check(t)
    elif isinstance(dt, np.ndarray):
        t = dt
        if np.any(t) < 0:
            raise ValueError("Date is before curve value date.")
        t = np.maximum(small, t)
        return t
    else:
        raise ValueError("Unknown type.")

###############################################################################


@njit(fastmath=True, cache=True)
def listdiff(a, b):
    ''' Calculate a vector of differences between two equal sized vectors. '''

    if len(a) != len(b):
        raise ValueError("Cannot diff lists with different sizes")
        return []

    diff = []
    for x, y in zip(a, b):
        diff.append(x - y)

    return diff

##########################################################################


@njit(fastmath=True, cache=True)
def dotproduct(xVector, yVector):
    ''' Fast calculation of dot product using Numba. '''

    dotprod = 0.0
    n = len(xVector)
    for i in range(0, n):
        dotprod += xVector[i] * yVector[i]
    return dotprod

##########################################################################


@njit(fastmath=True, cache=True)
def frange(start, stop, step):
    x = []
    while start <= stop:
        x.append(start)
        start += step

    return x

##########################################################################


@njit(fastmath=True, cache=True)
def normaliseWeights(wtVector):
    ''' Normalise a vector of weights so that they sum up to 1.0. '''

    n = len(wtVector)
    sumWts = 0.0
    for i in range(0, n):
        sumWts += wtVector[i]
    for i in range(0, n):
        wtVector[i] = wtVector[i]/sumWts
    return wtVector

##########################################################################


def labelToString(label, value, separator="\n", listFormat=False):
    ''' Format label/value pairs for a unified formatting. '''
    # Format option for lists such that all values are aligned:
    # Label: value1
    #        value2
    #        ...
    label = str(label)

    if listFormat and type(value) is list and len(value) > 0:
        s = label + ": "
        labelSpacing = " " * len(s)
        s += str(value[0])

        for v in value[1:]:
            s += "\n" + labelSpacing + str(v)
        s += separator

        return s
    else:
        return f"{label}: {value}{separator}"

##########################################################################
    
def toUsableType(t):
    ''' Convert any special types from the `typing` module into types
    that can be used with `isinstance`. '''
    origin = get_origin(t)
    if origin is list:
        return (list, np.ndarray)
    elif origin is Union:
        # `toUsableType` is mapped onto all types inside the `Union`
        types = get_args(t)
        return tuple(toUsableType(tp) for tp in types)
    else:
        return t

##########################################################################

def checkArgumentTypes(func, values):
    ''' Check that all values passed into a function are of the same type
    as the function annotations. If a value has not been annotated, it
    will not be checked. '''
    for valueName, annotationType in func.__annotations__.items():
        value = values[valueName]
        usableType = toUsableType(annotationType)
        if(not isinstance(value, usableType)):
            s = f"In {func.__module__}.{func.__name__}:\n"
            s += f"Mismatched Types: expected a "
            s += f"{valueName} of type '{usableType.__name__}', however"
            s += f" a value of type '{type(value).__name__}' was given."
            raise FinError(s)
