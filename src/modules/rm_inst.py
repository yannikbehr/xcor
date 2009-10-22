#!/usr/local/bin/python
"""
play around with removing instrument response
"""
import os, os.path, sys, glob
from subprocess import *
from obspy.sac import *
import sac_db
from numpy import *
from ConfigParser import SafeConfigParser


def cut(sdb,ne,ns,t1,nos):
    fin  = sdb.rec[ne][ns].ft_fname+'_tmp'
    fout = sdb.rec[ne][ns].ft_fname
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
        print "ERROR: incompatible time limits for %s; cannot cut"%(fin)
        return
    if ms > 0.:
        frac = 1./dt-0.001*ms/dt
        p.seis = p.seis[0:npts-1]+frac*diff(p.seis)
        ### round to next higher increment of dt
        t0 = round(tb+frac*dt,-int(log10(dt)))
    else:
        t0 = tb
    istart = int(t1/dt)
    ibegin = int((t0-te)/dt)
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

def rm_inst(sdbf,delta=1.0,rminst=True,instype='resp',
            plow=160.,phigh=4.,sacbin = '/usr/local/sac/bin/sac',
            t1=1000,nos=84000):
    sdb = sac_db.read_db(sdbf)
    for ne in xrange(sdb.nev):
        for ns in xrange(sdb.nst):
            fl1=1.0/(plow+0.0625*plow)
            fl2=1.0/plow
            fl3=1.0/phigh
            fl4=1.0/(phigh-0.25*phigh)
            p = Popen([sacbin],stdin=PIPE)
            cd1 = p.stdin
            print sdb.rec[ne][ns].fname
            print >>cd1, "r %s"%sdb.rec[ne][ns].fname
            print >>cd1, "rmean"
            print >>cd1, "rtrend"
            print >>cd1, "interpolate delta %f "%delta
            if rminst:
                if instype == 'resp':
                    print >>cd1, "transfer from evalresp fname %s to vel freqlimits\
                    %f %f %f %f"%(sdb.rec[ne][ns].resp_fname,fl1,fl2,fl3,fl4)
                if instype == 'pz':
                    print >>cd1, "transfer from polezero subtype %s to vel freqlimits\
                    %f %f %f %f"%(sdb.rec[ne][ns].pz_fname,fl1,fl2,fl3,fl4)
            else:
                print >>cd1,"bandpass npoles 4 corner %f %f"%(fl2,fl3)
            print >>cd1, "w %s"%(sdb.rec[ne][ns].ft_fname+'_tmp')
            print >>cd1, "quit"
            cd1.close()
            p.wait()
            cut(sdb,ne,ns,t1,nos)


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
    sacdir = conf.get("rm_resp","sacdir");
    t1     = int(conf.get("rm_resp","start_t"))
    nos    = int(conf.get("rm_resp","npts"))
    rmopt  = int(conf.get("rm_resp","rm_opt"))
    sacdb  = conf.get("rm_resp","sacdb")
    delta  = float(conf.get("rm_resp","sampling"))
    plow   = float(conf.get("rm_resp","plow"))
    phigh  = float(conf.get("rm_resp","phigh"))
    if rmopt == 0:
        instype = 'pz'
        rminst  = True
    if rmopt == 1:
        instype = 'resp'
        rminst  = True
    if rmopt == 3:
        instype = 'resp'
        rminst = False
        

    rm_inst(sacdb,delta=delta,rminst=rminst,instype=instype,\
            plow=plow,phigh=phigh,sacbin=os.path.join(sacdir,'sac'),\
            t1=t1,nos=nos)
