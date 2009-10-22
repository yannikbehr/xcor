#!/usr/local/bin/python

"""
do 1bit normalization + spectral whitening
"""

import os, os.path, string, shutil, glob, sys
import subprocess as sp
from ConfigParser import SafeConfigParser
from obspy.sac import *
from numpy import *
import sac_db
import progressbar as pg


class DoWhiten:
    """class that comprises routines for performing filtering\n
    and spectral whitening"""

    def __init__(self,sdbf):
        self.sdb = sac_db.read_db(sdbf)
        self.widgets = ['1bit: ', pg.Percentage(), ' ', pg.Bar('#'),
                        ' ', pg.ETA()]
        self.pbar = pg.ProgressBar(widgets=self.widgets, maxval=self.sdb.nev).start()

    def __call__(self):
        for _nev in xrange(self.sdb.nev):
            self.pbar.update(_nev)
            for _nst in xrange(self.sdb.nst):
                if not os.path.isfile(self.sdb.rec[_nev][_nst].ft_fname):continue
                self.onebit(self.sdb.rec[_nev][_nst].ft_fname)
        self.pbar.finish()


    def onebit(self,fn):
        #print fn
        x = ReadSac(fn)
        x.seis = sign(x.seis)
        dn = os.path.dirname(os.path.dirname(fn))
        dn1 = os.path.join(dn,'broadband',os.path.basename(os.path.dirname(fn)))
        if not os.path.isdir(dn1):
            os.makedirs(dn1)
        nf = os.path.join(dn1,os.path.basename(fn))
        x.WriteSacBinary(nf)



if __name__ == '__main__':

    try:
        sdbf = sys.argv[1]
    except:
        print "usage: %s sac_db file"%(os.path.basename(sys.argv[0]))
        sys.exit(1)
                
    t = DoWhiten(sdbf)
    t()
