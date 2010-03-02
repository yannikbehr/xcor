#!/usr/bin/python

"""
plot 2D-inversion results and the corresponding velocity measurements
"""

from pylab import *
from gmtpy import GMT, ScaleGuru, Ax
import os
import sys
import string
import mymkcpt
import cStringIO

class PlotException(Exception): pass

def _get_range_(paths):
    """
    determine geographical coordinate limits from velocity measurement table
    """
    val = loadtxt(paths,usecols=[1,2,3,4,5])
    latmin = append(val[:,0],val[:,2]).min()
    latmax = append(val[:,0],val[:,2]).max()
    lonmin = append(val[:,1],val[:,3]).min()
    lonmax = append(val[:,1],val[:,3]).max()
    zmin = val[:,4].min()
    zmax = val[:,4].max()
    return lonmin,lonmax,latmin,latmax,zmin,zmax

def _get_extrema_(paths):
    """
    determine maximum, minimum and mean of velocity measurements
    """
    val = loadtxt(paths,usecols=[1,2,3,4,5])
    zmin = val[:,4].min()
    zmax = val[:,4].max()
    mean = val[:,4].mean()
    return zmin, zmax, mean

def _convert_result_(paths):
    """
    convert velocity measurements into a format that can be plotted with
    GMT's psxy
    """
    val = loadtxt(paths,usecols=[1,2,3,4,5])
    fstr = cStringIO.StringIO()
    for line in val:
        fstr.write("> -Z%s\n%s %s\n%s %s\n"%(line[4],line[1],line[0],line[3],line[2]))
    return fstr

def _get_2dmap_lim_(map2D):
    """
    get geographical coordinate limits from inversion result
    """
    val = loadtxt(map2D)
    lonmin = val[:,0].min()
    lonmax = val[:,0].max()
    latmin = val[:,1].min()
    latmax = val[:,1].max()
    zmin = val[:,2].min()
    zmax = val[:,2].max()
    steplon = val[1,0] - val[0,0]
    _i = 1
    while True:
        steplat = val[_i,1] - val[_i-1,1]
        if steplat > 0.0001: break
        _i += 1
    return lonmin,lonmax,latmin,latmax,zmin,zmax,steplon, steplat

def _get_scale_tick_(zmin,zmax):
    """
    Find the right increment to put 5 anotations on the scalebar.
    """
    nticks = 5
    while True:
        sb = Ax(approx_ticks = nticks)
        sb_guru = ScaleGuru([([zmin,zmin],[zmax,zmax])], axes=(sb,sb))
        vstep = sb_guru.get_params()['xinc']
        if (zmax-zmin)/vstep >= 5: break
        nticks += 1
    return vstep


def plot_result(**keys):
    """
    plot measurements and 2D maps
    """
    gmt = GMT()
    paths = keys['paths']
    if keys['map_range'] == None:
        lonmin,lonmax,latmin,latmax,zmin,zmax = _get_range_(paths)
        ### if map range not given try to guess from data
        rng = '%f/%f/%f/%f'%(lonmin,lonmax,latmin,latmax)
    else:
        lonmin,lonmax,latmin,latmax = map(float,map_range.split('/'))
        rng = map_range
    scl = 'M10c'
    scalebar = '3.c/-1.6c/6c/.2ch'
    cptfile=gmt.tempfilename('colorpalette.txt')
    mymkcpt.make_cpt((a for a in _get_extrema_(paths)),cptfile)

    ### create temporary files
    tmppath=gmt.tempfilename('paths.txt')
    fileout = keys['fileout']
    #### plot measurements
    if keys['plot_paths']:
        if keys['map2D'] != None:
            lonmin,lonmax,latmin,latmax,zmin,zmax,slon,slat = _get_2dmap_lim_(map2D)
            rng = '%f/%f/%f/%f'%(lonmin,lonmax,latmin,latmax)
        if keys['map_range'] != None:
            lonmin,lonmax,latmin,latmax = map(float,map_range.split('/'))
            rng = map_range
        lonmin1,lonmax1,latmin1,latmax1,zmin1,zmax1 = _get_range_(paths)
        axx = Ax(approx_ticks=5)
        ayy = Ax(approx_ticks=5)
        guru = ScaleGuru([([lonmin,lonmax],[latmin,latmax])], axes=(axx,ayy))
        s = guru.get_params()
        anot = 'a%ff%f/a%ff%fWSne'%(s['xinc'],s['xinc']/2.,s['yinc'],s['yinc']/2.)
        gmt.psbasemap(R=rng,J=scl,V=True,B=anot,G='white')
        gmt.pscoast(R=True,J=True,V=True,W='1/0/0/0',D='i')
        gmt.psxy(R=True,J=True,m=True,V=True,W='2',C=cptfile,in_string=_convert_result_(paths).getvalue())
        gmt.psscale(C=cptfile,V=True,D=scalebar,B='%f::/:km/s:'%_get_scale_tick_(zmin1,zmax1))

    if keys['plot_map']:
        xshift = '0c'
        if keys['plot_paths']:
            xshift = '12c'
        grdtomo = gmt.tempfilename('tomo.grd')
        grdtomotmp = gmt.tempfilename('tomo_tmp.grd')
        tomocpt = gmt.tempfilename('tomo.cpt')
        lonmin,lonmax,latmin,latmax,zmin,zmax,slon,slat = _get_2dmap_lim_(map2D)
        rng = '%f/%f/%f/%f'%(lonmin,lonmax,latmin,latmax)
        if keys['map_range'] != None:
            lonmin,lonmax,latmin,latmax = map(float,map_range.split('/'))
            rng = map_range
        gmt.xyz2grd(keys['map2D'],G=grdtomotmp,I='%f/%f'%(slon,slat),R=rng,out_discard=True)
        gmt.grdsample(grdtomotmp,G=grdtomo,I='1m',Q='l',R=True,out_discard=True)
        gmt.grd2cpt(grdtomo,E=50,L='%f/%f'%(zmin,zmax),C="seis",out_filename=tomocpt)
        gmt.grdimage(grdtomo,R=True,J=scl,P=True,C=tomocpt,X=xshift)
        gmt.pscoast(R=True,J=scl,B=anot,D='i',W='thinnest' )
        gmt.psscale(C=tomocpt,D=scalebar,B='%f::/:km/s:'%_get_scale_tick_(zmin,zmax))

    gmt.save(fileout) 
    os.system('gv '+fileout+'&')


if __name__ == '__main__':
    from ConfigParser import SafeConfigParser
    map_range = None
    plot_paths = False
    plot_map = False
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            plot_paths = cp.getboolean('plotting','plot_paths')
            plot_map = cp.getboolean('plotting','plot_map')
            fileout = cp.get('plotting','fileout')
            if plot_paths:
                pathdir = cp.get('plotting','pathdir')
                prefix = cp.get('plotting','prefix')
                period = eval(cp.get('plotting','period'))
            if plot_map:
                mapdir = cp.get('plotting','mapdir')
                prefix = cp.get('plotting','prefix')
                alpha = cp.get('plotting','alpha')
                sigma = cp.get('plotting','sigma')
                beta = cp.get('plotting','beta')
                period = eval(cp.get('plotting','period'))
                
            if cp.has_option('plotting','map_range'):
                map_range = cp.get('plotting','map_range')
            
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception,e:
        print e
        sys.exit(1)

    for _p in period:
        fout = '%s_%d.ps'%(fileout,_p)
        if plot_map:
            map2D = os.path.join(mapdir,str(_p),'%s_%s_%s'%(alpha,sigma,beta),'%s_%d.1'%(prefix,_p))
            fout = os.path.join(mapdir,str(_p),'%s_%s_%s'%(alpha,sigma,beta),'%s_%d_%s_%s.ps'%(prefix,_p,alpha,sigma))
        else:
            map2D = None
        if plot_paths:
            paths = os.path.join(pathdir,'%ss_%s.txt'%(_p,prefix))
        plot_result(paths=paths,map2D=map2D,map_range=map_range,
                    plot_paths=plot_paths,plot_map=plot_map,
                    fileout=fout)
