import os, sys, string
from pylab import *
sys.path.append(os.environ['AUTO_SRC']+'/src/modules')
import pysacio as p
import ftan

class FtanError(Exception): pass
class FtanIOError(Exception): pass

def myftan(fn, t0=0, nfin=100,npoints=3,perc=50.0,dt=1.,vmin=2.,
           vmax=4.,tmin=5,tmax=None,thresh=10,ffact=1.,taperl=1,snr=0.1,
           phm=True,steps=False,extrace=None):
    """wrapper function to set ftan parameters and call ftan modules
    1st step raw ftan; 2nd step ftan with phase-matched filtering from
    1st step prediction curve;
    set tmax to the maximum observable (still reliable) wavelength"""
    [hf,hi,hs,seis,ok] = p.ReadSacFile(fn)
    if not ok:
        raise FtanIOError('cannot read sac file')
    stat1 = string.rstrip(p.GetHvalue('kstnm',hf,hi,hs))
    stat2 = string.rstrip(p.GetHvalue('kevnm',hf,hi,hs))
    trace = zeros(32768)
    for i in range(0,len(seis)):
        if i < 32767:
            trace[i] = seis[i]
    
    n = p.GetHvalue('npts',hf,hi,hs)
    delta = p.GetHvalue('dist',hf,hi,hs)
    if tmin*vmin > delta:
        raise FtanIOError("distance between stations is too small")
    if tmax==None:
        tmax = delta/(2*vmax)
        if tmax > 35:
            tmax = 35
    if not tmax > tmin:
        raise FtanIOError("tmax has to be bigger than tmin")
            
    times = arange(int(delta/vmax),int(delta/vmin))
    vels  = [ delta/i for i in times]

    if steps == True:
        #run ftan with small frequency steps
        cper=[];aper=[];gv=[];gvamp=[];gvsnr=[];
        amps = zeros((len(vels),1))
        cper.append(0);aper.append(0);gv.append(0);gvamp.append(0);gvsnr.append(0)
        jj = 0
        errcnt = 0
        for k in arange(tmin,int(tmax),1.):
            tm = k+10.
            if tm > tmax: break
            # first ftan run to get raw dispersion curve
            nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,amp,ierr = ftan.aftan4(n,trace,t0,dt,\
                                                                          delta,vmin,vmax,k,\
                                                                          tm,thresh,ffact,perc,\
                                                                          npoints,taperl,nfin,snr)
            if nfout2 == 0 or ierr == 2 or ierr == 1:
                errcnt = errcnt +1
                if errcnt > 3:
                    raise FtanError("ERROR in ftan-method (1st step)")

            if phm:
                # second ftan run using raw dispersion curve to construct phase match filter
                snr = 120.0
                npred=nfout2
                pred = zeros((300,2))
                for i in range(0,nfout2):
                    pred[i][0] = arr2[1][i]
                    pred[i][1] = arr2[2][i]
                    
                nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,amp,ierr = ftan.aftan4i(n,trace,t0,dt,delta,vmin,vmax,\
                                                                               k,tm,thresh,ffact,perc,npoints,\
                                                                               taperl,nfin,snr,npred,pred)
                
                if nfout2 == 0 or ierr == 2 or ierr == 1:
                    errcnt = errcnt +1
                    if errcnt > 3:
                        raise FtanError("ERROR in ftan-method (2nd step)")
                else:
                    for i in range(0,nfin):
                        if arr2[0][i]>cper[jj]:
                            cper.append(arr2[0][i])
                            aper.append(arr2[1][i])
                            gv.append(arr2[2][i])
                            gvamp.append(arr2[3][i])
                            gvsnr.append(arr2[4][i])
                            amps=append(amps[0:len(vels),0:jj],amp[0:len(vels),i:nfin],axis=1)
                            jj = jj + 1
            else:
                for i in range(0,nfin):
                    if arr2[0][i]>cper[jj]:
                        cper.append(arr2[0][i])
                        aper.append(arr2[1][i])
                        gv.append(arr2[2][i])
                        gvamp.append(arr2[3][i])
                        gvsnr.append(arr2[4][i])
                        amps=append(amps[0:len(vels),0:jj],amp[0:len(vels),i:nfin],axis=1)
                        jj = jj + 1

        
        cper  = array(cper[1:])
        aper  = array(aper[1:])
        gv    = array(gv[1:])
        gvamp = array(gvamp[1:])
        gvsnr = array(gvsnr[1:])
        ampv  = array(vels)

    else:
        # first ftan run to get raw dispersion curve
        nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,amp,ierr = ftan.aftan4(n,trace,t0,dt,\
                                                                      delta,vmin,vmax,tmin,\
                                                                      tmax,thresh,ffact,perc,\
                                                                      npoints,taperl,nfin,snr)
        if nfout2 == 0 or ierr == 2 or ierr == 1:
            raise FtanError("ERROR in ftan-method (1st step)")


        if phm:
            # second ftan run using raw dispersion curve to construct phase match filter
            snr = 120.0
            npred=nfout2
            pred = zeros((300,2))
            for i in range(0,nfout2):
                pred[i][0] = arr2[1][i]
                pred[i][1] = arr2[2][i]
            if extrace:
                tr = load(extrace)
                npred = len(tr)
                pred = zeros((300,2))
                for i in range(npred):
                    pred[i][0] = tr[i][0]
                    pred[i][1] = tr[i][1]
            nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,amp,ierr = ftan.aftan4i(n,trace,t0,dt,delta,vmin,vmax,\
                                                                           tmin,tmax,thresh,ffact,perc,npoints,\
                                                                           taperl,nfin,snr,npred,pred)
                
            if nfout2 == 0 or ierr == 2 or ierr == 1:
                raise FtanError("ERROR in ftan-method (2nd step)")

        cper  = array(arr2[0][0:nrow])
        aper  = array(arr2[1][0:nrow])
        gv    = array(arr2[2][0:nrow])
        gvamp = array(arr2[3][0:nrow])
        gvsnr = array(arr2[4][0:nrow])
        ampv  = array(vels)
        amps  = amp[0:len(vels),0:nrow]
    return (cper,aper,gv,gvamp,gvsnr,ampv,amps)
