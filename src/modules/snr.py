#!/usr/bin/env mypython

"""
measure signal-to-noise ratios of cross-correlations
"""

import os, sys, glob, os.path, string
from ConfigParser import SafeConfigParser
from obspy.sac import *
import numpy as np
from numpy.fft import *
import filter4
from pylab import *
import progressbar as pg

DEBUG = False

def get_snr(xcorfiles,pattern):
    """
    get snr in decibels
    """
    filelist = glob.glob(os.path.join(xcorfiles,pattern))
    if not DEBUG:
        widgets = ['snr: ', pg.Percentage(), ' ', pg.Bar('#'),
                   ' ', pg.ETA()]
        pbar = pg.ProgressBar(widgets=widgets, maxval=len(filelist)).start()
    nf = 20
    maxP = 50.
    minP = 1.
    minV = 1.0
    maxV = 4.0
    fb = 1./maxP
    fe = 1./minP
    step = (np.log(fb)-np.log(fe))/(nf-1)
    freqs = np.exp(np.log(fe)+np.arange(nf)*step)
    cnt = 0
    for _f in filelist:
        if not DEBUG:
            pbar.update(cnt)
            cnt += 1
        x = ReadSac(_f)
        snrout = _f+'_snr.txt'
        snr = array([])
        ### define the signal window
        minT = max(int(x.b),int(x.dist/maxV - maxP))
        e = x.b+x.npts*x.delta
        maxT = min(int(e-1000),int(x.dist/minV + 2*maxP))
        for k in xrange(1,freqs.size-1):
            f2 = freqs[k+1]
            f3 = freqs[k-1]
            addfac = 0.01
            f1 = f2 - addfac
            f4 = f3 + addfac
            ftr = abs(filter4.filter4_c(x.seis.copy(),f1,f2,f3,f4,x.delta))
            signalmax = ftr[minT:maxT].max()
            noiserms = sqrt(pow(ftr[maxT+500::],2).sum()/(ftr[maxT+500::].size))
            snr = append(snr,10*log10(signalmax/noiserms))
            #snr = append(snr,signalmax/noiserms)
        np.savetxt(snrout,vstack((1./freqs[1:-1],snr)).T)
    if not DEBUG:
        pbar.finish()

        
def snr(datdir,bin,pattern):
    curdir = os.getcwd()
    os.chdir(datdir)
    fn = 'files.txt'
    os.system('ls %s >%s'%(pattern,fn))
    os.system('%s %s'%(bin,fn))
    os.remove(fn)
    os.chdir(curdir)

def main():
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            xcorfiles = cp.get('snr','xcorfiles')
            command   = cp.get('snr','snrbin')
            spattern  = cp.get('snr','spattern')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "usage: %s -c config-file"%os.path.basename(sys.argv[0])
        sys.exit(1)
    else:
        #snr(xcorfiles,command,spattern)
        get_snr(xcorfiles,spattern)

if __name__ == '__main__':
    main()
    
