#!/usr/bin/env mypython

"""
whitening module to wrap up Fan-Chi Lin's Fortran 77 codes
"""


import os, os.path, string, shutil, glob, sys
from sac_db import *
import filter4
from obspy.sac import *
from pylab import *
import numpy as np
from ConfigParser import SafeConfigParser

class WhitenError(Exception): pass


def smooth(x,window_len=11,window='hanning'):
    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."
    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."
    if window_len<3:
        return x
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
    #s=np.r_[2*x[0]-x[window_len:1:-1],x,2*x[-1]-x[-1:-window_len:-1]]
    if window == 'flat': #moving average
        w=ones(2*window_len+1,'d')
    else:
        w=eval('numpy.'+window+'(2*window_len+1)')
    #y=np.convolve(w/w.sum(),s,mode='same')
    y=np.convolve(w/w.sum(),x,mode='valid')
    y = np.r_[ones(window_len)*y[0],y,ones(window_len)*y[-1]]
    #y = y[window_len-1:-window_len+1]
    #y[0:window_len] = x[0]
    #y[-1:-window_len:-1] = x[-1]
    return y
    #return y[window_len-1:-window_len+1]


def running_av(x,window_len=20):
    a  = arange(x.size)
    av = [x[_i-window_len:_i+window_len+1].sum()/(2*window_len+1) for _i in a[window_len:-window_len]]
    av = r_[ones(window_len)*av[0],av,ones(window_len)*av[-1]]
    y  = av
    return y
    

def whitening(sdb, ne, ns, plow, phigh,testtrace=None):
    """
    this implements the spectral and temporal
    normalization suggested by Bensen et al.
    """
    ### first filter the trace within the target frequency band
    f1 = 1./(plow + 0.2*plow)
    f2 = 1./plow 
    f3 = 1./phigh
    f4 = 1./(phigh - 0.2*phigh)
    tr = ReadSac(sdb.rec[ne][ns].ft_fname)
    delta = tr.GetHvalue('delta')
    ftr = filter4.filter4_c(tr.seis.copy(),f1,f2,f3,f4,delta)
    ### then filter trace within a common frequency band for earthquakes
    feq1 = 1./(50. + 0.2*50.)
    feq2 = 1./50. 
    feq3 = 1./15.
    feq4 = 1./(15. - 0.2*15.)
    eqtr = filter4.filter4_c(tr.seis.copy(),feq1,feq2,feq3,feq4,delta)
    ### smooth the earthquake-trace
    eqtr_s = smooth(np.abs(eqtr),128,'flat')
    ### divide broadband trace by earthquake trace
    ftr_norm = divide(ftr,eqtr_s)
    ### whiten spectrum using running average and write out amplitude and phase
    if testtrace != None:
        s, samp, sph = filter4.smooth_spec(testtrace.copy(),f1,f2,f3,f4,delta,npow=1,winlen=20)
    else:
        s, samp, sph = filter4.smooth_spec(ftr_norm.copy(),f1,f2,f3,f4,delta,npow=1,winlen=20)
    return s, samp, sph, eqtr_s, ftr, ftr_norm
    

if __name__ == '__main__':
    pass
    #conf = SafeConfigParser()
    #dbname = conf.get("whiten","dbname")
    #sdb = sac_db.read_db(dbname)
