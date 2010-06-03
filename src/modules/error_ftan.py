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
from scipy import optimize
import pdb
import os
from matplotlib import rcParams
rcParams={'backend':'Agg'}

class ErrorEstimateError(Exception): pass

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
    if len(fl) < 6:
        raise ErrorEstimateError("not enough substack dispersion curves")
    po,co = loadtxt(fdisp,usecols=(2,4),unpack=True)
    derr = zeros((len(fl),len(po)))
    cnt = 0
    for _f in fl:
        p,c = loadtxt(_f,usecols=(2,4),unpack=True)
        idx = where((po >= p[0]) & (po <=p[-1]))
        derr[cnt,idx] = interp(po[idx],p,c)
        cnt += 1
    if not any(derr):
        raise ErrorEstimateError("no overlap between dispersion curves")
    d = ma.masked_equal(derr,0)
    e = abs(d-co)
    errplus = co+e.mean(axis=0)
    errmin = co-e.mean(axis=0)
    ### cubic spline interpolation
    #rep = scint.splrep(po[~errplus.mask],errplus.data[~errplus.mask])
    #epn = scint.splev(po,rep)
    #rep = scint.splrep(po[~errmin.mask],errmin.data[~errmin.mask])
    #emn = scint.splev(po,rep)
    ### polynomial fit
    rep = poly1d(polyfit(po[~errplus.mask],errplus.data[~errplus.mask],3))
    epn = rep(po)
    rep = poly1d(polyfit(po[~errmin.mask],errmin.data[~errmin.mask],3))
    emn = rep(po)
    return po, epn, emn

def ev_err(dirn,averr=True,errvssnr=False):
    """
    make statistics from error measurements
    """
    if averr:
        fl = glob.glob(os.path.join(dirn,'*.mean_err'))
        periods = arange(1., 20.,.2)
        errup = zeros((len(fl),periods.size))
        errlow = zeros((len(fl),periods.size))
        globsnr = zeros((len(fl),periods.size))
        cnt = 0
        for _f in fl:
            p,l,u = loadtxt(_f,unpack=True)
            fsnr = _f.replace('2_DISP.mean_err','snr.txt')
            p1,snr = loadtxt(fsnr,unpack=True)
            idx = where((periods >= p[0]) & (periods <= p[-1]))
            errup[cnt,idx] = interp(periods[idx],p,u)
            errlow[cnt,idx] = interp(periods[idx],p,l)
            globsnr[cnt,idx] = interp(periods[idx],p1,snr)
            cnt += 1
        eu = ma.masked_equal(errup,0.)
        el = ma.masked_equal(errlow,0.)
        gsnr = ma.masked_equal(globsnr,0.)
        scatter(periods,eu.mean(axis=0),c=gsnr.mean(axis=0))
        scatter(periods,el.mean(axis=0),c=gsnr.mean(axis=0))
        xlabel('Period [s]')
        ylabel('Velocity [km/s]')
        cbar = colorbar()
        cbar.set_label('SNR [dB]')
        savefig('error_vs_period.pdf')

        figure()
        x = gsnr.mean(axis=0)
        y = (eu.mean(axis=0)-el.mean(axis=0))/2.
        plot(x,y,'k.')
        fitfunc = lambda p,x: p[0]/x**4+p[1]
        errfunc = lambda p,x,y: fitfunc(p,x)-y
        p0=[1.,0.]
        p1, success = optimize.leastsq(errfunc,p0[:],args=(x,y))
        print p1
        nv = fitfunc(p1,x)
        plot(x,nv)
        xlabel('SNR [dB]')
        ylabel('Mean error [km/s]')
        savefig('snr_vs_error.pdf')
        figure()
        plot(periods,y)
        plot(periods,nv)
        xlabel('Period [s]')
        ylabel('Mean error [km/s]')
        savefig('comp_error.pdf')
        
            
    if errvssnr:
        fl = glob.glob(os.path.join(dirn,'*.mean_err'))
        for _f in fl:
            fsnr = _f.replace('2_DISP.mean_err','snr.txt')
            p0,l,u = loadtxt(_f,unpack=True)
            p1,snr = loadtxt(fsnr,unpack=True)
            idx = where((p1 >= p0[0]) & (p1 <= p0[-1]))
            nl = interp(p1[idx],p0,l)
            nu = interp(p1[idx],p0,u)
            std = (nu-nl)/2.
            scatter(p1[idx],std,c=snr[idx])

if __name__ == '__main__':
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_S06_S13.SAC_s_2_DISP.c1'
    #forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_LPAP_S07.SAC_s_2_DISP.c1'
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_S24_S08.SAC_s_2_DISP.c1'
    if 0:
        po, epn, emn = err_seas_var(forig)
        plot(po,epn)
        plot(po,emn)
    if 0:
        files = glob.glob('/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_*.SAC_s_2_DISP.c1')
        for _f in files:
            print _f
            fout = _f.replace('.c1','.mean_err')
            if os.path.isfile(fout): continue
            try:
                po, epn, emn = err_seas_var(_f)
                savetxt(fout,vstack(((po,emn),epn)).T)
            except ErrorEstimateError, e:
                print e,_f
                continue
    if 1:
        dirn = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/'
        ev_err(dirn)
