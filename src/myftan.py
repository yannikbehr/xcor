#!/usr/bin/env mypython

""" wrapper script for ftan module """

import os, sys, string, glob
sys.path.append(os.environ['AUTO_SRC']+'/src/FTAN/gv')
sys.path.append(os.environ['AUTO_SRC']+'/src/FTAN/pv')
import ftanc
import ftangv
import pysacio as p
import progressbar as pg
import scipy.io as sio
from obspy.sac import *

DEBUG=True

if __name__ == '__main__':
    from ConfigParser import SafeConfigParser
    import logging
    ############## setting defaults #########################
    fltfact = 1.
    refdsp = None
    tmin = None
    tmax = None
    writeamps = False
    ############## read config file #########################
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            cordir  = cp.get('ftan','cordir')
            tmpdir  = cp.get('ftan','tmpdir')
            spattern= cp.get('ftan','spattern')
            dsptype = cp.get('ftan','dsptype')
            explore = cp.getboolean('ftan','explore')
            writeamps = cp.getboolean('ftan','writeamps')
            if  cp.has_option('ftan','refdsp'):
                refdsp  = cp.get('ftan','refdsp')
            if dsptype == 'phase' and not cp.has_option('ftan','refdsp'):
                raise Exception("reference curve has to be given for phase-velocity measurements")
            if cp.has_option('ftan','filter_fact'):
                fltfact = cp.get('ftan','filter_fact')
            if cp.has_option('ftan','tmin'):
                tmin = float(cp.get('ftan','tmin'))
            if cp.has_option('ftan','tmax'):
                tmax = float(cp.get('ftan','tmax'))
                             
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception,e:
        print e
        sys.exit(1)
    ########## set up log-files ##############################
    DBG_FILENAME = './%s/myftan.log'%tmpdir
    ERR_FILENAME = './%s/myftan.err'%tmpdir

    mylogger = logging.getLogger('MyLogger')
    mylogger.setLevel(logging.DEBUG)
    handlerdbg = logging.FileHandler(DBG_FILENAME,'w')
    handlererr = logging.FileHandler(ERR_FILENAME,'w')
    handlererr.setLevel(logging.ERROR)

    mylogger.addHandler(handlerdbg)
    mylogger.addHandler(handlererr)
    ########### set up progress bar ############################
    widgets = ['ftan: ', pg.Percentage(), ' ', pg.Bar('#'),
               ' ', pg.ETA()]
    ############################################################

    flist = glob.glob(cordir+'/'+spattern)
    if not DEBUG:
        pbar = pg.ProgressBar(widgets=widgets, maxval=len(flist)).start()

    if dsptype == 'group':
        cnt = 0
        ### store initial value
        tmin_init = tmin
        for fn in flist:
            cnt = cnt +1
            if not DEBUG:
                pbar.update(cnt)
            else:
                print fn
            try:
                tr = ReadSac(fn)
            except SacIOError:
                print "file %s can't be read"%fn
                continue
            except SacError:
                print "file %s not a valid sac-file"%fn
                continue
            outfile = '%s_2_DISP.1'%fn
            if explore:
                if tmin == None:
                    tmin = 2.
                while True:
                    try:
                        cper,aper,gv,gvamp,gvsnr,ampv,amps = ftangv.myftan(tr,tmin=tmin,ffact=fltfact,
                                                                           extrace=refdsp,tmaxmax=30,phm=True)
                    except ftangv.FtanError:
                        tmin += 1.
                    except ftangv.FtanIOError:
                        ### reset tmin to initial value
                        tmin = tmin_init
                        break
                    else:
                        tmin = tmin_init
                        break
            else:
                try:
                    cper,aper,gv,gvamp,gvsnr,ampv,amps = ftangv.myftan(tr,ffact=fltfact,extrace=refdsp)
                except ftangv.FtanError:
                    try:
                        outfile = '%s_2_DISP.2'%fn
                        cper,aper,gv,gvamp,gvsnr,ampv,amps = ftangv.myftan(tr,ffact=0.5,extrace=refdsp)
                    except ftangv.FtanError:
                        try:
                            outfile = '%s_2_DISP.3'%fn
                            cper,aper,gv,gvamp,gvsnr,ampv,amps = ftangv.myftan(tr,steps=True,phm=False)
                        except ftangv.FtanError, e:
                            mylogger.error('%s: %s'%(fn,e))
                            continue
    
            mylogger.debug('%s'%fn)
            if not locals().has_key('aper'):
                continue
            if (aper[-1]-aper[0]) > 2.:
                f = open(outfile,'w')
                for ii in range(0,len(cper)):
                    print >>f,'%d\t%f\t%f\t%f\t%f\t%f'%(ii,cper[ii],aper[ii],gv[ii],gvamp[ii],gvsnr[ii])
                f.close()
                if writeamps:
                    sio.savemat(outfile+'_amp.mat',{'cper':cper,'ampv':ampv,'amps':amps})

        if not DEBUG:
            pbar.finish()


    if dsptype == 'phase':
        cnt = 0
        tmin_init = tmin
        for fn in flist:
            cnt = cnt + 1
            if not DEBUG:
                pbar.update(cnt)
            else:
                print fn
            try:
                tr = ReadSac(fn)
            except SacIOError:
                print "file %s can't be read"%fn
                continue
            except SacError:
                print "file %s not a valid sac-file"%fn
                continue
            outfile='%s_2_DISP.c1'%fn
            if explore:
                if tmin == None:
                    tmin = 2.
                while True:
                    try:
                        cper,aper,gv,pv,gvamp,gvsnr,ampv,amps,refper,refvel = ftanc.myftan(tr,refdsp,tmin=tmin,tmax=tmax,ffact=fltfact,vmin=1.0)
                    except ftanc.FtanError:
                        tmin += 1.0
                    except ftanc.FtanIOError:
                        tmin = tmin_init
                        break
                    else:
                        tmin = tmin_init
                        break
            else:
                try:
                    cper,aper,gv,pv,gvamp,gvsnr,ampv,amps,refper,refvel = ftanc.myftan(tr,refdsp,ffact=fltfact)
                except ftanc.FtanIOError,e:
                    mylogger.error('%s: %s'%(fn,e))
                    continue
                except ftanc.FtanError:
                    try:
                        outfile = '%s_2_DISP.c2'%fn
                        cper,aper,gv,pv,gvamp,gvsnr,ampv,amps,refper,refvel = ftanc.myftan(tr,refdsp,tmin=8,tmax=35,ffact=fltfact)
                    except ftanc.FtanError:
                        try:
                            outfile = '%s_2_DISP.c3'%fn
                            cper,aper,gv,pv,gvamp,gvsnr,ampv,amps,refper,refvel = ftanc.myftan(tr,refdsp,tmin=12,tmax=35,ffact=fltfact)
                        except ftanc.FtanError,e:
                            mylogger.error('%s: %s'%(fn,e))
                            continue

            mylogger.debug('%s'%fn)
            if not locals().has_key('aper'):
                continue
            if (aper[-1]-aper[0]) > 2.:
                f = open(outfile,'w')
                for ii in range(0,len(cper)):
                    print >>f,'%d\t%f\t%f\t%f\t%f\t%f\t%f'%(ii,cper[ii],aper[ii],gv[ii],pv[ii],gvamp[ii],gvsnr[ii])
                f.close()
                if writeamps:
                    sio.savemat(outfile+'_amp.mat',{'cper':cper,'ampv':ampv,'amps':amps})
        if not DEBUG:
            pbar.finish()
                
            
