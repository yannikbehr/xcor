#!/usr/bin/env mypython
"""
Test sac_from_mseed routine.
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
from sac_from_mseed import SaFromMseed

class MseedTestCase(unittest.TestCase):
    """
    Test cases for processing
    """
    def setUp(self):
        # make config file
        self.tempdir = tempfile.mkdtemp()
        self.cp = SafeConfigParser()
        self.cp.add_section('mseed2sac')
        self.cp.set('mseed2sac','rdseed','/usr/local/bin/rdseed')
        self.cp.set('mseed2sac','bindir','/usr/local/xcorr/xcorr_git/bin/')
        self.cp.set('mseed2sac','mseedir','./testdata/miniseed/')
        self.cp.set('mseed2sac','outputdir',self.tempdir)
        self.cp.set('mseed2sac','dataless','./testdata/miniseed/START_XH_3.dataless')
        self.cp.set('mseed2sac','respdir','./testdata/miniseed/')
        self.cp.set('mseed2sac','search_pattern','*.D')

    def test_ms2sac(self):
        rdseed = self.cp.get('mseed2sac','rdseed')
        bindir   = self.cp.get('mseed2sac','bindir')
        mseedir  = self.cp.get('mseed2sac','mseedir')
        outputdir = self.cp.get('mseed2sac','outputdir')
        dataless = self.cp.get('mseed2sac','dataless')
        respdir = self.cp.get('mseed2sac','respdir')
        spat     = self.cp.get('mseed2sac','search_pattern')
        t = SaFromMseed(dataless, respdir, outputdir, bindir, rdseed)
        t(mseedir, outputdir, spat)
        fntemp = os.path.join(self.tempdir,'2001/May/2001_5_10_0_0_0/S28.HHZ.SAC')
        fntest = './testdata/S28.HHZ.SAC'
        tr1 = SacIO(fntemp)
        tr2 = SacIO(fntest)
        np.testing.assert_array_equal(tr1.seis, tr2.seis)
        shutil.rmtree(self.tempdir)
        fl = glob.glob('./rdseed.err_log.*')
        for _f in fl:
            os.remove(_f)

def suite():
    return unittest.makeSuite(MseedTestCase, 'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
