#!/usr/bin/env python
"""script to stack horizontal component cross-correlation results"""

import numpy as np
import array as a
import pysacio as p
import os.path, glob, re, sys, string, math
from ConfigParser import SafeConfigParser
sys.path.append('/home/behrya/dev/proc-scripts')
import delaz as dz
import logging

class PAR: pass

def find_match(par,dirname,filelist):
    """find 'COR'-files in 'dirname' and add them to global dict of 'COR'-files """
    for dn in par.skipdir:
        try:
            i = filelist.index(dn)
            del filelist[i]
        except: pass

    print '... in %s'%dirname
    corfiles = glob.glob(dirname+'/COR*')
    if len(corfiles) > 0:
        for f in corfiles:
            match = re.search(par.spattern,f)
            if match:
                [hf,hi,hs,seis,ok] = p.ReadSacFile(f)
                if not ok:
                    par.log.error("ERROR: cannot read sac-file %s" %(f))
                    return -1
                trace = np.array(seis, dtype=float)
                ### check if trace has values other than 'nan'
                if np.all(np.isnan(trace)):
                    par.log.error('no data for %s'%f)
                    continue
                nstack = p.GetHvalue('mag',hf,hi,hs)
                stat1 = match.group(1)
                stat2 = match.group(2)
                # account for the fact that the correlation could be
                # either COR_MATA_TIKO.SAC or COR_TIKO_MATA.SAC
                comb1=stat1+'_'+stat2
                comb2=stat2+'_'+stat1
                if comb1 in par.mystack.keys():
                    oldtrace = np.array(par.mystack[comb1]['trace'], dtype=float)
                    newtrace = oldtrace+trace
                    if len(newtrace) > 0:
                        oldstack = p.GetHvalue('mag',par.mystack[comb1]['hf'],par.mystack[comb1]['hi'],
                                               par.mystack[comb1]['hs'])
                        newstack = nstack+oldstack
                        p.SetHvalue('mag',newstack,hf,hi,hs)
                        new = {}
                        new[comb1] = {}
                        new[comb1]['trace'] = newtrace
                        new[comb1]['hf'] = hf
                        new[comb1]['hs'] = hs
                        new[comb1]['hi'] = hi
                        par.mystack.update(new)
                        continue
                    else: return -1
                elif comb2 in par.mystack.keys():
                    oldtrace = np.array(par.mystack[comb2]['trace'], dtype=float)
                    newtrace = oldtrace+trace[::-1]
                    if len(newtrace) > 0:
                        oldstack = p.GetHvalue('mag',par.mystack[comb2]['hf'],par.mystack[comb2]['hi'],
                                               par.mystack[comb2]['hs'])
                        newstack = nstack+oldstack
                        p.SetHvalue('mag',newstack,hf,hi,hs)
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
                    par.mystack[comb1]['hf']    = hf
                    par.mystack[comb1]['hs']    = hs
                    par.mystack[comb1]['hi']    = hi
                    continue

    return 0


def write_stack(stackdir,par):
    """write contents of global 'COR'-file dict to disk"""
    if not os.path.isdir(stackdir):
        os.mkdir(stackdir)
    for stat in par.mystack.keys():
        # write stacked correlation
        seis = par.mystack[stat]['trace']
        hf = par.mystack[stat]['hf']
        hs = par.mystack[stat]['hs']
        hi = par.mystack[stat]['hi']
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
        try:
            app = par.spattern.split('.SAC')[1][0:-1]
        except:
            app = ''
        outputfile = stackdir+'/COR_'+stat+'.SAC'+app
        #print 'writing',outputfile
        p.WriteSacBinary(outputfile, hf, hi, hs, a.array('f',seis))

        # write symmetric part 
        delta = p.GetHvalue('delta',hf,hi,hs)
        null = -1*b/delta
        reversed = seis[::-1]
        newseis = seis+reversed
        p.SetHvalue('npts',len(newseis[null:]),hf,hi,hs)
        p.SetHvalue('b',0,hf,hi,hs)
        p.SetHvalue('o',0, hf,hi,hs)
        outputfile = stackdir+'/COR_'+stat+'.SAC'+app+'_s'
        #print 'writing',outputfile
        p.WriteSacBinary(outputfile, hf, hi, hs, a.array('f',newseis[null:]))


if __name__ == '__main__':

    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            rootdir  = cp.get('stack','cordir')
            stackdir = cp.get('stack','stackdir')
            spattern = cp.get('stack','spattern')
            tmpdir   = cp.get('stack','tmpdir')
            skipdir  = cp.get('stack','skip_directories')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "no configuration file found"
        sys.exit(1)
        
    ######## setup logging ################
    DBG_FILENAME = tmpdir+'/stack.log'
    ERR_FILENAME = tmpdir+'/stack.err'

    mylogger = logging.getLogger('MyLogger')
    mylogger.setLevel(logging.DEBUG)
    handlerdbg = logging.FileHandler(DBG_FILENAME,'w')
    handlererr = logging.FileHandler(ERR_FILENAME,'w')
    handlererr.setLevel(logging.ERROR)

    mylogger.addHandler(handlerdbg)
    mylogger.addHandler(handlererr)


    for sp in spattern.split(','):
        par          = PAR()
        par.mystack  = {}
        par.spattern = sp
        par.skipdir  = skipdir.split(',')
        par.log      = mylogger
        print 'searching for files matching %s'%sp
        os.path.walk(rootdir, find_match, par)
        print 'writing stacks to %s'%stackdir
        write_stack(stackdir,par)
