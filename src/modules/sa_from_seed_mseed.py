#!/usr/bin/env python
"""extract mseed data from geonet download and put them into the right\n
directory structure together with their corresponding response files"""


import glob, os, string, sys, os.path, time, shutil
sys.path.append('/Users/home/yannik78/auto/src/modules/')
import pysacio as p
from ConfigParser import SafeConfigParser


altrespfile = '/Volumes/stage/stage/yannik78/nord-geonet/nz.dataless.seed.national'
seedrespdir = '/Volumes/stage/stage/yannik78/nord-geonet/respfiles/'
outputdir = 'sacfiles'
monthdict = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May', \
             6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct', \
             11:'Nov',12:'Dec'}


def resp_file_dict(dirname):
    respdict = {}
    for file in glob.glob(dirname+'/RESP*'):
        fn = os.path.basename(file)
        a  = string.split(fn,'.')
        if a[2] not in respdict.keys():
            respdict[a[2]] = {}
            respdict[a[2]][a[4]] = []
            respdict[a[2]][a[4]].append(file)
        elif a[4] not in respdict[a[2]].keys():
            respdict[a[2]][a[4]] = []
            respdict[a[2]][a[4]].append(file)
        else:
            respdict[a[2]][a[4]].append(file)
    return respdict

def mk_fn(stn, chan, d, sacdir):
    monstr = monthdict[d.tm_mon]
    ydir = sacdir+'/'+`d.tm_year`
    mdir = sacdir+'/'+`d.tm_year`+'/'+monstr
    ddir = sacdir+'/'+`d.tm_year`+'/'+monstr+'/'+\
           `d.tm_year`+'_'+`d.tm_mon`+'_'+`d.tm_mday`+'_0_0_0/'
    if not os.path.isdir(sacdir):
        print "ERROR: directory for sac-files doesn't exist"
        sys.exit(1)
    if not os.path.isdir(ydir):
        os.mkdir(ydir)
        print "---> creating dir ", ydir
    if not os.path.isdir(mdir):
        os.mkdir(mdir)
        print "---> creating dir ", mdir
    if not os.path.isdir(ddir):
        os.mkdir(ddir)
        print "---> creating dir ", ddir
    filename = ddir+'/'+stn+'.'+chan+'.SAC'
    return filename

def get_ms_cont(dir):
    listfiles = glob.glob(dir+'/*.SAC')
    stations = {}
    for file in listfiles:
        [hf,hi,hs,ok] = p.ReadSacHeader(file)
        if not ok:
            print "ERROR: cannot read in sac-header: ", file
        else:
            year = `p.GetHvalue('nzyear',hf,hi,hs)`
            yday = `p.GetHvalue('nzjday',hf,hi,hs)`
            stn  = p.GetHvalue('kstnm',hf,hi,hs).strip()
            chan = p.GetHvalue('kcmpnm',hf,hi,hs).strip()
            date = time.strptime(year+" "+yday,"%Y %j")
            if stn not in stations.keys():
                stations[stn] = {}
                stations[stn][chan] = []
                stations[stn][chan].append(file)
                stations[stn]['date'] = date
            elif chan not in stations[stn].keys():
                stations[stn][chan] = []
                stations[stn][chan].append(file)
                if stations[stn]['date'] != date:
                    print "WARNING: date differs between two files"
            else:
                stations[stn][chan].append(file)
    return stations


def merge_sac(filelist, outputfn):
    try:
        mergesaccmd = "/Users/home/yannik78/auto/src/merge_sac "+outputfn
        child = os.popen(mergesaccmd, 'w')
        for i in filelist:
            print >>child, i
        err = child.close()
        if err:
            raise RuntimeError, '%r failed with exit code %d' %(mergesaccmd, err)
    except Exception, e:
        print "ERROR: while merging sacfiles"
        return 0
    else:
        return 1
    

def cp_resp(stn, chan, sacfn):
    if len(resp_file_dict(seedrespdir)[stn][chan]) > 1:
        print "WARNING: there are several response files available"
    respfile = resp_file_dict(seedrespdir)[stn][chan][0]
    outdir = os.path.dirname(sacfn)
    target = os.path.join(outdir,os.path.basename(respfile))
    shutil.copy(respfile, target)
    print "--> cp ", respfile,' ', target
    
def proc_mseed(mseedir, rdseedir, sacdir):
    files = os.listdir(mseedir)
    for file in files:
        if os.path.isfile(mseedir+file):
            if not os.path.isdir(mseedir+outputdir):
                os.mkdir(mseedir+outputdir)
            command = rdseedir+'rdseed -f '+mseedir+file+' -g '+altrespfile+' -q '+\
                      mseedir+outputdir+' -o 1 -d 1>/dev/null 2>/dev/null '
            os.system(command)
            g = get_ms_cont(mseedir+outputdir)
            for i in g.keys():
                for j in g[i].keys():
                    if j != 'date':
                        filename = mk_fn(i,j,g[i]['date'], sacdir)
                        print "--> writing file ", filename
                        if merge_sac(g[i][j],filename):
                            cp_resp(i, j, filename)
                        for k in g[i][j]:
                            os.remove(k)


if __name__ == '__main__':
    cp = SafeConfigParser()
    config='./config.txt'
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
        else:
            print "config file is config.txt"
    except Exception:
        print "config file is config.txt"
    cp.read(config)
    bindir = cp.get('database','bindir')
    mseedir = cp.get('database','databasedir')
    rdseedir = cp.get('database','rdseeddir')
    sacdirroot = cp.get('database','sacdirroot')

    proc_mseed(mseedir, rdseedir, sacdirroot)
