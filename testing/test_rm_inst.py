#!/usr/bin/env mypython
"""
Test rm_inst routine.
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
import rm_inst

class RmInstTestCase(unittest.TestCase):

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
        self.sdb.rec[0][0].resp_fname = './testdata/miniseed/RESP.XH.S28..HHZ'
        self.sdb.rec[0][0].pz_fname = './testdata/miniseed/SAC_PZs_XH_S28_HHZ'
        if self.which('sac') is None:
            print "Can't find SAC executable"
            sys.exit(1)

    def test_rminst_resp(self):
        sacbin='sac'
        self.sdb.rec[0][0].ft_fname = './testdata/ft_resp_S28.HHZ.SAC'
        rm_inst.rm_inst(self.sdb,0,0,delta=0.1,rminst=True,instype='resp',\
                        plow=100.,phigh=0.3,sacbin=sacbin,\
                        t1=4000,nos=81000,filter=False)
        tr1 = ReadSac('./testdata/ft_test_resp_S28.HHZ.SAC')
        tr2 = ReadSac('./testdata/ft_resp_S28.HHZ.SAC')
        np.testing.assert_array_equal(tr1.seis, tr2.seis)

    def test_rminst_pz(self):
        sacbin='sac'
        self.sdb.rec[0][0].ft_fname = './testdata/ft_pz_S28.HHZ.SAC'
        rm_inst.rm_inst(self.sdb,0,0,delta=0.1,rminst=True,instype='pz',\
                        plow=100.,phigh=0.3,sacbin=sacbin,\
                        t1=4000,nos=81000,filter=False)
        tr1 = ReadSac('./testdata/ft_test_pz_S28.HHZ.SAC')
        tr2 = ReadSac('./testdata/ft_pz_S28.HHZ.SAC')
        np.testing.assert_array_equal(tr1.seis, tr2.seis)

    def test_pz_vs_resp(self):
        ### It seems like the instrument response removal 
        ### using either pole-zero or RESP-files does not
        ### result in exactly the same trace
        tr1 = ReadSac('./testdata/ft_test_pz_S28.HHZ.SAC')
        tr2 = ReadSac('./testdata/ft_test_resp_S28.HHZ.SAC')
        rms = np.sqrt(np.sum((tr1.seis - tr2.seis) ** 2) / \
                      np.sum(tr2.seis ** 2))
        self.assertTrue(rms<0.00289)
                        
    def tearDown(self):
        if os.path.isfile('./testdata/ft_resp_S28.HHZ.SAC'):
            os.remove('./testdata/ft_resp_S28.HHZ.SAC')
        if os.path.isfile('./testdata/ft_pz_S28.HHZ.SAC'):
            os.remove('./testdata/ft_pz_S28.HHZ.SAC')
#  -0.313536.
#  This is inconsistent with the value calculated from poles and zeros: 0.010207.
#*CONSTANT 2.462500e+09
#orig:CONSTANT 8.016767e+07

 
        



def suite():
    return unittest.makeSuite(RmInstTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
