#!/usr/bin/env mypython


"""driver for ftan method to measure phase-velocities"""
import os, sys, string, glob
sys.path.append(os.environ['AUTO_SRC']+'/src/modules')
from obspy.sac import *
from numpy import *
import ftanpv

class FtanError(Exception): pass
class FtanIOError(Exception): pass

def myftan(tr,ref,t0=0,nfin=32,npoints=10,perc=50.0,vmin=1.,
           vmax=4.5,tmin=5,tmax=None,thresh=20,ffact=1.,taperl=.5,snr=0.2,
           fmatch=2,piover4=-1,phm=True,steps=False,extrace=None,level='strict'):

    stat1 = tr.kstnm.rstrip()
    stat2 = tr.kevnm.rstrip()
    dt = tr.delta
    n = tr.npts
    delta = tr.dist
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
    for i in range(0,min(len(tr.seis),32767)):
        trace[i] = tr.seis[i]
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
    if level == 'strict':
        if ierr == 2 or ierr == 1 or nfout2 == 0:
            raise FtanError("ERROR in ftan-method (1st step): nfout=%d ierr=%d "%(nfout2,ierr))
    if level == 'easy':
        if ierr == 2 or nfout2 == 0:
            raise FtanError("ERROR in ftan-method (1st step): nfout=%d ierr=%d "%(nfout2,ierr))
           

    if phm:
        pred = zeros((300,2))
        for i in range(0,nfout2):
            pred[i][0] = arr2[1][i]
            pred[i][1] = arr2[2][i]
    
        ffact = ffact
        fmatch = fmatch
        npred  = nfout2
        tmin = arr2[1][0];
        tmax = arr2[1][nfout2-1];
        amp   = []
        arr1  = []
        arr2  = []
        if extrace:
            tr = loadtxt(extrace)
            npred = len(tr)
            pred = zeros((300,2))
            for i in range(npred):
                pred[i][0] = tr[i][0]
                pred[i][1] = tr[i][1]

        nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,amp,ierr = ftanpv.aftanipg(piover4,n,trace,t0,dt,
                                                                          delta,vmin,vmax,tmin,
                                                                          tmax,thresh,ffact,perc,
                                                                          npoints,taperl,nfin,
                                                                          snr,fmatch,npred,pred,
                                                                          nphpr,phprper,phprvel)
    
        if level == 'strict':
            if ierr == 2 or ierr == 1 or nfout2 == 0:
                raise FtanError("ERROR in ftan-method (1st step): nfout=%d ierr=%d "%(nfout2,ierr))
        if level == 'easy':
            if ierr == 2 or nfout2 == 0:
                raise FtanError("ERROR in ftan-method (2nd step): nfout=%d ierr=%d "%(nfout2,ierr))

    cper  = array(arr2[0][0:nfout2])
    aper  = array(arr2[1][0:nfout2])
    gv    = array(arr2[2][0:nfout2])
    pv    = array(arr2[3][0:nfout2])
    gvamp = array(arr2[4][0:nfout2])
    gvsnr = array(arr2[5][0:nfout2])
    gvwdth = array(arr2[6][0:nfout2])
    ampv  = array(vels)
    amps  = amp[0:len(vels),0:nrow]
    return (cper,aper,gv,pv,gvamp,gvsnr,gvwdth,ampv,amps,phprper,phprvel[i])


if __name__=='__main__':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    reffn = './scalifornia_avg_phvel.dat'
    fn = './COR_GSC_R06C.SAC_s'
    tr = SacIO(fn)
    cper,aper,gv,pv,gvamp,gvsnr,gvwdth,ampv,amps,refper,refvel = myftan(tr,reffn)
    plt.plot(aper,pv,'k')
    plt.plot(aper,gv,'b--')
    plt.contourf(aper,ampv,amps,250)
    plt.xlabel('Period [s]')
    plt.ylabel('Phase velocity [km/s]')
    ax = plt.gca()
    ax.autoscale_view(tight=True)
    xmin, xmax = plt.xlim()
    ymin, ymax = plt.ylim()
    ############## result from fanchi's code 1st FTAN run ######
    cmpdsp = loadtxt('./COR_GSC_R06C.SAC_s_2_DISP.1')
    plt.plot(cmpdsp[:,2],cmpdsp[:,3],'k+')
    plt.xlim([xmin,xmax])
    plt.ylim(ymin,ymax)
    plt.savefig('test.png')
