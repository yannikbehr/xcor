#!/usr/bin/env mypython
""" run ftan on radial component; needs pi/4 phase shift """

import os, sys, string, glob
sys.path.append(os.environ['AUTO_SRC']+'/src/FTAN/gv')
sys.path.append(os.environ['AUTO_SRC']+'/src/FTAN/pv')
import ftanc
import ftangv
import pysacio as p
import progressbar as pg
from pylab import *
from obspy.sac import *

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
            cordir     = cp.get('ftanradial','cordir')
            spattern = cp.get('ftanradial','spattern')
            npattern = cp.get('ftanradial','npattern')
            refdsp   = cp.get('ftanradial','refdsp')
            explore = cp.getboolean('ftanradial','explore')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception,e:
        print e
        sys.exit(1)
    flist = glob.glob(os.path.join(cordir,'*'+spattern))
    for xfile in flist:
        print xfile
        x  = ReadSac(xfile)
        X  = rfft(x.seis)
        NX = multiply(X,exp(-1j*pi/4.))
        y  = irfft(NX)
        x.seis = y
        x.WriteSacBinary(xfile+'_tmp')
        if explore:
            tmin = 2.
            aper = None
            while True:
                try:
                    cper,aper,gv,pv,gvamp,gvsnr,ampv,amps,refper,refvel = ftanc.myftan(xfile+'_tmp',refdsp,tmin=tmin,ffact=fltfact)
                except ftanc.FtanError:
                    tmin += 1.0
                except ftanc.FtanIOError,e:
                    print e
                    break
                else:
                    break
            if aper == None: continue
            nname = xfile+npattern
            print "writing %s"%nname
            f = open(nname,'w')
            for ii in range(0,len(cper)):
                print >>f,'%d\t%f\t%f\t%f\t%f\t%f\t%f'%(ii,cper[ii],aper[ii],gv[ii],pv[ii],gvamp[ii],gvsnr[ii])
            f.close()
            if os.path.isfile(xfile+'_tmp'):
                os.remove(xfile+'_tmp')
