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
    
def err_seas_var(fdisp,subdir,pv=True,gv=False):
    """
    Estimate the error from the seasonal variability of the
    dispersion curves
    """
    if pv:
        pattern = '_s_2_DISP.c1'
        odir = os.path.dirname(fdisp)
        ndir = os.path.join(os.path.dirname(fdisp),subdir)
        fdisp_new = fdisp.replace(odir,ndir)
        fl = glob.glob(fdisp_new.replace(pattern,'_err*DISP*.c1'))
    if gv:
        pattern = '_s_2_DISP.1'
        odir = os.path.dirname(fdisp)
        ndir = os.path.join(os.path.dirname(fdisp),subdir)
        fdisp_new = fdisp.replace(odir,ndir)
        fl = glob.glob(fdisp_new.replace(pattern,'_err*DISP*.1'))
    if len(fl) < 6:
        raise ErrorEstimateError("not enough substack dispersion curves")
    if pv:
        po,co = loadtxt(fdisp,usecols=(2,4),unpack=True)
    if gv:
        po,co = loadtxt(fdisp,usecols=(2,3),unpack=True)
    derr = zeros((len(fl),len(po)))
    cnt = 0
    for _f in fl:
        if pv:
            p,c = loadtxt(_f,usecols=(2,4),unpack=True)
        if gv:
            p,c = loadtxt(_f,usecols=(2,3),unpack=True)
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

def ev_err(dirn,func,p0,averr=True,errvssnr=False,gv=False,logscale=True,save=True):
    """
    make statistics from error measurements
    """
    if averr:
        if gv:
            fl = glob.glob(os.path.join(dirn,'*.mean_err_u'))
        else:
            fl = glob.glob(os.path.join(dirn,'*.mean_err'))
        periods = arange(1., 20.,.2)
        errup = zeros((len(fl),periods.size))
        errlow = zeros((len(fl),periods.size))
        globsnr = zeros((len(fl),periods.size))
        cnt = 0
        for _f in fl:
            p,l,u = loadtxt(_f,unpack=True)
            if gv:
                fsnr = _f.replace('2_DISP.mean_err_u','snr.txt')
            else:
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
        ylim(1.5,4.5)
        if save:
            savefig('error_vs_period_love_u.pdf')

        figure()
        ax1 = subplot(111)
        x = gsnr.mean(axis=0)
        y = abs((eu.mean(axis=0)-el.mean(axis=0))/2.)
        sidx = argsort(x.data)
        xs = x[sidx]
        ys = y[sidx]
        plot(xs,ys,'k.')
        errfunc = lambda p,x,y: fitfunc(p,x)-y
        #cidx = where((xs>=2.5) & (ys>0.01))
        cidx = where((xs > 4.) & (xs < 7.))
        #cidx = xs > 5.
        #cidx = where((xs.data > 4.) & (xs.data < 8.))
        if logscale:
            p1, success = optimize.leastsq(errfunc,p0[:],args=(xs[cidx],log(ys[cidx])))
        else:
            p1, success = optimize.leastsq(errfunc,p0[:],args=(xs[cidx],ys[cidx]))
        print p1
        nv = fitfunc(p1,xs[cidx])
        if logscale:
            plot(xs[cidx],exp(nv))
        else:
            plot(xs[cidx],nv)
        ax1.set_ylabel('Mean error [km/s]')

        ax2 = ax1.twinx()
        a,b = histogram(xs,range=(0,10),normed=True)
        plot(b[:-1]+diff(b)/2,cumsum(a),'r')
        ax2.set_ylabel('Cumulative histogram')
        xlabel('SNR [dB]')
        if save:
            savefig('snr_vs_error_love_u.pdf')

        
        figure()
        plot(periods,y)
        if logscale:
            plot(periods,exp(fitfunc(p1,x)))
        else:
            plot(periods,fitfunc(p1,x))
        xlabel('Period [s]')
        ylabel('Mean error [km/s]')
        if save:
            savefig('comp_error_love_u.pdf')
        
            
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


def diff_caus_acaus(dirn,spattern,gv=False):
    fl = glob.glob(os.path.join(dirn,spattern))
    periods = linspace(1.0,30.0,200)
    err_diff = zeros((len(fl),periods.size))
    rms_diff = array([])
    cnt = 0
    for _f in fl:
        fp = _f+'_p_2_DISP.c1'
        fn = _f+'_n_2_DISP.c1'
        if gv:
            fp = _f+'_p_2_DISP.1'
            fn = _f+'_n_2_DISP.1'
        if os.path.isfile(fp) and os.path.isfile(fn):
            tr = read(_f,headonly=True,format='SAC')[0]
            dist = tr.stats.sac.dist
            pp,cp = loadtxt(fp,usecols=(2,3),unpack=True)
            pn,cn = loadtxt(fn,usecols=(2,3),unpack=True)
            pmin = max(pp.min(),pn.min())
            pmax = min(pp.max(),pn.max())
            idx = where((periods >= pmin)&(periods <= pmax))
            ncp = interp(periods[idx],pp,cp)
            ncn = interp(periods[idx],pn,cn)
            #err_diff[cnt,idx[0]] = sqrt((dist/ncp-dist/ncn)**2)
            err_diff[cnt,idx[0]] = sqrt((ncp-ncn)**2)
            #rms_diff = append(rms_diff,sqrt(sum((dist/ncp-dist/ncn)**2)))
            rms_diff = append(rms_diff,sqrt(sum((ncp-ncn)**2)))
            cnt += 1
    return periods, err_diff, rms_diff, cnt
    
if __name__ == '__main__':
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_S06_S13.SAC_s_2_DISP.c1'
    #forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_LPAP_S07.SAC_s_2_DISP.c1'
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_S24_S08.SAC_s_2_DISP.c1'
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse_horizontal/COR_LWTT_S13.SAC_TT_s_2_DISP.c1'
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_LDEN_S22.SAC_s_2_DISP.1'
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse_horizontal/COR_LWTT_S13.SAC_TT_s_2_DISP.1'
    if 0:
        subdir = 'err'
        po, epn, emn = err_seas_var(forig,subdir,gv=True,pv=False)
        plot(po,epn)
        plot(po,emn)
    if 0:
        #files = glob.glob('/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_*.SAC_s_2_DISP.c1')
        #files = glob.glob('/data/wanakaII/yannik/cnipse/stack_start_cnipse_horizontal/COR_*.SAC_TT_s_2_DISP.c1')
        files = glob.glob('/data/wanakaII/yannik/cnipse/stack_start_cnipse_horizontal/COR_*.SAC_TT_s_2_DISP.1')
        subdir = 'err'
        for _f in files:
            print _f
            fout = _f.replace('.1','.mean_err_u')
            if os.path.isfile(fout): continue
            try:
                po, epn, emn = err_seas_var(_f,subdir,gv=True,pv=False)
                savetxt(fout,vstack(((po,emn),epn)).T)
            except ErrorEstimateError, e:
                print e,_f
                continue
    if 1:
        dirn = '/data/wanakaII/yannik/cnipse/stack_start_cnipse_horizontal/'
        fitfunc = lambda p,x: p[0]*x+p[1]
        p0 = [1.,1.]
        #fitfunc = lambda p,x: 1./(p[0]*x**2+p[1]*x+p[2])
        #p0 = [1.,1.,0.]
        ev_err(dirn,fitfunc,p0,gv=True,logscale=True,save=True)

    if 0:
        dirn = '/data/wanakaII/yannik/cnipse/stack_start_cnipse_horizontal/'
        spattern = 'COR*.SAC_TT'
        periods, err_diff, rms_diff, cnt = diff_caus_acaus(dirn,spattern,gv=False)
        nerr = ma.masked_equal(err_diff,0.)
        figure()
        plot(periods,nerr.mean(axis=0))
        xlabel('Periods [s]')
        ylabel('RMS [km/s]')
        ylim(0,2)
        savefig('rms_diff_caus_acaus_love_c.pdf')
        figure()
        hist(rms_diff,bins=100,range=(0,4))
        xlabel('RMS [km/s]')
        savefig('rms_hist_caus_acaus_love_c.pdf')
