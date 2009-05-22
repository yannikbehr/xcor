#!/usr/local/bin/python

import os, os.path, sys
import glob, time, bisect
import pylab as plb
import shutil, math
import pysacio as p
import array
import delaz as dz

class PAR: pass

def ls(par,dirname,filelist):
    flist = glob.glob(dirname+'/'+par.pattern)
    if len(flist) == 1:
        a = os.path.basename(os.path.dirname(flist[0]))
        date = time.strptime(a,'%Y_%m_%d_0_0_0')
        sec = time.mktime(date)
        par.list.append((flist[0],sec))
    if len(flist) > 1:
        print "ERROR: found too many matching files!"
        print flist

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


def substack(a, shift, stackdir):
    cnt = 0
    pmax=0
    stack = plb.array([],dtype='float')
    nstack = 0
    nsub = 1
    while cnt < (len(a)-shift):
        for no in range(cnt,cnt+shift):
            [hf,hi,hs,seis,ok] = p.ReadSacFile(a[no][1][0])
            if not ok:
                print "ERROR: cannot read file %s!"%a[no][1][0]
                continue
            if len(stack)<1:
                stack=plb.array(seis,dtype=float)
                stack = plb.divide(stack,abs(stack).max())
                nstack = nstack + 1
            else:
                ntrace = plb.array(seis,dtype=float)
                ntrace = plb.divide(ntrace,abs(ntrace).max())
                stack = stack + ntrace
                nstack = nstack + 1
        delta = p.GetHvalue('delta',hf,hi,hs)
        b = p.GetHvalue('b',hf,hi,hs)
        null = -1*b/delta
        reversed = stack[::-1]
        newseis = stack+reversed
        p.SetHvalue('npts',len(newseis[null:]),hf,hi,hs)
        p.SetHvalue('b',0,hf,hi,hs)
        p.SetHvalue('o',0, hf,hi,hs)
        lat1 = p.GetHvalue('evla',hf,hi,hs)
        lon1 = p.GetHvalue('evlo',hf,hi,hs)
        lat2 = p.GetHvalue('stla',hf,hi,hs)
        lon2 = p.GetHvalue('stlo',hf,hi,hs)
        dist, dump1, dump2 = dz.delaz(lat1,lon1,lat2,lon2,0)
        dist = dist*math.pi*6372/180
        p.SetHvalue('dist',dist,hf,hi,hs)
        outfile = stackdir+'/'+os.path.basename(a[no][1][0])+'_'+str(nsub)
        p.WriteSacBinary(outfile,hf,hi,hs,array.array('f',newseis[null:]))
        cnt = cnt + 30
        stack = plb.array([],dtype='float')
        nstack = 0
        nsub = nsub + 1


if __name__ == '__main__':
    stat1 = 'WCZ'
    stat2 = 'TIKO'
    pattern = 'COR_'+stat1+'_'+stat2+'.SAC_rr'
    datdir  = '/data/sabine/yannik/Results/XCor/vertical/nord/daily'
    stackdir = '/data/sabine/yannik/Results/err_analysis/nord'
    shift = 100
    al = mklist(pattern,datdir)
    substack(al,shift,stackdir)

