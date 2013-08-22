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
                # [hf,hi,hs,seis,ok] = p.ReadSacFile(f)
                p = SacIO(f)
                # hf = p.GetHvalue('hf')
                # hi = p.GetHvalue('hi')
                # hs = p.GetHvalue('hs')
                hf = p.hf
                hi = p.hi
                hs = p.hs

#                if not ok:
#                    par.log.error("ERROR: cannot read sac-file %s" %(f))
#                    return -1
                trace = np.array(p.seis, dtype=float)
                # ## check if trace has values other than 'nan'
                if np.all(np.isnan(trace)):
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
                    oldtrace = np.array(par.mystack[comb1]['trace'], dtype=float)
                    newtrace = oldtrace + trace
                    if len(newtrace) > 0:
                        oldstack = p.GetHvalue('mag')
                        newstack = nstack + oldstack
                        p.SetHvalue('mag', newstack)
                        new = {}
                        new[comb1] = {}
                        new[comb1]['trace'] = newtrace
                        new[comb1]['hf'] = hf
                        new[comb1]['hs'] = hs
                        new[comb1]['hi'] = hi
                        par.mystack.update(new)
                        continue
                    else:
			return -1
                elif comb2 in par.mystack.keys():
                    oldtrace = np.array(par.mystack[comb2]['trace'], dtype=float)
                    newtrace = oldtrace + trace[::-1]
                    if len(newtrace) > 0:
                        oldstack = p.GetHvalue('mag')
                        newstack = nstack + oldstack
                        p.SetHvalue('mag', newstack)
                        new = {}
                        new[comb2] = {}
                        new[comb2]['trace'] = newtrace
                        new[comb2]['hf'] = hf
                        new[comb2]['hs'] = hs
                        new[comb2]['hi'] = hi
                        par.mystack.update(new)
                        continue
                    else: return -1
                else:
                    par.mystack[comb1] = {}
                    par.mystack[comb1]['trace'] = trace
                    par.mystack[comb1]['hf'] = hf
                    par.mystack[comb1]['hs'] = hs
                    par.mystack[comb1]['hi'] = hi
                    continue

    return 0


def write_stack(stackdir, par):
    """write contents of global 'COR'-file dict to disk"""
    if not os.path.isdir(stackdir):
        os.mkdir(stackdir)
    for stat in par.mystack.keys():
        # write stacked correlation
        t = SacIO()
        t.seis = par.mystack[stat]['trace']
        # p.seis = seis
        t.hf = par.mystack[stat]['hf']
        t.hs = par.mystack[stat]['hs']
        t.hi = par.mystack[stat]['hi']
        stat1, stat2 = stat.split('_')
        t.SetHvalue('kevnm', stat1)
        t.SetHvalue('kstnm', stat2)
        b = t.GetHvalue('b')
        lat1 = t.GetHvalue('evla')
        lon1 = t.GetHvalue('evlo')
        lat2 = t.GetHvalue('stla')
        lon2 = t.GetHvalue('stlo')
        # use the obspy version here
        dist, dump1, dump2 = gps2DistAzimuth(lat1, lon1, lat2, lon2)
        dist = dist / 1000.0
        # dist, dump1, dump2 = dz.delaz(lat1,lon1,lat2,lon2,0)
        # dist = dist*math.pi*6371/180
        t.SetHvalue('dist', dist)
        try:
            app = par.spattern.split('.SAC')[1]
        except:
            app = ''
        outputfile = stackdir + '/COR_' + stat + '.SAC' + app
        # p.WriteSacBinary(outputfile, hf, hi, hs, a.array('f',seis))
        t.WriteSacBinary(outputfile)

        # write symmetric part
        delta = t.GetHvalue('delta')
        null = int(round(-1 * b / delta))
        reversed = t.seis[::-1]
        newseis = t.seis + reversed
        t.seis = newseis[null:]
        t.SetHvalue('npts', len(newseis[null:]))
#        p.seis = p.seis[null:]
        t.SetHvalue('b', 0)
        t.SetHvalue('o', 0)
        outputfile = stackdir + '/COR_' + stat + '.SAC' + app + '_s'
        t.WriteSacBinary(outputfile)


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
