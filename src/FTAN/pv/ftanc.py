#!/usr/bin/env mypython


"""driver for ftan method to measure phase-velocities"""
import os, sys, string, glob
sys.path.append(os.environ['AUTO_SRC']+'/src/modules')
import pysacio as p
from numpy import *
from pylab import *
import ftanpv

class FtanError(Exception): pass
class FtanIOError(Exception): pass

def myftan(fn,ref,t0=0,nfin=32,npoints=10,perc=50.0,vmin=1.5,
           vmax=4.5,tmin=5,tmax=None,thresh=20,ffact=1.,taperl=.5,snr=0.2,
           fmatch=2,piover4=-1,phm=True,steps=False):

    [hf,hi,hs,seis,ok] = p.ReadSacFile(fn)
    stat1 = string.rstrip(p.GetHvalue('kstnm',hf,hi,hs))
    stat2 = string.rstrip(p.GetHvalue('kevnm',hf,hi,hs))
    dt = p.GetHvalue('delta',hf,hi,hs)
    n = p.GetHvalue('npts',hf,hi,hs)
    delta = p.GetHvalue('dist',hf,hi,hs)
    if tmin*vmin > delta:
        raise FtanIOError("distance between stations is too small")
    if delta/vmax < 1.:
        raise FtanIOError("distance between stations is too small")
    times = [x*dt for x in xrange(int(delta/vmax/dt)-1,int(delta/vmin/dt))]
    #times = arange(int(delta/vmax),int(delta/vmin))
    vels  = [ delta/i for i in times]
    if tmax==None:
        tmax = delta/(2*vmax)
        if tmax > 35:
            tmax = 35
    if not tmax > tmin:
        raise FtanIOError("tmax has to be bigger than tmin")
    trace = zeros(32768)
    for i in range(0,len(seis)):
        if i < 32767:
            trace[i] = seis[i]
    reftr = loadtxt(ref)
    phprper = zeros(300)
    phprvel = zeros(300)
    nphpr = len(reftr[:,1])
    for i in range(0,nphpr):
        phprper[i] = reftr[i,0]
        phprvel[i] = reftr[i,1]
    
    nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,amp,ierr = ftanpv.aftanpg(piover4,n,trace,t0,dt,
                                                                     delta,vmin,vmax,tmin,
                                                                     tmax,thresh,ffact,perc,
                                                                     npoints,taperl,nfin,snr,
                                                                     nphpr,phprper,phprvel)
            
    if ierr == 2 or ierr == 1 or nfout2 == 2:
        raise FtanError("ERROR in ftan-method (1st step)")

    if phm:
        pred = zeros((300,2))
        for i in range(0,nfout2):
            pred[i][0] = arr2[1][i]
            pred[i][1] = arr2[2][i]
    
        ffact = 2.0
        fmatch = 2.0
        npred  = nfout2
        tmin = arr2[1][0];
        tmax = arr2[1][nfout2-1];
        amp   = []
        arr1  = []
        arr2  = []
        
        nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,amp,ierr = ftanpv.aftanipg(piover4,n,trace,t0,dt,
                                                                          delta,vmin,vmax,tmin,
                                                                          tmax,thresh,ffact,perc,
                                                                          npoints,taperl,nfin,
                                                                          snr,fmatch,npred,pred,
                                                                          nphpr,phprper,phprvel)
    
        if ierr == 2 or ierr == 1 or nfout2 == 2:
            raise FtanError("ERROR in ftan-method (2nd step)")

    cper  = array(arr2[0][0:nrow])
    aper  = array(arr2[1][0:nrow])
    gv    = array(arr2[2][0:nrow])
    pv    = array(arr2[3][0:nrow])
    gvamp = array(arr2[4][0:nrow])
    gvsnr = array(arr2[5][0:nrow])
    ampv  = array(vels)
    amps  = amp[0:len(vels),0:nrow]
    return (cper,aper,gv,pv,gvamp,gvsnr,ampv,amps,phprper,phprvel[i])


if __name__=='__main__':
    reffn = './scalifornia_avg_phvel.dat'
    fn = './COR_GSC_R06C.SAC_s'
    cper,aper,gv,pv,gvamp,gvsnr,ampv,amps,refper,refvel = myftan(fn,reffn)
    plot(aper,pv,'k')
    plot(aper,gv,'b--')
    contourf(aper,ampv,amps,250)
    xlabel('Period [s]')
    ylabel('Phase velocity [km/s]')
    ax = gca()
    ax.autoscale_view(tight=True)
    xmin, xmax = xlim()
    ymin, ymax = ylim()
    ############## result from fanchi's code 1st FTAN run ######
    cmpdsp = loadtxt('./COR_GSC_R06C.SAC_s_2_DISP.1')
    plot(cmpdsp[:,2],cmpdsp[:,3],'k+')
    xlim([xmin,xmax])
    ylim(ymin,ymax)
    show()
