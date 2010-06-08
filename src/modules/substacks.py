#!/usr/bin/env mypython
"""
make substacks in order to calculate error of ftan method
"""

import os, os.path, sys, string
import glob, time, bisect, logging
import pylab as plb
import shutil, math, re
import numpy as np
import array as a
import delaz as dz
import pysacio as p
from ConfigParser import SafeConfigParser
import progressbar as pg

class PAR: pass

def add2dict(mydict,astr,f,log,rev=False,newentry=False):
    [hf,hi,hs,seis,ok] = p.ReadSacFile(f)
    if not ok:
        log.error("ERROR: cannot read sac-file %s" %(f))
        return 1
    trace = np.array(seis, dtype=float)
    ### check if trace has values other than 'nan'
    if np.all(np.isnan(trace)):
        log.error('no data for %s'%f)
        return 1
    if newentry:
        mydict[astr] = {}
        mydict[astr]['trace'] = trace
        mydict[astr]['hf']    = hf
        mydict[astr]['hs']    = hs
        mydict[astr]['hi']    = hi
        mydict[astr]['fn']    = os.path.basename(f)
        return 1
        
    nstack = p.GetHvalue('mag',hf,hi,hs)
    oldtrace = np.array(mydict[astr]['trace'], dtype=float)
    if rev==True:
        newtrace = oldtrace+trace[::-1]
    else:
        newtrace = oldtrace+trace
    if len(newtrace) > 0:
        oldstack = p.GetHvalue('mag',mydict[astr]['hf'],mydict[astr]['hi'],
                               mydict[astr]['hs'])
        newstack = nstack+oldstack
        p.SetHvalue('mag',newstack,hf,hi,hs)
        new = {}
        new[astr] = {}
        new[astr]['trace'] = newtrace
        new[astr]['hf'] = hf
        new[astr]['hs'] = hs
        new[astr]['hi'] = hi
        new[astr]['fn'] = os.path.basename(f)
        mydict.update(new)
        return 1
    else: return 0


def ls(par,dirname,filelist):
    flist = glob.glob(os.path.join(dirname,par.pattern))
    if len(flist) > 0:
        a = os.path.basename(os.path.dirname(flist[0]))
        date = time.strptime(a,'%Y_%m_%d_0_0_0')
        sec = time.mktime(date)
        par.list.append((flist,sec))


def mklist(pattern,datadir):
    par = PAR()
    par.pattern = pattern
    par.list = []
    # get all COR-files
    os.path.walk(datadir,ls,par)
    # sort them according to their date
    a = []
    for i in par.list:
        bisect.insort(a,(i[1],i))
    return a


def write_stack(stackdir,mystack,nsub):
    """write contents of global 'COR'-file dict to disk"""
    if not os.path.isdir(stackdir):
        os.makedirs(stackdir)
    for stat in mystack.keys():
        # write stacked correlation
        seis = mystack[stat]['trace']
        hf = mystack[stat]['hf']
        hs = mystack[stat]['hs']
        hi = mystack[stat]['hi']
        stat1, stat2 = stat.split('_')
        p.SetHvalue('kevnm',stat1, hf,hi,hs)
        p.SetHvalue('kstnm',stat2, hf,hi,hs)
        b = p.GetHvalue('b',hf,hi,hs)
        lat1 = p.GetHvalue('evla',hf,hi,hs)
        lon1 = p.GetHvalue('evlo',hf,hi,hs)
        lat2 = p.GetHvalue('stla',hf,hi,hs)
        lon2 = p.GetHvalue('stlo',hf,hi,hs)
        dist, dump1, dump2 = dz.delaz(lat1,lon1,lat2,lon2,0)
        dist = dist*math.pi*6372/180
        p.SetHvalue('dist',dist,hf,hi,hs)
        delta = p.GetHvalue('delta',hf,hi,hs)
        null = -1*b/delta
        reversed = seis[::-1]
        newseis = seis+reversed
        p.SetHvalue('npts',len(newseis[null:]),hf,hi,hs)
        p.SetHvalue('b',0,hf,hi,hs)
        p.SetHvalue('o',0, hf,hi,hs)
        outputfile = stackdir+'/'+mystack[stat]['fn']+'_err_'+str(nsub)
        p.WriteSacBinary(outputfile, hf, hi, hs, a.array('f',newseis[null:]))


def substack(corfiles,spattern,stackdir,log,stackl,shift):
    cnt = 0
    nsub = 0
    while cnt < (len(corfiles)-stackl):
        mystack = {}
        for no in range(cnt,min(cnt+stackl,len(corfiles))):
            for f in corfiles[no][1][0]:
                aa = os.path.basename(f).split('_')
                stat1 = aa[1]
                stat2 = aa[2].split('.SAC')[0]
                # account for the fact that the correlation could be
                # either COR_STAT1_STAT2.SAC or COR_STAT2_STAT1.SAC
                comb1=stat1+'_'+stat2
                comb2=stat2+'_'+stat1
                if comb1 in mystack.keys():
                    if add2dict(mystack,comb1,f,log): continue
                    return -1
                elif comb2 in mystack.keys():
                    if add2dict(mystack,comb2,f,log,rev=True): continue
                    return -1
                else:
                    if add2dict(mystack,comb1,f,log,newentry=True): continue
                    return -1
                    continue
        write_stack(stackdir,mystack,nsub)
        nsub = nsub + 1
        cnt  = cnt + shift 
    return 1


if __name__ == '__main__':

    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            datdir   = cp.get('daterr','cordir')
            stackdir = cp.get('daterr','stackdir')
            spattern = cp.get('daterr','spattern')
            tmpdir   = cp.get('daterr','tmpdir')
            skipdir  = cp.get('daterr','skip_directories')
            stackl   = int(cp.get('daterr','stack_length'))
            shift    = int(cp.get('daterr','shift'))
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "no configuration file found"
        sys.exit(1)
        
    ######## setup logging ################
    DBG_FILENAME = tmpdir+'/substack.log'
    ERR_FILENAME = tmpdir+'/substack.err'

    mylogger = logging.getLogger('MyLogger')
    mylogger.setLevel(logging.DEBUG)
    handlerdbg = logging.FileHandler(DBG_FILENAME,'w')
    handlererr = logging.FileHandler(ERR_FILENAME,'w')
    handlererr.setLevel(logging.ERROR)

    mylogger.addHandler(handlerdbg)
    mylogger.addHandler(handlererr)

    ########### set up progress bar ############################
    ### count files for progressbar
    tmppar = PAR()
    tmppar.cnt = 0
    def cntf(tmppar,dirname,files):
        flist = glob.glob(os.path.join(dirname,tmppar.pattern))
        if len(flist) > 0:
            tmppar.cnt = tmppar.cnt+1

    for tmppar.pattern in spattern.split(','):
        os.path.walk(datdir,cntf,tmppar)
    widgets = ['substacks: ', pg.Percentage(), ' ', pg.Bar('#'),
               ' ', pg.ETA()]
    pbar = pg.ProgressBar(widgets=widgets, maxval=tmppar.cnt).start()
    ############################################################

    cnt = 0
    for sp in spattern.split(','):
        al = mklist(sp,datdir)
        substack(al,sp,stackdir,mylogger,stackl,shift)
        cnt = cnt + len(al)
        pbar.update(cnt)
    pbar.finish()
