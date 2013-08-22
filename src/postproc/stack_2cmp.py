#!/usr/bin/env python
"""script to stack horizontal component cross-correlation results"""

import numpy as np
import array as a
from ConfigParser import SafeConfigParser
import os.path, glob, re, sys, string
sys.path.append('/home/behrya/dev/proc-scripts')
import pysacio as p
import delaz as dz
import stack as st

if __name__ == '__main__':

    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            rootdir  = cp.get('stack','cordir')
            stackdir = cp.get('stack','stackdir')
            spattern  = cp.get('stack','spattern')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "no configuration file found"
        sys.exit(1)

    for sp in spattern.split(','):
        par = st.PAR()
        par.mystack = {}
        par.spattern = sp
        os.path.walk(rootdir, st.find_match, par)
        st.write_stack(stackdir,par)
