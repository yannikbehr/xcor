#!/usr/bin/env mypython
"""Do temporal and spectral normalization by calling sac-routines and
the fortran routines filter4.f, white_phamp_2cmp.f and
white_phamp_1cmp.f by calling their respective C-drivers.
"""

import os
import string
import sys
import subprocess as sp
sys.path.append(os.path.join(os.environ['XCORSRC'], 'src', 'common'))
import sac_db
from ConfigParser import SafeConfigParser
import progressbar as pg
from obspy.sac import *
from obspy.core.util import NamedTemporaryFile

DEBUG = False
months = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep',
          10:'Oct', 11:'Nov', 12:'Dec'}

def white_1_comp(fns, lowerp, upperp, utaper, ltaper, npow, bindir, sacbin):
    """Downweight parts with earthquakes and smooth the spectrum for
    the vertical component"""
    whitefilter = bindir + '/white_1cmp' + ' 1>/dev/null'
    # whitefilter = bindir+'/white_1cmp'
    saccmd = sacbin + ' 1>/dev/null'
    p1 = sp.Popen(saccmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
    child1 = p1.stdin
    src, tar, eqtar = fns[0]
    tempfile = NamedTemporaryFile().name
    print >> child1, "r %s" % (eqtar + '_tmp')
    print >> child1, "abs"
    print >> child1, "smooth mean h 128"
    print >> child1, "w over %s" % tempfile
    print >> child1, "r %s" % (tar + '_tmp')
    print >> child1, "divf %s" % tempfile
    print >> child1, "w over %s" % (tar)
    print >> child1, "q"
    err1 = child1.close()
    ret1 = p1.wait()
    # os.remove('a1.avg') - Is overwritten by above sac command?
    os.remove(eqtar + '_tmp')
    os.remove(tar + '_tmp')
    if err1 or ret1 != 0:
        raise RuntimeError, '%r failed with exit code %d' % (saccmd, err1)
    p2 = sp.Popen(whitefilter, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
    child2 = p2.stdin
    print >> child2, ltaper, lowerp, upperp, utaper, npow, tar
    err2 = child2.close()
    ret2 = p2.wait()
    if err2 or ret2 != 0:
        raise RuntimeError, '%r failed with exit code %d' % (whitefilter, err2)
    os.remove(tar)
    os.remove(tempfile)
    return 1



def white_2_comp(fns, lowerp, upperp, utaper, ltaper, npow, bindir, sacbin):
    """Downweight parts with earthquakes and smooth the spectrum for
    the two horizontal components simultaneously"""
    whitefilter = bindir + '/white_2cmp' + ' 1>/dev/null'
    # whitefilter = bindir+'/white_2cmp'
    saccmd = sacbin + ' 1>/dev/null'
    srcE, tarE, eqtarE = fns[0]
    srcN, tarN, eqtarN = fns[1]
    p1 = sp.Popen(saccmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
    child1 = p1.stdin
    print >> child1, "r %s %s" % (eqtarE + '_tmp', eqtarN + '_tmp')
    print >> child1, "abs"
    print >> child1, "smooth mean h 128"
    print >> child1, "w aaa bbb"
    print >> child1, "r aaa"
    print >> child1, "subf bbb"
    print >> child1, "abs"
    print >> child1, "addf aaa"
    print >> child1, "addf bbb"
    print >> child1, "div 2"
    print >> child1, "w a1.avg"
    print >> child1, "r %s %s" % (tarE + '_tmp', tarN + '_tmp')
    print >> child1, "divf a1.avg"
    print >> child1, "w %s %s" % (tarE, tarN)
    print >> child1, "q"
    err1 = child1.close()
    ret1 = p1.wait()
    if err1 or ret1 != 0:
        raise RuntimeError, '%r failed with exit code %d' % (saccmd, err1)
    if os.path.isfile('./aaa'):
        os.remove('./aaa')
    if os.path.isfile('./bbb'):
        os.remove('./bbb')
    if os.path.isfile('./a1.avg'):
        os.remove('./a1.avg')
    os.remove(eqtarN + '_tmp')
    os.remove(eqtarE + '_tmp')
    os.remove(tarN + '_tmp')
    os.remove(tarE + '_tmp')
    p2 = sp.Popen(whitefilter, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
    child2 = p2.stdin
    print >> child2, ltaper, lowerp, upperp, utaper, npow, tarE, tarN
    err2 = child2.close()
    ret2 = p2.wait()
    if err2 or ret2 != 0:
        raise RuntimeError, '%r failed with exit code %d' % (whitefilter, err2)
    os.remove(tarE)
    os.remove(tarN)
    return 1

def filter_f(fns, ltaper, lowerp, upperp, utaper, eqband, eqltaper, equtaper, npow, bindir):
    """
    Filter seismograms in analysis band and earthquake band
    """
    # filtercmd = bindir+"/filter4"
    filtercmd = bindir + "/filter4 1>/dev/null"
    for src, tar, eqtar in fns:
        p = sp.Popen(filtercmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
        child = p.stdin
        print >> child, ltaper, lowerp, upperp, utaper, npow, src, tar + '_tmp'
        err = child.close()
        ret = p.wait()
        if err or ret != 0:
            raise RuntimeError, '%r failed with exit code %d' % (filtercmd, err)
        p = sp.Popen(filtercmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
        child = p.stdin
        print >> child, eqltaper, eqband[0], eqband[1], equtaper, npow, tar + '_tmp', eqtar + '_tmp'
        err = child.close()
        ret = p.wait()
        if err or ret != 0:
            raise RuntimeError, '%r failed with exit code %d' % (filtercmd, err)
    return 1

def specnorm(sdb, ne, ns, upperp, lowerp, rootdir, polarity='vertical', eqband=[50, 15],
             bindir=os.path.join(os.environ['XCORSRC'], 'bin'), sacbin=None, npow=1):
    """
    Check filenames and call filtering and normalization functions.
    """
    utaper = upperp - (float(upperp) / 100) * 20
    ltaper = lowerp + (float(lowerp) / 100) * 20
    equtaper = eqband[1] - (float(eqband[1]) / 100) * 20
    eqltaper = eqband[0] + (float(eqband[0]) / 100) * 20
    if polarity == 'horizontal':
        srcE = sdb.rec[ne][ns].ft_fname
        srcN = srcE.replace('E.SAC', 'N.SAC')
        if not os.path.isfile(srcE): return 1
        if not os.path.isfile(srcN): return 1
        bpfile = "%.1fto%.1f" % (upperp, lowerp)
        year = str(sdb.ev[ne].yy)
        month = months[sdb.ev[ne].mm]
        day = "%s_%d_%d_0_0_0" % (year, sdb.ev[ne].mm, sdb.ev[ne].dd)
        bpdir = os.path.join(rootdir, bpfile, year, month, day)
        eqdir = os.path.join(rootdir, bpfile, year, month, day, 'eqband')
        if not os.path.isdir(eqdir):
            os.makedirs(eqdir)
        eqtarE = os.path.join(eqdir, os.path.basename(srcE))
        tarE = os.path.join(bpdir, os.path.basename(srcE))
        eqtarN = os.path.join(eqdir, os.path.basename(srcN))
        tarN = os.path.join(bpdir, os.path.basename(srcN))
        fns = [(srcE, tarE, eqtarE), (srcN, tarN, eqtarN)]
    if polarity == 'vertical':
        src = sdb.rec[ne][ns].ft_fname
        if not os.path.isfile(src): return 1
        bpfile = "%.1fto%.1f" % (upperp, lowerp)
        year = str(sdb.ev[ne].yy)
        month = months[sdb.ev[ne].mm]
        day = "%s_%d_%d_0_0_0" % (year, sdb.ev[ne].mm, sdb.ev[ne].dd)
        bpdir = os.path.join(rootdir, bpfile, year, month, day)
        eqdir = os.path.join(rootdir, bpfile, year, month, day, 'eqband')
        if not os.path.isdir(eqdir):
            os.makedirs(eqdir)
        eqtar = os.path.join(eqdir, os.path.basename(src))
        tar = os.path.join(bpdir, os.path.basename(src))
        fns = [(src, tar, eqtar)]
    # ## filtering and temporal normalization
    filter_f(fns, ltaper, lowerp, upperp, utaper, eqband, eqltaper, equtaper, npow, bindir)
    # ## whitening
    if polarity == 'vertical':
        white_1_comp(fns, lowerp, upperp, utaper, ltaper, npow, bindir, sacbin)
    if polarity == 'horizontal':
        white_2_comp(fns, lowerp, upperp, utaper, ltaper, npow, bindir, sacbin)
    return 1




if __name__ == '__main__':
    try:
        if string.find(sys.argv[1], '-c') != -1:
            config = sys.argv[2]
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        config = 'config.txt'

    if not os.path.isfile(config):
        print "no config file found"
        sys.exit(1)

    conf = SafeConfigParser()
    conf.read(config)

    # frequency band +- 20% as taper
    rootdir = conf.get("whitening", "rootdir")
    sacbin = conf.get("whitening", "sacbin")
    bindir = conf.get("whitening", "bindir")
    upperp = float(conf.get("whitening", "upperperiod"))
    lowerp = float(conf.get("whitening", "lowerperiod"))
    polarity = conf.get("whitening", "polarity")
    tmpdir = conf.get("whitening", "tmpdir")
    dbname = conf.get("whitening", "dbname")
    sdbf = os.path.join(tmpdir, dbname)
    sdb = sac_db.read_db(sdbf)
    if not DEBUG:
        widgets = ['whitening: ', pg.Percentage(), ' ', pg.Bar('#'),
                   ' ', pg.ETA()]
        pbar = pg.ProgressBar(widgets=widgets, maxval=sdb.nev).start()
    for ne in xrange(sdb.nev):
        if not DEBUG:
            pbar.update(ne)
        for ns in xrange(sdb.nst):
            specnorm(sdb, ne, ns, upperp, lowerp, rootdir, polarity=polarity, sacbin=sacbin, bindir=bindir)
        try:
            year = str(sdb.ev[ne].yy)
            month = months[sdb.ev[ne].mm]
            day = "%s_%d_%d_0_0_0" % (year, sdb.ev[ne].mm, sdb.ev[ne].dd)
            bpfile = "%.1fto%.1f" % (upperp, lowerp)
            eqdir = os.path.join(rootdir, bpfile, year, month, day, 'eqband')
            os.rmdir(eqdir)
        except Exception:
            if DEBUG:
                print "cannot remove %s" % eqdir
            continue
    if not DEBUG:
        pbar.finish()

