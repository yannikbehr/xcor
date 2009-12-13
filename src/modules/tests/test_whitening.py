#!/usr/bin/env mypython

"""
unittest for whitening routine
"""

import inspect, os, unittest, sys
import numpy as np
from obspy.sac import *
#from pylab import *
from ConfigParser import SafeConfigParser
sys.path.append(os.path.join(os.environ['AUTO_SRC'],'src/modules'))
from whitening import *
from sac_db import *
import filter4

class WhitenTestCase(unittest.TestCase):
    """
    Test cases for whitening.py
    """

    def testOld(self):
        tfile1 = os.path.join(os.path.dirname(__file__),'data/2001/Apr/2.0to90.0/2001_4_27_0_0_0/ft_grid_KNGC.BHZ.SAC')
        tfile1amp = os.path.join(os.path.dirname(__file__),'data/2001/Apr/2.0to90.0/2001_4_27_0_0_0/ft_grid_KNGC.BHZ.SAC.am')
        tfile1eq  = os.path.join(os.path.dirname(__file__),'data/2001/Apr/2.0to90.0/2001_4_27_0_0_0/eqband/ft_grid_KNGC.BHZ.SAC')
        tfile2 = os.path.join(os.path.dirname(__file__),'data/2001/Apr/2001_4_27_0_0_0/ft_grid_KNGC.BHZ.SAC')
        tfileeq = os.path.join(os.path.dirname(__file__),'data/2001/Apr/2.0to90.0/2001_4_27_0_0_0/eqband/ft_grid_KNGC.BHZ.SAC')
        if False:
            ### run do_whiten_new
            shutil.rmtree(os.path.join(os.path.dirname(__file__),'data/2001/Apr/2.0to90.0/'))
            output = open('config.txt','w')
            outlines = []
            outlines.append("[whitening]\n")
            outlines.append("sacfiles=%s\n"%(os.path.join(os.path.dirname(__file__),'data/')))
            outlines.append("sacdir=/usr/local/sac/bin/sac\n")
            outlines.append("bindir=/home/behrya/dev/auto_git/bin\n")
            outlines.append("prefix=ft_grid\n")
            outlines.append("upperperiod=2.0\n")
            outlines.append("lowerperiod=90.0\n")
            outlines.append("complist=BHZ\n")
            outlines.append("skip_directories=5to100")
            output.writelines(outlines)
            output.close()
            cmd = os.path.join(os.environ['AUTO_SRC'],'src/modules/do_whiten_new.py')
            os.system(cmd)

        sdb = SacDb()
        sdb.nev = 1
        sdb.nst = 1
        sdb.rec[0][0].ft_fname = tfile2
        trace_norm = ReadSac(tfile1+'_smooth').seis
        trace_filter = ReadSac(tfile1+'_filter').seis
        s, samp, sph, eqtr_s, ftr, ftr_norm = whitening(sdb,0,0,90.,2.,testtrace=trace_norm)
        xorig = ReadSac(tfile1).seis
        xorig_amp = ReadSac(tfile1+'.am').seis
        xorig_ph = ReadSac(tfile1+'.ph').seis
        np.testing.assert_array_almost_equal(xorig,s,decimal=6)
        np.testing.assert_array_almost_equal(xorig_amp,samp,decimal=6)
        np.testing.assert_array_almost_equal(trace_filter,ftr,decimal=6)
        s, samp, sph, eqtr_s, ftr, ftr_norm = whitening(sdb,0,0,90.,2.)
        #plot(xorig)
        #plot(s,'k--')
        #show()
        
def suite():
    return unittest.makeSuite(WhitenTestCase, 'test')


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
