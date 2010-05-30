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

if 1:
    fl = glob.glob('/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_S06_S13.SAC_err*DISP*.c1')
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_S06_S13.SAC_s_2_DISP.c1'
    fl = glob.glob('/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_LPAP_S07.SAC_err*DISP*.c1')
    forig = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_LPAP_S07.SAC_s_2_DISP.c1'
    po,co = loadtxt(forig,usecols=(2,4),unpack=True)
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
    rep = scint.splrep(po[~errplus.mask],errplus.data[~errplus.mask])
    nn = scint.splev(po,rep)
    plot(po,nn)
    rep = scint.splrep(po[~errmin.mask],errmin.data[~errmin.mask])
    nn = scint.splev(po,rep)
    plot(po,nn)
    #plot(po,errplus)
    #plot(po,errmin)
    plot(po,co,'ko')

if 0:
    figure()
    f1 = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_S06_S13.SAC_s_2_DISP.c1'
    f2 = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_S06_S13.SAC_s_2_DISP.c1_amp.mat'

    p,u,c = loadtxt(f1,usecols=(2,3,4),unpack=True)
    a = sio.loadmat(f2,struct_as_record=False)
    contourf(a['cper'],a['ampv'],a['amps'],100)
    ax = gca()
    ax.autoscale_view(tight=True)
    plot(p,c)
    plot(p,u)
    amp,snr,wdth = loadtxt(f1,usecols=(5,6,7),unpack=True)
    #plot(p,amp,'b')
    #plot(p,snr,'r')
    plot(p,st[0].stats.sac.dist/(st[0].stats.sac.dist/u+wdth/10.),'ko')
    plot(p,st[0].stats.sac.dist/(st[0].stats.sac.dist/u-wdth/10.),'ko')



if 0:
    figure()
    f1 = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_LPAP_S07.SAC_s_2_DISP.c1'
    f2 = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_LPAP_S07.SAC_s_2_DISP.c1_amp.mat'
    f3 = '/data/wanakaII/yannik/cnipse/stack_start_cnipse/COR_LPAP_S07.SAC_s'

    p,u,c = loadtxt(f1,usecols=(2,3,4),unpack=True)
    a = sio.loadmat(f2,struct_as_record=False)
    contourf(a['cper'],a['ampv'],a['amps'],100)
    ax = gca()
    ax.autoscale_view(tight=True)
    plot(p,c)
    plot(p,u)

    amp,snr,wdth = loadtxt(f1,usecols=(5,6,7),unpack=True)
    st = read(f3)
    plot(p,st[0].stats.sac.dist/(st[0].stats.sac.dist/u+wdth/10.),'ko')
    plot(p,st[0].stats.sac.dist/(st[0].stats.sac.dist/u-wdth/10.),'ko')
