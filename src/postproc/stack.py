#!/usr/bin/env mypython
"""script to stack horizontal component cross-correlation results"""

import numpy as np
import array as a
# import pysacio as pysac
from obspy.sac import *
import os, os.path, glob, re, sys, string, math
from ConfigParser import SafeConfigParser
sys.path.append('/Users/home/carrizad/xcorr/src/modules/')
# import delaz as dz
from obspy.core.util import gps2DistAzimuth

import logging

class PAR: pass

def find_match(par, dirname, filelist):
    """find 'COR'-files in 'dirname' and add them to global dict of 'COR'-files """
    for dn in par.skipdir:
        try:
            i = filelist.index(dn)
            del filelist[i]
        except: pass
        if dirname.find(dn) != -1:
            return

    print '... in %s' % dirname
    corfiles = glob.glob(os.path.join(dirname, 'COR*'))
    if len(corfiles) > 0:
        for f in corfiles:
            # match = re.search('COR_(\\w*_\\w*).SAC',f)
            match = re.search(par.spattern, f)

            if match:
                p = SacIO(f)

                # ## check if trace has values other than 'nan'
                if np.all(np.isnan(p.seis)):
                    par.log.error('no data for %s' % f)
                    continue
                nstack = p.GetHvalue('mag')
                stats = string.split(match.group(1), '_')
                stat1 = stats[0]
                stat2 = stats[1]
                # print stat1, stat2
                # account for the fact that the correlation could be
                # either COR_MATA_TIKO.SAC or COR_TIKO_MATA.SAC
                comb1 = stat1 + '_' + stat2
                comb2 = stat2 + '_' + stat1
                if comb1 in par.mystack.keys():
                    oldp = par.mystack[comb1]
                    oldp.seis += p.seis
                    oldp.SetHvalue('mag', oldp.GetHvalue('mag') + nstack)
                    continue
                elif comb2 in par.mystack.keys():
                    oldp.seis += p.seis[::-1]
                    oldp.SetHvalue('mag', oldp.GetHvalue('mag') + nstack)
                    continue
                else:
                    par.mystack[comb1] = p
                    continue
    return 0


def write_stack(stackdir, par):
    """write contents of global 'COR'-file dict to disk"""
    if not os.path.isdir(stackdir):
        os.mkdir(stackdir)
    for _k in par.mystack.keys():
        # write stacked correlation
        st = par.mystack[_k]
        stat1, stat2 = _k.split('_')
        st.SetHvalue('kevnm', stat1)
        st.SetHvalue('kstnm', stat2)
        try:
            app = par.spattern.split('.SAC')[1]
        except:
            app = ''
        outputfile = stackdir + '/COR_' + _k + '.SAC' + app
        st.WriteSacBinary(outputfile)

        # write symmetric part
        null = int(round(-1 * st.b / st.delta))
        reversed = st.seis[::-1]
        newseis = st.seis + reversed
        st.seis = newseis[null:]
        st.SetHvalue('npts', len(newseis[null:]))
        st.SetHvalue('b', 0)
        st.SetHvalue('o', 0)
        outputfile = stackdir + '/COR_' + _k + '.SAC' + app + '_s'
        st.WriteSacBinary(outputfile)


if __name__ == '__main__':

    try:
        if string.find(sys.argv[1], '-c') != -1:
            config = sys.argv[2]
            print "config file is: ", sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            rootdir = cp.get('stack', 'cordir')
            stackdir = cp.get('stack', 'stackdir')
            spattern = cp.get('stack', 'spattern')
            tmpdir = cp.get('stack', 'tmpdir')
            skipdir = cp.get('stack', 'skipdir')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "usage: %s -c config-file" % os.path.basename(sys.argv[0])
        sys.exit(1)

    ######## setup logging ################
    DBG_FILENAME = tmpdir + '/stack.log'
    ERR_FILENAME = tmpdir + '/stack.err'

    mylogger = logging.getLogger('MyLogger')
    mylogger.setLevel(logging.DEBUG)
    handlerdbg = logging.FileHandler(DBG_FILENAME, 'w')
    handlererr = logging.FileHandler(ERR_FILENAME, 'w')
    handlererr.setLevel(logging.ERROR)

    mylogger.addHandler(handlerdbg)
    mylogger.addHandler(handlererr)


    for sp in spattern.split(','):
        par = PAR()
        par.mystack = {}
        par.spattern = sp
        # par.spattern = 'COR_(\\w*_\\w*).SAC'
        par.skipdir = skipdir.split(',')
        par.log = mylogger
        print 'searching for files matching %s' % sp
        os.path.walk(rootdir, find_match, par)
        print 'writing stacks to %s' % stackdir
        write_stack(stackdir, par)
