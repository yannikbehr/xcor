#!/usr/bin/env mypython
"""
Remove instrument response using sac and cut precisely.

"""

import os
import sys
import glob
import string
sys.path.append(os.path.join(os.environ['XCORSRC'], 'src', 'common'))
from subprocess import *
from obspy.sac import *
from obspy import read
from obspy.signal.invsim import seisSim
import sac_db
from numpy import *
from ConfigParser import SafeConfigParser
import progressbar as pg

DEBUG = False

def abs_time(yy, jday, hh, mm, ss, ms):
    nyday = 0
    for i in range(1901, yy):
        if i % 4 == 0:
            nyday = nyday + 366
        else:
            nyday = nyday + 365
    return 24.*3600.*(nyday + jday) + 3600.*hh + 60.*mm + ss + 0.001 * ms



def cut(sdb, ne, ns, t1, nos):
    """
    cut traces precisely
    """
    fin = sdb.rec[ne][ns].ft_fname + '_tmp'
    fout = sdb.rec[ne][ns].ft_fname
    if DEBUG:
        print fin
        print fout
    p = SacIO(fin)
    dt = p.GetHvalue('delta')
    npts = p.GetHvalue('npts')
    yy = p.GetHvalue('nzyear')
    jday = p.GetHvalue('nzjday')
    hh = p.GetHvalue('nzhour')
    mm = p.GetHvalue('nzmin')
    ss = p.GetHvalue('nzsec')
    ms = p.GetHvalue('nzmsec')
    b = p.GetHvalue('b')
    # ## correct for milli-seconds in trace by linear interpolation
    tb = sdb.rec[ne][ns].t0
    te = sdb.ev[ne].t0
    t2 = t1 + (nos - 1)
    t1b = tb - te
    t1e = t1b + (npts - 1) * dt
    if t1b > t1 or t1e < t2 or t1e > 100000 / dt:
        print "ERROR: incompatible time limits for %s; cannot cut" % (fin)
        os.remove(fin)
        return
    if ms > 0.:
        frac = (int((0.001 * ms + dt) / dt) * dt - 0.001 * ms) / dt
        # 1./dt-0.001*ms/dt
        p.seis = p.seis[0:npts - 1] + frac * diff(p.seis)
        # ## round to next higher increment of dt
        # t0 = round(tb+frac*dt,-int(log10(dt)))
        t0 = tb + frac * dt
    else:
        t0 = tb
    istart = int(round(t1 / dt))
    ibegin = int(round((t0 - te) / dt))
    n = int(round(nos / dt))
    n1 = istart - ibegin
    p.SetHvalue("npts", n)
    p.SetHvalue("nzyear", 2000)
    p.SetHvalue("nzjday", 1)
    p.SetHvalue("nzhour", 0)
    p.SetHvalue("nzmin", 0)
    p.SetHvalue("nzsec", 0)
    p.SetHvalue("nzmsec", 0)
    p.SetHvalue("b", 0.)
    p.seis = p.seis[n1:n1 + n]
    p.WriteSacBinary(fout)
    os.remove(fin)


def rm_inst(sdb, ne, ns, factor=[10, 10], rminst=True, filter=False, instype='resp',
            plow=160., phigh=4., t1=1000, nos=84000, force=False):
    """
    downsample traces, remove mean, trend, cut them to the exact same
    time window, and either remove instrument response, filter, or leave
    them as they are
    """
    fl1 = 1.0 / (plow + 0.0625 * plow)
    fl2 = 1.0 / plow
    fl3 = 1.0 / phigh
    fl4 = 1.0 / (phigh - 0.25 * phigh)
    if DEBUG:
        print "f1=%.2f; f2=%.2f; f3=%.2f; f4=%.2f" % (fl1, fl2, fl3, fl4)
    if sdb.rec[ne][ns].fname == '':return
    if os.path.isfile(sdb.rec[ne][ns].ft_fname) and not force:
        sys.stderr.write("File %s already exists." % sdb.rec[ne][ns].ft_fname)
        return
    tr = read(sdb.rec[ne][ns].fname)[0]
    for _f in factor:
        tr.decimate(_f)
    date = tr.stats.starttime
    if instype == 'resp':
        if sdb.rec[ne][ns].resp_fname == '':
            if DEBUG:
                print "response file not found"
            return
        seedresp = {'filename': sdb.rec[ne][ns].resp_fname, 'date': date,
                    'units': 'VEL'}
        tr.data = seisSim(tr.data, tr.stats.sampling_rate, paz_remove=None,
                          pre_filt=(fl1, fl2, fl3, fl4),
                          seedresp=seedresp, taper_fraction=0.1,
                          pitsasim=False, sacsim=True)
        tr.data *= 1e9
    elif instype == 'pz':
        if sdb.rec[ne][ns].pz_fname == '':
            if DEBUG:
                print "response file not found"
            return
        attach_paz(tr, sdb.rec[ne][ns].pz_fname, tovel=True)
        tr.data = seisSim(tr.data, tr.stats.sampling_rate,
                          paz_remove=tr.stats.paz, remove_sensitivity=False,
                          pre_filt=(fl1, fl2, fl3, fl4))
    if filter:
        tr.detrend('linear')
        tr.detrenc('dmean')
        tr.filter('bandpass', freqmin=fl2, freqmax=fl3, zerophase=True,
                  corners=4)
    tr.write(sdb.rec[ne][ns].ft_fname + '_tmp', format='SAC')
    cut(sdb, ne, ns, t1, nos)
    sdb.rec[ne][ns].dt = delta
    sdb.rec[ne][ns].n = int(round(nos / delta))


if __name__ == "__main__":
    try:
        if string.find(sys.argv[1], '-c') != -1:
            cnffile = sys.argv[2]
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception, e:
        cnffile = 'config.txt'
        print e

    if not os.path.isfile(cnffile):
        print "config file %s not found" % cnffile
        sys.exit(1)

    conf = SafeConfigParser()
    conf.read(cnffile)
    t1 = int(conf.get("rm_resp", "start_t"))
    nos = int(conf.get("rm_resp", "npts"))
    rmopt = int(conf.get("rm_resp", "rm_opt"))
    tmpdir = conf.get("rm_resp", "tmpdir")
    dbname = conf.get("rm_resp", "dbname")
    delta = float(conf.get("rm_resp", "sampling"))
    plow = float(conf.get("rm_resp", "plow"))
    phigh = float(conf.get("rm_resp", "phigh"))
    force = bool(conf.get("rm_resp", "force"))
    if rmopt == 0:
        instype = 'pz'
        rminst = True
        filt = False
    if rmopt == 1:
        instype = 'resp'
        rminst = True
        filt = False
    if rmopt == 2:
        instype = 'resp'
        rminst = False
        filt = True
    if rmopt == 3:
        instype = 'resp'
        rminst = False
        filt = False

    sdbf = os.path.join(tmpdir, dbname)
    sdb = sac_db.read_db(sdbf)
    if not DEBUG:
        widgets = ['rm_inst: ', pg.Percentage(), ' ', pg.Bar('#'),
                   ' ', pg.ETA()]
        pbar = pg.ProgressBar(widgets=widgets, maxval=sdb.nev).start()

    for ne in xrange(sdb.nev):
        if not DEBUG:
            pbar.update(ne)
        for ns in xrange(sdb.nst):
            rm_inst(sdb, ne, ns, rminst=rminst, instype=instype, \
                    plow=plow, phigh=phigh, t1=t1, nos=nos,
                    filter=filt, force=force)
    sac_db.write_db(sdb, sdbf)
    if not DEBUG:
        pbar.finish()
