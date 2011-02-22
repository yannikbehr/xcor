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
sys.path.append('../src/modules')
from sac_db import *
import rm_inst
class RmInstTestCase(unittest.TestCase):

    def setUp(self):
        self.sdb = SacDb()
        self.sdb.nev = 1
        self.sdb.nst = 1
        self.sdb.rec[0][0].fname = './testdata/S28.HHZ.SAC'
        self.sdb.rec[0][0].ft_fname = './testdata/ft_test_S28.HHZ.SAC'
        self.sdb.rec[0][0].resp_fname = './testdata/miniseed/RESP.XH.S28..HHZ'
        if os.path.isfile(self.sdb.rec[0][0].ft_fname):
            os.remove(self.sdb.rec[0][0].ft_fname)

    def test_rminst(self):
        sacbin='/usr/local/sac101.3b/bin/sac'
        rm_inst.rm_inst(self.sdb,0,0,delta=0.1,rminst=False,instype='resp',\
                        plow=100.,phigh=0.3,sacbin=sacbin,\
                        t1=4000,nos=81000,filter=False)
        tr1 = ReadSac('./testdata/ft_S28.HHZ.SAC')
        tr2 = ReadSac('./testdata/ft_test_S28.HHZ.SAC')
        np.testing.assert_array_equal(tr1.seis, tr2.seis)



def suite():
    return unittest.makeSuite(RmInstTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
