#!/usr/bin/env mypython

"""
tests for xcor modules
"""

import os, sys, os.path
sys.path.append(os.path.join(os.environ['AUTO_SRC'],'src/modules'))
import unittest
from initsac_db import *

class XcorTestCase(unittest.TestCase):
    """
    Test cases for xcor-routines
    """
    
    def test_xcorfftw(self):
        if os.system('./xcor_fftw') != 0:
            raise Exception

def suite():
    return unittest.makeSuite(XcorTestCase,'test')

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
