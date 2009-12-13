#!/usr/bin/env mypython

"""construct prediction curves from 2D inversion results"""

import os, os.path, sys, glob
from numpy import *
from ConfigParser import SafeConfigParser
import progressbar as pg

def mkfilenames(fn,fh,rawfn,outdir):
    f  = open(rawfn,'r')
    for line in f.readlines():
        a = line.split()
        stat1 = a[8]
        stat2 = a[9]
        key   = stat2+'_'+stat1
        newfn = '%s/%s_%s.PRED'%(outdir,stat2,stat1)
        if not os.path.isfile(newfn):
            fh[key] = (open(newfn,'w'))
    return fh
    
def construct(fn, fh, rawfn):
    f0  = open(fn,'r')
    f1  = open(rawfn,'r')
    while True:
        l0 = f0.readline()
        l1 = f1.readline()
        if not l0: break
        if not l1: break
        a0 = l0.split()
        a1 = l1.split()
        stat1 = a1[8]
        stat2 = a1[9]
        key = stat2+'_'+stat1
        delta = float(a0[9])*pi*6372./180.
        t1    = delta/float(a0[5])
        t2    = t1 - float(a0[7])
        vnew  = delta/t2
        print >>fh[key],a0[0],vnew
    

if __name__ == '__main__':
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        config = 'config.txt' 

    if not os.path.isfile(config):
        print "no config file found"
        sys.exit(1)
        
    cnf = SafeConfigParser()
    cnf.read(config)
    periods = eval(cnf.get('predcurve','periods'))
    name    = cnf.get('predcurve','name')
    datdir  = cnf.get('predcurve','datdir')
    invdir  = cnf.get('predcurve','invdir')
    alpha   = int(cnf.get('predcurve','alpha'))
    beta    = int(cnf.get('predcurve','beta'))
    sigma   = int(cnf.get('predcurve','sigma'))
    outdir  = cnf.get('predcurve','outdir')
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    fh = {}
    for _p in periods:
        fn    = glob.glob('%s/%d/%d_%d_%d/*%s.resid'%(invdir,_p,alpha,sigma,beta,_p))[0]
        rawfn = os.path.join(datdir,'%ds_%s.txt'%(_p,name))
        fh = mkfilenames(fn,fh,rawfn,outdir)
        construct(fn,fh,rawfn)
