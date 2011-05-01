#!/usr/bin/env mypython
"""
Remove instrument response using sac and cut precisely.

"""

import os, os.path, sys, glob
from subprocess import *
from obspy.sac import *
import sac_db
from numpy import *
from ConfigParser import SafeConfigParser
import progressbar as pg

DEBUG = False

def abs_time(yy,jday,hh,mm,ss,ms):
    nyday = 0
    for i in range(1901,yy):
        if i%4 == 0:
            nyday = nyday + 366
        else:
            nyday = nyday + 365
    return 24.*3600.*(nyday+jday) + 3600.*hh + 60.*mm + ss + 0.001*ms



def cut(sdb,ne,ns,t1,nos):
    """
    cut traces precisely
    """
    fin  = sdb.rec[ne][ns].ft_fname+'_tmp'
    fout = sdb.rec[ne][ns].ft_fname
    if DEBUG:
        print fin
        print fout
    p = ReadSac(fin)
    dt   = p.GetHvalue('delta')
    npts = p.GetHvalue('npts')
    yy   = p.GetHvalue('nzyear')
    jday = p.GetHvalue('nzjday')
    hh   = p.GetHvalue('nzhour')
    mm   = p.GetHvalue('nzmin')
    ss   = p.GetHvalue('nzsec')
    ms   = p.GetHvalue('nzmsec')
    b    = p.GetHvalue('b')
    ### correct for milli-seconds in trace by linear interpolation
    tb   = sdb.rec[ne][ns].t0
    te   = sdb.ev[ne].t0
    t2   = t1 + (nos-1)
    t1b  = tb-te
    t1e  = t1b + (npts-1)*dt
    if t1b>t1 or t1e<t2 or t1e > 100000/dt:
        #print "ERROR: incompatible time limits for %s; cannot cut"%(fin)
        return
    if ms > 0.:
        frac = (int((0.001*ms+dt)/dt)*dt-0.001*ms)/dt
        #1./dt-0.001*ms/dt
        p.seis = p.seis[0:npts-1]+frac*diff(p.seis)
        ### round to next higher increment of dt
        #t0 = round(tb+frac*dt,-int(log10(dt)))
        t0 = tb+frac*dt
    else:
        t0 = tb
    istart = int(round(t1/dt))
    ibegin = int(round((t0-te)/dt))
    n = int(round(nos/dt))
    n1 = istart-ibegin
    p.SetHvalue("npts",n)
    p.SetHvalue("nzyear",2000)
    p.SetHvalue("nzjday",1)
    p.SetHvalue("nzhour",0)
    p.SetHvalue("nzmin",0)
    p.SetHvalue("nzsec",0)
    p.SetHvalue("nzmsec",0)
    p.SetHvalue("b",0.)
    p.seis = p.seis[n1:n1+n]
    p.WriteSacBinary(fout)
    os.remove(fin)


def rm_inst(sdb,ne,ns,delta=1.0,rminst=True,filter=False,instype='resp',
            plow=160.,phigh=4.,sacbin = '/usr/local/sac/bin/sac',
            t1=1000,nos=84000):
    """
    downsample traces, remove mean, trend, cut them to the exact same
    time window, and either remove instrument response, filter, or leave
    them as they are
    """
    fl1=1.0/(plow+0.0625*plow)
    fl2=1.0/plow
    fl3=1.0/phigh
    fl4=1.0/(phigh-0.25*phigh)
    if sdb.rec[ne][ns].fname == '':return
    if os.path.isfile(sdb.rec[ne][ns].ft_fname):return
    if DEBUG:
        p = Popen(sacbin,shell=True,stdin=PIPE)
    else:
        p = Popen(sacbin+' 2>/dev/null 1>/dev/null',shell=True,stdin=PIPE)
    cd1 = p.stdin
    print >>cd1, "r %s"%sdb.rec[ne][ns].fname
    print >>cd1, "rmean"
    print >>cd1, "rtrend"
    print >>cd1, "interpolate delta %f "%delta
    if rminst:
        if instype == 'resp':
            if sdb.rec[ne][ns].resp_fname == '':
                print >>cd1, "quit"
                if DEBUG:
                    print "response file not found"
                return
            print >>cd1, "transfer from evalresp fname %s to vel freqlimits\
            %f %f %f %f"%(sdb.rec[ne][ns].resp_fname,fl1,fl2,fl3,fl4)
        elif instype == 'pz':
            if sdb.rec[ne][ns].pz_fname == '':
                print >>cd1, "quit"
                if DEBUG:
                    print "response file not found"
                return
            print >>cd1, "transfer from polezero subtype %s to vel freqlimits\
            %f %f %f %f"%(sdb.rec[ne][ns].pz_fname,fl1,fl2,fl3,fl4)
            print >>cd1, "mul 1.0e+9" ## needed to convert m to nm (see SAC manual)
        else:
            if DEBUG:
                print "instrument type has to be either 'resp' or 'pz'"
                return
            else:
                pass
    if filter:
        print >>cd1,"bandpass npoles 4 corner %f %f"%(fl2,fl3)
    print >>cd1, "w %s"%(sdb.rec[ne][ns].ft_fname+'_tmp')
    print >>cd1, "quit"
    cd1.close()
    p.wait()
    cut(sdb,ne,ns,t1,nos)
    sdb.rec[ne][ns].dt = delta
    sdb.rec[ne][ns].n  = int(round(nos/delta))


if __name__ == "__main__":
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            cnffile=sys.argv[2]
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        cnffile = 'config.txt' 

    if not os.path.isfile(cnffile):
        print "no config file found"
        sys.exit(1)

    conf = SafeConfigParser()
    conf.read(cnffile)
    sacbin = conf.get("rm_resp","sacbin");
    t1     = int(conf.get("rm_resp","start_t"))
    nos    = int(conf.get("rm_resp","npts"))
    rmopt  = int(conf.get("rm_resp","rm_opt"))
    tmpdir = conf.get("rm_resp","tmpdir")
    dbname = conf.get("rm_resp","dbname")
    delta  = float(conf.get("rm_resp","sampling"))
    plow   = float(conf.get("rm_resp","plow"))
    phigh  = float(conf.get("rm_resp","phigh"))
    if rmopt == 0:
        instype = 'pz'
        rminst  = True
        filt    = False
    if rmopt == 1:
        instype = 'resp'
        rminst  = True
        filt    = False
    if rmopt == 2:
        instype = 'resp'
        rminst = False
        filt   = True

    if rmopt == 3:
        instype = 'resp'
        rminst  = False
        filt    = False

    if not os.access('/usr/local/sac101.3b/bin/sac',os.X_OK):
        print "Cannot find executable sac-binary"
        sys.exit(1)
    sdbf = os.path.join(tmpdir,dbname)
    sdb = sac_db.read_db(sdbf)
    if not DEBUG:
        widgets = ['rm_inst: ', pg.Percentage(), ' ', pg.Bar('#'),
                   ' ', pg.ETA()]
        pbar = pg.ProgressBar(widgets=widgets, maxval=sdb.nev).start()
    
    for ne in xrange(sdb.nev):
        if not DEBUG:
            pbar.update(ne)
        for ns in xrange(sdb.nst):
            rm_inst(sdb,ne,ns,delta=delta,rminst=rminst,instype=instype,\
                    plow=plow,phigh=phigh,sacbin=sacbin,\
                    t1=t1,nos=nos,filter=filt)
    sac_db.write_db(sdb,sdbf)
    if not DEBUG:
        pbar.finish()
