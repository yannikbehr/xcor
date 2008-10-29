#!/usr/bin/env python
"""script to stack horizontal component cross-correlation results"""

import numpy as np
import array as a
import pysacio as p
import os.path, glob, re, sys, string, math
from ConfigParser import SafeConfigParser
sys.path.append('/home/behrya/dev/proc-scripts')
import delaz as dz

mystack = {}
pattern = r'COR_(\w*_\w*).SAC'

def find_match(f):
    match = re.search(pattern,f)
    if match:
        [hf,hi,hs,seis,ok] = p.ReadSacFile(f)
        if not ok:
            print "ERROR: cannot read sac-file %s" %(f)
            return -1
        else:
            trace = np.array(seis, dtype=float)
            if match.group(1) in mystack.keys():
                oldtrace = np.array(mystack[match.group(1)]['trace'], dtype=float)
                newtrace = oldtrace+trace
                if len(newtrace) > 0:
                    new = {}
                    new[match.group(1)] = {}
                    new[match.group(1)]['trace'] = newtrace
                    new[match.group(1)]['hf'] = hf
                    new[match.group(1)]['hs'] = hs
                    new[match.group(1)]['hi'] = hi
                    mystack.update(new)
                    return 1
                else: return -1
            else:
                mystack[match.group(1)] = {}
                mystack[match.group(1)]['trace'] = trace
                mystack[match.group(1)]['hf'] = hf
                mystack[match.group(1)]['hs'] = hs
                mystack[match.group(1)]['hi'] = hi
                return 1
    else:
        return 0
    
def find_xcor(arg, dirname, files):
    corfiles = glob.glob(dirname+'/COR*')
    if len(corfiles) > 0:
        for f in corfiles:
            find_match(f)

if __name__ == '__main__':

    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            rootdir  = cp.get('stack','cordir')
            stackdir = cp.get('stack','stackdir')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "no configuration file found"
        sys.exit(1)

    os.path.walk(rootdir, find_xcor, None)
    if not os.path.isdir(stackdir):
        os.mkdir(stackdir)
    for stat in mystack.keys():
        #print mystack[stat]
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
        outputfile = stackdir+'/COR_'+stat+'.SAC'
        print 'writing',outputfile
        p.WriteSacBinary(outputfile, hf, hi, hs, a.array('f',seis))

        # write causal part only
        delta = p.GetHvalue('delta',hf,hi,hs)
        null = -1*b/delta
        reversed = seis[-1::-1]
        newseis = seis+reversed
        p.SetHvalue('npts',len(newseis[null:]),hf,hi,hs)
        p.SetHvalue('b',0,hf,hi,hs)
        p.SetHvalue('o',0, hf,hi,hs)
        outputfile = stackdir+'/COR_'+stat+'.SAC_s'
        print 'writing',outputfile
        p.WriteSacBinary(outputfile, hf, hi, hs, a.array('f',newseis[null:]))
