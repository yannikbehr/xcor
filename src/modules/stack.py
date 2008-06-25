#!/usr/bin/env python
import numpy as np
import array as a
import c_stack as c
import pysacio as p
import os.path, glob, re, sys

eestack = {}
enstack = {}
nestack = {}
nnstack = {}
patternlist = [(r'COR_(\w*_\w*).SAC.prelim_NE', nestack, 'NE'),\
               (r'COR_(\w*_\w*).SAC.prelim_EN', enstack, 'EN'),\
               (r'COR_(\w*_\w*).SAC.prelim_NN', nnstack, 'NN'),\
               (r'COR_(\w*_\w*).SAC.prelim_EE', eestack, 'EE')]

class TwirlyBar:
    """show progress of program"""
    def __init__(self):
        self.__state = 0
        self.__bar = ('[|]', '[/]', '[-]', '[\\]')

    def ShowProgress(self):
        sys.stdout.write('\b\b\b' +self.__bar[self.__state])
        sys.stdout.flush()
        self.__state = self.__state + 1
        if self.__state > 3: self.__state = 0

tb = TwirlyBar()
        
def stack(trace1, trace2):
    test = np.zeros((5),float)
    typetest= type(test) 
    datatest=test.dtype        
    if type(trace1) != typetest:
        print "ERROR: 1st input argument not valid numpy array!"
        return []
    if type(trace2) != typetest:
        print "ERROR: 2nd input argument not valid numpy array!"
        return []
    if trace1.dtype != datatest:
        print "ERROR: 1st input argument not a float numpy array!"
        return []
    if trace1.dtype != datatest:
        print "ERROR: 2nd input argument not a float numpy array!"
        return []
    n = len(trace1)
    if n != len(trace2):
        print "ERROR: input arguments don't have same length!"
        return []
    a = np.zeros((n),float)
    if c.stack(trace1, trace2, a):
        return a


def find_match(tupatt, f):
    tb.ShowProgress()
    pattern, mystack, comp = tupatt
    match = re.search(pattern,f)
    if match:
        [hf,hi,hs,seis,ok] = p.ReadSacFile(f)
        if not ok:
            print "ERROR: cannot read sac-file %s" %(f)
            return -1
        else:
            trace = np.array(seis, dtype=float)
            if match.group(1) in mystack.keys():
                oldtrace = np.array(mystack[match.group(1)]['trace'], dtype=float)
                newtrace = stack(oldtrace, trace)
                if len(newtrace) > 0:
                    new = {}
                    new[match.group(1)] = {}
                    new[match.group(1)]['trace'] = newtrace
                    new[match.group(1)]['hf'] = hf
                    new[match.group(1)]['hs'] = hs
                    new[match.group(1)]['hi'] = hi
                    mystack.update(new)
                    return 1
                else: return -1
            else:
                mystack[match.group(1)] = {}
                mystack[match.group(1)]['trace'] = trace
                mystack[match.group(1)]['hf'] = hf
                mystack[match.group(1)]['hs'] = hs
                mystack[match.group(1)]['hi'] = hi
                return 1
    else:
        return 0
    
def find_xcor(stackdir, dirname, files):
    corfiles = glob.glob(dirname+'/COR*prelim*')
    if len(corfiles) > 0:
        for f in corfiles:
            for entry in patternlist:
                if find_match(entry, f): break
                elif find_match(entry, f) == -1: break


if __name__ == '__main__':
    file1 = '../../testing/testdata/fanchi/Jan/5to100/COR/COR_MATA_TIKO.SAC'
    file2 = '../../testing/testdata/fanchi/Jan/5to100/COR/COR_MATA_TIKO.SAC'
    rootdir = '/Volumes/stage/stage/yannik78/datasets/nord/nord-sac-EN/'
    stackdir = '/Volumes/stage/stage/yannik78/datasets/nord/nord-sac-EN/STACK'
    [hf1,hi1,hs1,seis1,ok1] = p.ReadSacFile(file1)
    [hf2,hi2,hs2,seis2,ok2] = p.ReadSacFile(file2)
    trace1 = np.array(seis1, dtype=float)
    trace2 = np.array(seis2, dtype=float)
    os.path.walk(rootdir, find_xcor, stackdir)
    if not os.path.isdir(stackdir):
        os.mkdir(stackdir)
    for i in patternlist:
        pattern, mystack, comp = i
        for stat in mystack.keys():
            outputfile = stackdir+'/COR_'+stat+'.SAC_'+comp
            print 'writing',outputfile
            print mystack[stat]
            seis = mystack[stat]['trace']
            hf = mystack[stat]['hf']
            hs = mystack[stat]['hs']
            hi = mystack[stat]['hi']
            p.WriteSacBinary(outputfile, hf, hi, hs, a.array('f',seis))




