#!/usr/local/bin/python

""" wrapper script for ftan module """


from pylab import *
import os, sys, string, glob
sys.path.append(os.environ['AUTO_SRC']+'/src/FTAN/gv')
sys.path.append(os.environ['AUTO_SRC']+'/src/FTAN/pv')
import ftanc
import ftangv
import pysacio as p
import progressbar as pg

if __name__ == '__main__':
    from ConfigParser import SafeConfigParser
    import logging
    ############## read config file #########################
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            cordir  = cp.get('ftan','cordir')
            tmpdir  = cp.get('ftan','tmpdir')
            dsptype = cp.get('ftan','dsptype')
            refdsp  = cp.get('ftan','refdsp')
            spattern= cp.get('ftan','spattern')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "no configuration file found"
        sys.exit(1)
    ########## set up log-files ##############################
    DBG_FILENAME = './%s/myftan.log'%tmpdir
    ERR_FILENAME = './%s/myftan.err'%tmpdir
    print dsptype

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
    pbar = pg.ProgressBar(widgets=widgets, maxval=len(flist)).start()

    if dsptype == 'group':
        cnt = 0
        for fn in flist:
            cnt = cnt +1
            pbar.update(cnt)
            outfile = '%s_2_DISP.1'%fn
            try:
                cper,aper,gv,gvamp,gvsnr,ampv,amps = ftangv.myftan(fn,extrace=refdsp)
            except:
                try:
                    outfile = '%s_2_DISP.2'%fn
                    cper,aper,gv,gvamp,gvsnr,ampv,amps = ftangv.myftan(fn,ffact=0.5,extrace=refdsp)
                except:
                    try:
                        outfile = '%s_2_DISP.3'%fn
                        cper,aper,gv,gvamp,gvsnr,ampv,amps = ftangv.myftan(fn,steps=True,phm=False)
                    except Exception, e:
                        mylogger.error('%s: %s'%(fn,e))
                        continue
    
            mylogger.debug('%s'%fn)
            f = open(outfile,'w')
            for ii in range(0,len(cper)):
                print >>f,'%d\t%f\t%f\t%f\t%f\t%f'%(ii,cper[ii],aper[ii],gv[ii],gvamp[ii],gvsnr[ii])
            f.close()
        pbar.finish()


    if dsptype == 'phase':
        cnt = 0
        for fn in flist:
            cnt = cnt + 1
            pbar.update(cnt)
            outfile='%s_2_DISP.c'%fn
            try:
                cper,aper,gv,pv,gvamp,gvsnr,ampv,amps,refper,refvel = ftanc.myftan(fn,refdsp)
            except:
                mylogger.error('%s: %s'%(fn,e))
                continue

            mylogger.debug('%s'%fn)
            f = open(outfile,'w')
            for ii in range(0,len(cper)):
                print >>f,'%d\t%f\t%f\t%f\t%f\t%f\t%f'%(ii,cper[ii],aper[ii],gv[ii],pv[ii],gvamp[ii],gvsnr[ii])
            f.close()
        pbar.finish()
                
            
