#!/usr/local/bin/python

"""extract information from dispersion curves, read traces and
find auxiliary files"""

import os, os.path, sys, glob
from pylab import *
import obspy.sac as sac

class DispError(Exception):
    pass

class ReadDisp:
    def __init__(self,fname,**keys):
        self.name = fname
        self.type = None
        self.read()
        self.get_stat()
        if keys.has_key('dirs'):
            self.dirs = keys['dirs']
        else:
            self.dirs = {}


    def read(self):
        self.trace = load(self.name)
        rows,cols = self.trace.shape
        if cols == 6:
            self.type = 'group'
        if cols == 7:
            self.type = 'phase'
            

    def get_stat(self):
        a = os.path.basename(self.name).split('.SAC')
        b = a[0].split('_')
        self.st1 = b[1]
        self.st2 = b[2]


    def find_aux(self):
        """convenience function to find SAC file and other useful
        files in connection with dispersion curve files"""
        pcurve = xcurve = d2curve = 'dummy'
        ### find prediction curve
        if self.dirs.has_key('pdir'):
            pcurve = os.path.join(self.dirs['pdir'],
                                  '%s_%s.PRED'%(self.st1,self.st2))
            if not os.path.isfile(pcurve):
                pcurve = os.path.join(self.dirs['pdir'],
                                      '%s_%s.PRED'%(self.st2,self.st1))
        if not os.path.isfile(pcurve):
            pcurve = os.path.join(os.path.dirname(self.name),
                                  '%s_%s.PRED'%(self.st1,self.st2))
            if not os.path.isfile(pcurve):
                pcurve = os.path.join(os.path.dirname(self.name),
                                      '%s_%s.PRED'%(self.st2,self.st1))
        if os.path.isfile(pcurve):
            self.ptrace = load(pcurve)
            if self.ptrace.shape == (2,):
                self.ptrace.shape = (1,2)
            self.pname  = pcurve

        ### find x-correlation file
        sacf  = os.path.basename(self.name).split('_s_')[0]+'_s'
        if self.dirs.has_key('xdir'):
            xcurve = os.path.join(self.dirs['xdir'],sacf)
        if not os.path.isfile(xcurve):
            xcurve = os.path.join(os.path.dirname(self.name),sacf)
        if os.path.isfile(xcurve):
            try:
                self.xtrace = sac.ReadSac(xcurve)
                self.xname  = xcurve
            except sac.SacIOError:
                print "can't read SAC file %s"%xcurve

        ### find 2nd iteration dispersion curve
        d2f  = sacf+'_4_DISP.*'
        d2curve = 'dummy'
        if self.dirs.has_key('ddir'):
            try:
                d2curve = glob.glob(os.path.join(self.dirs['ddir'],d2f))[0]
            except:
                pass
        if not os.path.isfile(d2curve):
            try:
                d2curve = glob.glob(os.path.join(os.path.dirname(self.name),d2f))[0]
            except:
                pass
        if os.path.isfile(d2curve):
            self.d2trace = load(d2curve)
            self.d2name  = d2curve
        

if __name__ == '__main__':
    try:
        fname = sys.argv[1]
    except:
        print "usage: %s filename [pred-dir] [xdir]"%(os.path.basename(sys.argv[0]))
        sys.exit(1)

    dirs = {}
    try:
        dirs['pdir'] = sys.argv[2]
    except:
        pass
    try:
        dirs['xdir'] = sys.argv[3]
    except:
        pass
    try:
        dirs['ddir'] = sys.argv[4]
    except:
        pass
    
    d = ReadDisp(fname,dirs=dirs)
    d.find_aux()
    if hasattr(d,'xname'):
        subplot(2,1,1)
        plot(d.xtrace.seis[0:1000])
        subplot(2,1,2)
    else:
        subplot(1,1,1)
    if d.type == 'phase':
        plot(d.trace[:,2],d.trace[:,4])
    if d.type == 'group':
        plot(d.trace[:,2],d.trace[:,3])
    if hasattr(d,'pname'):
        plot(d.ptrace[:,0],d.ptrace[:,1])
    if hasattr(d,'d2name'):
        plot(d.d2trace[:,2],d.d2trace[:,4])
    ylim(2.5,5)
    show()
