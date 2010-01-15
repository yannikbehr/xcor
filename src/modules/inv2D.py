#!/usr/bin/env mypython

""" run inversion code on VUW machine as my laptop
can't allocate enough memory to run it"""

import sys, math, os, glob, time, string
from os.path import basename, isdir, isfile,join
import tempfile, shutil
from ConfigParser import SafeConfigParser
from subprocess import *
from numpy import *

class Inv2D:

    def __init__(self,cnf):
        self.wd       = tempfile.mkdtemp()
        self.datadir   = cnf.get('2Dmap','datadir')
        self.ctrf      = cnf.get('2Dmap','ctrfile')
        ### read contour file
        f1 = open(self.ctrf).readlines()
        no = int(f1[1].split()[0])
        coord = []
        for _i in range(no):
            coord.append(map(float,f1[_i+2].split()))
        coord = array(coord)
        self.latmin = coord[:,1].min()
        self.latmax = coord[:,1].max()
        self.lonmin = coord[:,0].min()
        self.lonmax = coord[:,0].max()
        self.gridx = 0.25
        self.gridy = 0.25
        self.period    = eval(cnf.get('2Dmap','period'))
        self.name      = cnf.get('2Dmap','name')
        self.beta      = int(cnf.get('2Dmap','beta'))
        self.alpha     = int(cnf.get('2Dmap','alpha'))
        self.sigma     = int(cnf.get('2Dmap','sigma'))
        self.param     = ['me','4','5',str(self.beta),'6',str(self.alpha),
                          str(self.sigma),str(self.sigma),'7','%f %f %f'%(self.latmin,self.latmax,self.gridx),
                          '8','%f %f %f'%(self.lonmin,self.lonmax,self.gridy),'12','.1','.5','16',
                          '19','q','v','go']
        self.result    = cnf.get('2Dmap','result')
        self.tomobin   = cnf.get('2Dmap','tomobin')
        self.tomoray   = cnf.get('2Dmap','tomoray')
        shutil.copy(self.ctrf,self.wd)
        self.ctrf = basename(self.ctrf)
        os.chdir(self.wd)


    def __call__(self):
        for _p in self.period:
            self.run_inv2D(_p)
            self.copy_res(_p)


    def run_inv2D(self,period,ray=False):
        """ function to run 2D inversion that can be called to test several
        different inversion parameters """
        ############## generate script to be run on the remote machine ####
        datafile = os.path.join(self.datadir,'%ds_%s.txt'%(period,self.name))
        if ray:
            p = Popen('%s %s %s %d'\
                      %(self.tomoray,datafile,self.name,period),shell=True,stdin=PIPE)
            f = p.stdin
            for _pm in self.param:
                print >>f,_pm
            f.close()
            p.wait()
            
        else:
            p = Popen('%s %s %s %d '\
                      %(self.tomobin,datafile,self.name,period),shell=True,stdin=PIPE)
            f = p.stdin
            for _pm in self.param:
                print >>f,_pm
            f.close()
            p.wait()


    def copy_res(self,p):
        fl = glob.glob(os.path.join(self.wd,"%s_%d*"%(self.name,p)))
        resdir = os.path.join(self.result,str(p),'%d_%d_%d'%(self.alpha,self.sigma,self.beta))
        if not os.path.isdir(resdir):
            os.makedirs(resdir)
        for _f in fl:
            shutil.copy2(_f,resdir)


if __name__ == '__main__':
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "no configuration file found"
        sys.exit(1)
    t = Inv2D(cp)()
