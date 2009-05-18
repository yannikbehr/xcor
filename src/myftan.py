#!/usr/bin/python

""" wrapper script for ftan module """


from pylab import *
import os, sys, string, glob
sys.path.append('./modules')
sys.path.append('./FTAN/gv')
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
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "no configuration file found"
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

    flist = glob.glob(cordir+'/COR*.SAC*_s')
    pbar = pg.ProgressBar(widgets=widgets, maxval=len(flist)).start()
    cnt = 0
    for fn in flist:
        cnt = cnt +1
        pbar.update(cnt)
        outfile = '%s_2_DISP.1'%fn
        try:
            cper,aper,gv,gvamp,gvsnr,ampv,amps = myftan(fn)
        except:
            try:
                outfile = '%s_2_DISP.2'%fn
                cper,aper,gv,gvamp,gvsnr,ampv,amps = myftan(fn,ffact=0.5)
            except:
                try:
                    outfile = '%s_2_DISP.3'%fn
                    cper,aper,gv,gvamp,gvsnr,ampv,amps = myftan(fn,steps=True,phm=False)
                except Exception, e:
                    mylogger.error('%s: %s'%(fn,e))
                    continue

        mylogger.debug('%s'%fn)
        f = open(outfile,'w')
        for ii in range(0,len(cper)):
            print >>f,'%d\t%f\t%f\t%f\t%f\t%f'%(ii,cper[ii],aper[ii],gv[ii],gvamp[ii],gvsnr[ii])
        f.close()
    pbar.finish()

