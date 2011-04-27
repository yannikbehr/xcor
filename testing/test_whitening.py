#!/usr/bin/env mypython
"""
Test do_whiten_new script.
"""

import numpy as np
import unittest
import glob
import os
from obspy.sac import *
from ConfigParser import SafeConfigParser
import tempfile
import shutil
import sys
os.environ['AUTO_SRC'] = os.path.dirname(os.path.realpath(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.environ['AUTO_SRC'],'src/modules'))
from sac_db import *
from do_whiten_new import specnorm



class WhitenTestCase(unittest.TestCase):
    def which(self,program):
        def is_exe(fpath):
            return os.path.exists(fpath) and os.access(fpath, os.X_OK)
        
        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file
                
        return None
    
    def setUp(self):
        self.sdb = SacDb()
        self.sdb.nev = 1
        self.sdb.nst = 1
        self.sdb.rec[0][0].fname = './testdata/S28.HHZ.SAC'
        self.sdb.rec[0][0].ft_fname = './testdata/ft_test_resp_S28.HHZ.SAC'
        self.sdb.rec[0][0].resp_fname = './testdata/miniseed/RESP.XH.S28..HHZ'
        self.sdb.rec[0][0].pz_fname = './testdata/miniseed/SAC_PZs_XH_S28_HHZ'
        self.sdb.ev[0].yy = 2001
        self.sdb.ev[0].mm = 5
        self.sdb.ev[0].dd = 10
        self.tmpdir = tempfile.mkdtemp()
        if self.which('sac') is None:
            print "Can't find SAC executable"
            sys.exit(1)
        
    def test_whiten_vertical(self):
        sacbin='sac'
        specnorm(self.sdb,0,0,0.4,100.0,self.tmpdir,polarity='vertical',eqband=[50,15],
                 bindir=os.path.join(os.environ['AUTO_SRC'],'bin'),sacbin=sacbin,npow=1)
        self.wt_dir = os.path.join(self.tmpdir,'0.4to100.0/2001/May/2001_5_10_0_0_0/')
        tr1 = ReadSac(os.path.join(self.wt_dir,'ft_test_resp_S28.HHZ.SAC.am'))
        tr2 = ReadSac(os.path.join(self.wt_dir,'ft_test_resp_S28.HHZ.SAC.ph'))
        test_dir = os.path.join(os.environ['AUTO_SRC'],'testing/testdata')
        tr3 = ReadSac(os.path.join(test_dir,'ft_test_resp_S28.HHZ.SAC.am'))
        tr4 = ReadSac(os.path.join(test_dir,'ft_test_resp_S28.HHZ.SAC.ph'))
        np.testing.assert_array_equal(tr1.seis, tr3.seis)
        np.testing.assert_array_equal(tr2.seis, tr4.seis)

    def tearDown(self):
        fn1 = os.path.join(self.wt_dir,'ft_test_resp_S28.HHZ.SAC.am')
        fn2 = os.path.join(self.wt_dir,'ft_test_resp_S28.HHZ.SAC.ph')
        if os.path.isfile(fn1):
            os.remove(fn1)
        if os.path.isfile(fn2):
            os.remove(fn2)
        if os.path.isdir(self.tmpdir):
            shutil.rmtree(self.tmpdir)


def suite():
    return unittest.makeSuite(WhitenTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
