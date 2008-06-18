#!/usr/bin/env python
import numpy as np
import c_stack as c
import pysacio as p

def stack(trace1, trace2):
    test = np.zeros((5),float)
    typetest= type(test) 
    datatest=test.dtype        
    if type(trace1) != typetest:
        print "ERROR: 1st input argument not valid numpy array!"
        return 0
    if type(trace2) != typetest:
        print "ERROR: 2nd input argument not valid numpy array!"
        return 0
    if trace1.dtype != datatest:
        print "ERROR: 1st input argument not a float numpy array!"
        return 0
    if trace1.dtype != datatest:
        print "ERROR: 2nd input argument not a float numpy array!"
        return 0
    n = len(trace1)
    if n != len(trace2):
        print "ERROR: input arguments don't have same length!"
        return 0
    a = np.zeros((n),float)
    if c.stack(trace1, trace2, a):
        return a
    




if __name__ == '__main__':
    file1 = '../../testing/testdata/fanchi/Jan/5to100/COR/COR_MATA_TIKO.SAC'
    file2 = '../../testing/testdata/fanchi/Jan/5to100/COR/COR_MATA_TIKO.SAC'
    [hf1,hi1,hs1,seis1,ok1] = p.ReadSacFile(file1)
    [hf2,hi2,hs2,seis2,ok2] = p.ReadSacFile(file2)
    trace1 = np.array(seis1, dtype=float)
    trace2 = np.array(seis2, dtype=float)
    result = stack(trace1, trace2)
