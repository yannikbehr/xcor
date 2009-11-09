#!/usr/bin/env mypython

"""
measure signal-to-noise ratios of cross-correlations
"""

import os, sys, glob, os.path, string
from ConfigParser import SafeConfigParser

def snr(datdir,bin,pattern):
    curdir = os.getcwd()
    os.chdir(datdir)
    fn = 'files.txt'
    os.system('ls %s >%s'%(pattern,fn))
    os.system('%s %s'%(bin,fn))
    os.remove(fn)
    os.chdir(curdir)


if __name__ == '__main__':
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            xcorfiles = cp.get('snr','xcorfiles')
            command   = cp.get('snr','snrbin')
            spattern  = cp.get('snr','spattern')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "usage: %s -c config-file"%os.path.basename(sys.argv[0])
        sys.exit(1)
    else:
        snr(xcorfiles,command,spattern)
