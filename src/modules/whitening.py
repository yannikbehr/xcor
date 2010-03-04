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
import progressbar as pg

class WhitenError(Exception): pass
DEBUG = True

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
    

def whitening(sdb,ne,ns,plow,phigh,filename,testtrace=None):
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

    ### calculate sampling interval for amplitude and phase
    npts = tr.GetHvalue('npts')
    ns = 2**max(int(log(float(npts))/log(2.0))+1,13);
    dom = 1.0/delta/ns
    ### write traces to disc
    trace2sac(s,tr,filename)
    trace2sac(samp,tr,filename+'.am',delta=dom)
    trace2sac(sph,tr,filename+'.ph',delta=dom)

def trace2sac(trace,sacf,filename,**kw):
    """
    write trace as sac-file onto disc
    """
    nf = ReadSac()
    nf.seis = trace
    nf.hf = sacf.hf.copy()
    nf.hi = sacf.hi.copy()
    nf.hs = sacf.hs.copy()
    if len(kw.keys()) > 0:
        for _k in kw.keys():
            nf.SetHvalue(_k,kw[_k])
    nf.WriteSacBinary(filename)
    

def make_file_name(sdb,ne,ns,rootdir,phigh,plow):
    """
    create output file
    """
    bpfile = "%.1fto%.1f"%(phigh,plow)
    a = sdb.rec[ne][ns].ft_fname.split('/')
    year = a[-4]
    mon = a[-3]
    day = a[-2]
    newd = os.path.join(rootdir,bpfile,year,mon,day)
    if not os.path.isdir(newd):
        os.makedirs(newd)
    newf = os.path.join(newd,a[-1])
    return newf

    
if __name__ == '__main__':
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
        else:
            print "missing or unknown command line argument: %s"%sys.argv[1]
            raise Exception
    except Exception:
        print "usage: %s -c config-file"%os.path.basename(sys.argv[0])
        sys.exit(1)
        
    conf = SafeConfigParser()
    conf.read(config)

    ### frequency band +- 20% as taper
    rootdir = conf.get("whitening","rootdir")
    tmpdir = conf.get("whitening","tmpdir")
    dbname = conf.get("whitening","dbname")
    prefix = conf.get("whitening", "prefix")
    phigh = float(conf.get("whitening", "upperperiod"))
    plow = float(conf.get("whitening", "lowerperiod"))
    sdb = read_db(os.path.join(tmpdir,dbname))
    if not DEBUG:
        widgets = ['whitening: ', pg.Percentage(), ' ', pg.Bar('#'),
                   ' ', pg.ETA()]
        pbar = pg.ProgressBar(widgets=widgets, maxval=sdb.nev*sdb.nst).start()

    for ne in xrange(sdb.nev):
        for ns in xrange(sdb.nst):
            if not os.path.isfile(sdb.rec[ne][ns].ft_fname):continue
            if not DEBUG:
                pbar.update(ne*ns)
            else:
                print sdb.rec[ne][ns].fname
            fn = make_file_name(sdb,ne,ns,rootdir,phigh,plow)
            whitening(sdb,ne,ns,plow,phigh,fn)
    if not DEBUG:
        pbar.finish()
