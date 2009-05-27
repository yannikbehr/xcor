#!/usr/local/bin/python

import os, os.path, sys, string
import glob, time, bisect, logging
import pylab as plb
import shutil, math
import pysacio as p
import array
import delaz as dz
from ConfigParser import SafeConfigParser

class PAR: pass

def add2dict(mydict,astr,f,log,rev=False):
    [hf,hi,hs,seis,ok] = p.ReadSacFile(f)
    if not ok:
        log.error("ERROR: cannot read sac-file %s" %(f))
        return 0
    trace = np.array(seis, dtype=float)
    ### check if trace has values other than 'nan'
    if np.all(np.isnan(trace)):
        log.error('no data for %s'%f)
        return 0
    nstack = p.GetHvalue('mag',hf,hi,hs)
    oldtrace = np.array(mydict[astr]['trace'], dtype=float)
    if rev=True:
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
        mydict.update(new)
        return 1
    else return 0



def ls(par,dirname,filelist):
    flist = glob.glob(dirname+'/'+par.pattern)
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


def substack(corfiles,spattern,mystack,log):
    for f in corfiles:
        match = re.search(spattern,f)
        if match:
            stat1 = match.group(1)
            stat2 = match.group(2)
            # account for the fact that the correlation could be
            # either COR_MATA_TIKO.SAC or COR_TIKO_MATA.SAC
            comb1=stat1+'_'+stat2
            comb2=stat2+'_'+stat1
            if comb1 in mystack.keys():
                if add2dict(mystack,comb1,f,log): continue
                return -1
            elif comb2 in mystack.keys():
                if add2dict(mystack,comb2,f,log,rev=True): continue
                return -1
            else:
                mystack[comb1] = {}
                mystack[comb1]['trace'] = trace
                mystack[comb1]['hf']    = hf
                mystack[comb1]['hs']    = hs
                mystack[comb1]['hi']    = hi
                continue

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

    al = mklist(spattern,datdir)
    substack(al,shift,stackl,stackdir)



#def substack(a, shift, stackl, stackdir):
#    cnt = 0
#    pmax=0
#    stack = plb.array([],dtype='float')
#    nstack = 0
#    nsub = 1
#    while cnt < (len(a)-stackl):
#        for no in range(cnt,cnt+stackl):
#            [hf,hi,hs,seis,ok] = p.ReadSacFile(a[no][1][0])
#            if not ok:
#                print "ERROR: cannot read file %s!"%a[no][1][0]
#                continue
#            if len(stack)<1:
#                stack=plb.array(seis,dtype=float)
#                stack = plb.divide(stack,abs(stack).max())
#                nstack = nstack + 1
#            else:
#                ntrace = plb.array(seis,dtype=float)
#                ntrace = plb.divide(ntrace,abs(ntrace).max())
#                stack = stack + ntrace
#                nstack = nstack + 1
#        delta = p.GetHvalue('delta',hf,hi,hs)
#        b = p.GetHvalue('b',hf,hi,hs)
#        null = -1*b/delta
#        reversed = stack[::-1]
#        newseis = stack+reversed
#        p.SetHvalue('npts',len(newseis[null:]),hf,hi,hs)
#        p.SetHvalue('b',0,hf,hi,hs)
#        p.SetHvalue('o',0, hf,hi,hs)
#        lat1 = p.GetHvalue('evla',hf,hi,hs)
#        lon1 = p.GetHvalue('evlo',hf,hi,hs)
#        lat2 = p.GetHvalue('stla',hf,hi,hs)
#        lon2 = p.GetHvalue('stlo',hf,hi,hs)
#        dist, dump1, dump2 = dz.delaz(lat1,lon1,lat2,lon2,0)
#        dist = dist*math.pi*6372/180
#        p.SetHvalue('dist',dist,hf,hi,hs)
#        outfile = stackdir+'/'+os.path.basename(a[no][1][0])+'_'+str(nsub)
#        p.WriteSacBinary(outfile,hf,hi,hs,array.array('f',newseis[null:]))
#        cnt = cnt + shift
#        stack = plb.array([],dtype='float')
#        nstack = 0
#        nsub = nsub + 1
