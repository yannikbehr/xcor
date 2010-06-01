#!/usr/bin/env mypython
"""
Calculate the standard deviation of dispersion
curves by evaluating the substacks
"""

import glob
from obspy.core import read
from pylab import *
import scipy.io as sio
import scipy.interpolate as scint

def err_amp_map(fdisp):
    """
    Using the width of the envelope peaks from the amplitude map to
    estimate the error of the dispersion curve (still experimental).
    """
    p,u,c = loadtxt(fdisp,usecols=(2,3,4),unpack=True)
    st = read(fdisp.replace('_2_DISP.c1',''))
    amp,snr,wdth = loadtxt(fdisp,usecols=(5,6,7),unpack=True)
    errplus = st[0].stats.sac.dist/(st[0].stats.sac.dist/c+wdth/20.)
    errmin = st[0].stats.sac.dist/(st[0].stats.sac.dist/c-wdth/20.)
    plot(p,errplus)
    plot(p,errmin)
    plot(p,c,'ko')
    
def err_seas_var(fdisp):
    """
    Estimate the error from the seasonal variability of the
    dispersion curves
    """
    fl = glob.glob(fdisp.replace('_s_2_DISP.c1','_err*DISP*.c1'))
    po,co = loadtxt(fdisp,usecols=(2,4),unpack=True)
    derr = zeros((len(fl),len(po)))
    cnt = 0
    for _f in fl:
        p,c = loadtxt(_f,usecols=(2,4),unpack=True)
        idx = where((po >= p[0]) & (po <=p[-1]))
        derr[cnt,idx] = interp(po[idx],p,c)
        cnt += 1
    d = ma.masked_equal(derr,0)
    e = abs(d-co)
    errplus = co+e.mean(axis=0)
    errmin = co-e.mean(axis=0)
    ### cubic spline interpolation
    rep = scint.splrep(po[~errplus.mask],errplus.data[~errplus.mask])
    epn = scint.splev(po,rep)
    rep = scint.splrep(po[~errmin.mask],errmin.data[~errmin.mask])
    emn = scint.splev(po,rep)
    plot(po,epn)
    plot(po,emn)
    plot(po,co,'ko')


if __name__ == '__main__':
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_S06_S13.SAC_s_2_DISP.c1'
    #forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_LPAP_S07.SAC_s_2_DISP.c1'
    err_seas_var(forig)
    figure()
    err_amp_map(forig)
    
