#!/usr/bin/env mypython


""" combine phase velocity measurements and snr measurements to build a
phase velocity table that is required by Barmin et al. 2D surface wave
inversion program
"""

import os, sys, optparse, os.path, string
from obspy.sac import ReadSac, SacError, SacIOError
#sys.path.append(os.path.join(os.environ['PROC_SRC'],'disp_curves'))
from dispio import ReadDisp
import numpy, glob
import pylab as pl
import scipy
from scipy.signal import *
import scipy.interpolate
import logging, logging.handlers
from ConfigParser import SafeConfigParser
import progressbar as pg

DEBUG=True

class PrepDispErr(Exception): pass

class PrepDisp:
    def __init__(self,cnf):
        self.dthresh   = int(cnf.get('mktables','dthresh'))
        self.snrthresh = int(cnf.get('mktables','snrthresh'))
        self.vmax      = eval(cnf.get('mktables','vmax'))
        self.periods   = eval(cnf.get('mktables','periods'))
        self.dispdir   = cnf.get('mktables','dispdir')
        self.outdir    = cnf.get('mktables','outdir')
        if not os.path.isdir(self.outdir):
            os.makedirs(self.outdir)
        self.spattern  = cnf.get('mktables','spattern')
        self.dtype     = cnf.get('mktables','dtype')
        if not self.dtype:
            raise PrepDispErr("Specify type of dispersion curve (group or phase)")
        self.dirs      = {'xdir':cnf.get('mktables','xdir')}
        ### setup logging
        logdir         = cnf.get('mktables','log')
        if not os.path.isdir(logdir):
            os.makedirs(logdir)
        DBG_FILENAME = os.path.join(logdir,'prep_disp_boulder.dbg')
        ERR_FILENAME = os.path.join(logdir,'prep_disp_boulder.err')
        self.mylogger = logging.getLogger('MyLogger')
        self.mylogger.setLevel(logging.DEBUG)
        handlerdbg = logging.FileHandler(DBG_FILENAME,'w')
        handlererr = logging.FileHandler(ERR_FILENAME,'w')
        handlererr.setLevel(logging.ERROR)
        self.mylogger.addHandler(handlerdbg)
        self.mylogger.addHandler(handlererr)


    def __call__(self):
        fhs = {}
        for p in self.periods:
            f0 = open("%s/%ds_%dlambda_%d.txt"%(self.outdir,p,self.dthresh,self.snrthresh), 'w')
            f1 = open("%s/%ds_%dlambda_%d_gv.txt"%(self.outdir,p,self.dthresh,self.snrthresh), 'w')
            fhs[p]=(f0,f1)
        ### from the manually picked dispersion curves it can happen that some have
        ### '_4_DISP.1'-ending (2nd iteration) and some have '_2_DISP.1'-ending (1st
        ### iteration) --> create a list of files, that contain the '_2_DISP.1' files
        ### unless there's only a '_4_DISP.1' file available
        dispfiles = glob.glob(os.path.join(self.dispdir,self.spattern))
        for _f in glob.glob(self.dispdir+'/*s_4_DISP.1'):
            _a = _f.split('_4_')[0]+'_2_DISP.*'
            _l = glob.glob(_a)
            if len(_a)<1:
                dispfiles.append(_f)

        if len(dispfiles)<1:
            print "file list to process is empty!"
            return
        
        ########### set up progress bar ############################
        widgets = ['mktable: ', pg.Percentage(), ' ', pg.Bar('#'),
                   ' ', pg.ETA()]
        ############################################################
        if not DEBUG:
            pbar = pg.ProgressBar(widgets=widgets, maxval=len(dispfiles)).start()
            cnt = 0
        for dispfn in dispfiles:
            if not DEBUG:
                cnt += 1
                pbar.update(cnt)
            a = dispfn.split('_s_')
            snr_fn = a[0]+'_s_snr.txt'
            if not os.path.isfile(snr_fn):
                print "Cannot find snr-file for %s"%dispfn
                return
            for _p in self.periods:
                try:
                    dispval = self.my_interp(_p,dispfn,type=self.dtype)
                except PrepDispErr,e:
                    continue
                else:
                    try:
                        snrval = self.my_interp(_p,snr_fn,type='snr')
                    except PrepDispErr,e:
                        print snr_fn,e
                        continue
                    else:
                        if snrval > self.snrthresh:
                            try:
                                if self.dtype == 'phase':
                                    self.write_table(dispfn,dispval,_p, fhs[_p][0],snrval,dirs=self.dirs)
                                if self.dtype == 'group':
                                    self.write_table(dispfn,dispval,_p, fhs[_p][1],snrval,dirs=self.dirs)
                            except PrepDispErr,e:
                                continue
    
        for i in fhs.keys():
            fhs[i][0].close()
            fhs[i][1].close()
        if not DEBUG:
            pbar.finish()


    def my_interp(self,p,fn,type=None):
        """ interpolate phase velocity dispersion curve using cubic
        splines or linear interpolation and measure values at given periods"""
        if not type:
            raise PrepDispErr("Specify type of dispersion curve (group or phase)")
        if type == 'group':
            cols = (2,3)
        if type == 'phase':
            cols = (2,4)
        if type == 'snr':
            cols = (0,1)
            
        DISP    = pl.load(fn, usecols=cols)
        if p < DISP[:,0].min() or p > DISP[:,0].max():
            raise PrepDispErr('Period value out of bounds')
        ## linear interpolation
        try:
            val = scipy.interp(p,DISP[:,0], DISP[:,1])
        except:
            self.mylogger.error('Cannot interpolate: %s'%fn)
            raise PrepDispErr('Cannot interpolate')
        else:
            return val
    
    
    def write_table(self,fn,dispval,per,fh,snrval,dirs={}):
        """write table for inversion program"""
        d = ReadDisp(fn,dirs=dirs)
        d.find_aux()
        try:
            xtr = ReadSac(d.xname)
        except (SacError,SacIOError),e:
            print e
            self.mylogger.debug('Cannot read file: %s'%d.xname)
            raise PrepDispErr('Cannot read file: %s'%d.xname)
        except AttributeError,e:
            print e,fn
            return
        evla  = xtr.GetHvalue('evla')
        evlo  = xtr.GetHvalue('evlo')
        stla  = xtr.GetHvalue('stla')
        stlo  = xtr.GetHvalue('stlo')
        st1nm = xtr.GetHvalue('kstnm')
        st2nm = xtr.GetHvalue('kevnm')
        dist  = xtr.GetHvalue('dist')
        for _i in sorted(self.vmax.keys()):
            if per <= _i:
                vmax = self.vmax[_i]
                break
        if dist > self.dthresh*vmax*per:
            newline = "%d  %f  %f  %f  %f  %f  1  1  %s %s %f"\
                      %(per,evla,evlo,stla,stlo,dispval,st1nm,st2nm,snrval)
            print >>fh, newline
        else:
            self.mylogger.debug('distance too short: T=%f delta=%f file:%s'%(per,dist,d.xname))
            raise PrepDispErr('distance too short: T=%f delta=%f file:%s'%(per,dist,d.xname))


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
    t = PrepDisp(cp)()

