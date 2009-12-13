#!/usr/bin/env mypython

""" run 2nd iteration of ftan with prediction curves from overdamped maps """

import os, sys, string, glob
sys.path.append(os.environ['AUTO_SRC']+'/src/FTAN/gv')
sys.path.append(os.environ['AUTO_SRC']+'/src/FTAN/pv')
import ftanc
import ftangv
import pysacio as p
import progressbar as pg
from pylab import *

if __name__ == '__main__':
    from ConfigParser import SafeConfigParser
    import logging
    ############## setting defaults #########################
    fltfact = 1.
    ############## read config file #########################
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            dispdir  = cp.get('2ndftan','dispdir')
            xdir     = cp.get('2ndftan','xdir')
            spattern = cp.get('2ndftan','spattern')
            npattern = cp.get('2ndftan','npattern')
            pcurves  = cp.get('2ndftan','pcurves')
            explore = cp.getboolean('2ndftan','explore')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception,e:
        print e
        sys.exit(1)
    flist = glob.glob(os.path.join(dispdir,'*'+spattern))
    for _f in flist:
        print _f
        stat1 = os.path.basename(_f).split(".SAC")[0].split('_')[1]
        stat2 = os.path.basename(_f).split(".SAC")[0].split('_')[2]
        pname = os.path.join(pcurves,'%s_%s.PRED'%(stat1,stat2))
        if not os.path.isfile(pname):
            pname = os.path.join(pcurves,'%s_%s.PRED'%(stat2,stat1))
            if not os.path.isfile(pname):
                print "no prediction curve for %s"%_f
                continue
        x,y=load(pname,unpack=True)
        try:
            if len(x)<4:
                print "prediction curve too short"
                continue
        except:
            continue
        xfile = os.path.join(xdir,os.path.basename(_f).split(spattern)[0])
        if not os.path.isfile(xfile):
            print "cannot find %s"%xfile
            continue
        if explore:
            tmin = 2.
            aper = None
            while True:
                try:
                    cper,aper,gv,pv,gvamp,gvsnr,ampv,amps,refper,refvel = ftanc.myftan(xfile,pname,tmin=tmin,ffact=fltfact)
                except ftanc.FtanError:
                    tmin += 1.0
                except ftanc.FtanIOError,e:
                    print e
                    break
                else:
                    break
            if aper == None: continue
            nname = _f.split(spattern)[0]+npattern
            print "writing %s"%nname
            f = open(nname,'w')
            for ii in range(0,len(cper)):
                print >>f,'%d\t%f\t%f\t%f\t%f\t%f\t%f'%(ii,cper[ii],aper[ii],gv[ii],pv[ii],gvamp[ii],gvsnr[ii])
            f.close()
