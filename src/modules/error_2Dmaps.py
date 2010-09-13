#!/usr/bin/env mypython
"""
Evaluate error of minimum and maximum surface wave maps.
"""

import glob
from pylab import *
from gmtpy import GMT, ScaleGuru, Ax
from plot_2D import _get_2dmap_lim_, _get_scale_tick_
import mymkcpt

#def _get_2dmap_lim_(lon,lat,v):
#    """
#    get geographical coordinate limits from inversion result
#    """
#    lonmin = lon.min()
#    lonmax = lon.max()
#    latmin = lat.min()
#    latmax = lat.max()
#    zmin = v.min()
#    zmax = v.max()
#    zmean = v.mean()
#    steplon = lon[1] - lon[0]
#    _i = 1
#    while True:
#        steplat = lat[_i] - lat[_i-1]
#        if steplat > 0.0001: break
#        _i += 1
#    return lonmin,lonmax,latmin,latmax,zmin,zmax,zmean,steplon, steplat
def _get_scale_tick_(zmin,zmax):
    """
    Find the right increment to put 5 anotations on the scalebar.
    """
    nticks = 2
    while True:
        sb = Ax(approx_ticks = nticks)
        sb_guru = ScaleGuru([([zmin,zmin],[zmax,zmax])], axes=(sb,sb))
        vstep = sb_guru.get_params()['xinc']
        if (zmax-zmin)/vstep >= 2: break
        nticks += 1
    return vstep

periods = range(3,26)
#periods = range(8,9)
periods = range(3,13)

mapdirmax = '/data/wanakaII/yannik/cnipse/inversion/group_maps_max/zz/'
mapdirmin = '/data/wanakaII/yannik/cnipse/inversion/group_maps_min/zz/'
mapdirerr = '/data/wanakaII/yannik/cnipse/inversion/group_maps_error/zz/'
mapdirmax = '/data/wanakaII/yannik/cnipse/inversion/group_maps_max/tt/'
mapdirmin = '/data/wanakaII/yannik/cnipse/inversion/group_maps_min/tt/'
mapdirerr = '/data/wanakaII/yannik/cnipse/inversion/group_maps_error/tt/'
mapdirmax = '/data/wanakaII/yannik/cnipse/inversion/phase_maps_max/tt/'
mapdirmin = '/data/wanakaII/yannik/cnipse/inversion/phase_maps_min/tt/'
mapdirerr = '/data/wanakaII/yannik/cnipse/inversion/phase_maps_error/tt/'
if not os.path.isdir(mapdirerr):
    os.makedirs(mapdirerr)
alpha = 200
sigma = 200
beta = 1
prefix = '2lambda_5'
for _p in periods:
    map2Dmax = os.path.join(mapdirmax,str(_p),'%s_%s_%s'%(alpha,sigma,beta),'%s_max_%d.1'%(prefix,_p))
    if not os.path.isfile(map2Dmax):continue
    map2Dmin = os.path.join(mapdirmin,str(_p),'%s_%s_%s'%(alpha,sigma,beta),'%s_min_%d.1'%(prefix,_p))
    if not os.path.isfile(map2Dmin):continue

    lon,lat,vmax = loadtxt(map2Dmax,unpack=True)
    vmin = loadtxt(map2Dmin,usecols=(2,))
    err = abs((vmax-vmin))/2.
    gmt = GMT()
    scl = 'M10c'
    scalebar = '3.c/-1.6c/6c/.2ch'
    xshift = '2c'
    grdxyz = map2Dmax.replace(mapdirmax,mapdirerr)
    grdxyz = grdxyz.replace('_max_','_err_')
    dirn = os.path.dirname(grdxyz)
    if not os.path.isdir(dirn):
        os.makedirs(dirn)
    grdtomo = gmt.tempfilename('tomo.grd')
    grdtomotmp = gmt.tempfilename('tomo_tmp.grd')
    tomocpt = gmt.tempfilename('tomo.cpt')
    savetxt(grdxyz,vstack(((lon,lat),err)).T)
    lonmin,lonmax,latmin,latmax,zmin,zmax,zmean,slon,slat = _get_2dmap_lim_(grdxyz)
    rng = '174.5/178.6/-40/-37.'
    #rng = '%f/%f/%f/%f'%(lonmin,lonmax,latmin,latmax)
    axx = Ax(approx_ticks=5)
    ayy = Ax(approx_ticks=5)
    guru = ScaleGuru([([lonmin,lonmax],[latmin,latmax])], axes=(axx,ayy))
    s = guru.get_params()
    anot = 'a%ff%f/a%ff%fWSne'%(s['xinc'],s['xinc']/2.,s['yinc'],s['yinc']/2.)
    gmt.xyz2grd(grdxyz,G=grdtomotmp,I='%f/%f'%(slon,slat),R=rng,out_discard=True)
    gmt.grdsample(grdtomotmp,G=grdtomo,I='1m',Q='l',R=True,out_discard=True)
    #gmt.grd2cpt(grdtomo,E=50,L='%f/%f'%(zmin,zmax),C="polar",out_filename=tomocpt)
    mymkcpt.make_cpt((zmin,zmax,zmean),tomocpt)
    gmt.grdimage(grdtomo,R=True,J=scl,P=True,C=tomocpt,X=xshift)
    gmt.pscoast(R=True,J=scl,B=anot,D='i',W='thinnest' )
    gmt.psscale(C=tomocpt,D=scalebar,B='%f::/:km/s:'%_get_scale_tick_(zmin,zmax))
    textstring = "177.5 -36.8 18 0 1 CT T = %d s"%_p
    gmt.pstext(R=True,J=True,D='j0.5',G='0/0/0',N=True,in_string=textstring)
    fileout = grdxyz.replace('.1','_%d_%d.pdf'%(alpha,sigma))
    gmt.save(fileout)
    os.system('gv %s&'%fileout)

