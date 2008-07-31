#!/usr/bin/env python
"""extract mseed data from geonet download and put them into the right\n
directory structure together with their corresponding response files"""


import glob, os, string, sys, os.path, time, shutil
import subprocess as sp
import pysacio as p


class SaFromMseed:
    def __init__(self, dataless, respdir, outputdir, bindir, rdseedir):
        self.dataless  = dataless
        self.respdir   = respdir
        self.outputdir = outputdir
        self.bindir    = bindir
        self.rdseedir  = rdseedir
        self.monthdict = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May', \
                          6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct', \
                          11:'Nov',12:'Dec'}

    def __call__(self, mseedir, sacdiroot):
        self.proc_mseed(mseedir, sacdirroot)



    def resp_file_dict(self, dirname):
        """create a dictionary from all responsefiles in 'dirname'"""
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
    

    def mk_fn(self, stn, chan, d, sacdir):
        """construct filename out of station-, channel-, date-info"""
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
    

    def get_ms_cont(self, dir):
        """get info about extracted sacfiles from sac-file header"""
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
    
    
    def merge_sac(self, filelist, outputfn):
        """run c-code to merge several sac-files of the same day into
        one big sac-file"""
        try:
            mergesaccmd = self.bindir+"merge_sac "+outputfn
            p = sp.Popen(mergesaccmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
            child = p.stdin
            for i in filelist:
                print >>child, i
            err = child.close()
            rcode = p.wait()
            if err or rcode != 0:
                raise RuntimeError, '%r failed with exit code %d' %(mergesaccmd, err)
        except Exception, e:
            print "ERROR: while merging sacfiles"
            return 0
        else:
            return 1
        
    
    def cp_resp(self, stn, chan, sacfn):
        """copy response file for station(stn) channel(chan) to
        appropriate location"""
        if len(self.resp_file_dict(seedrespdir)[stn][chan]) > 1:
            print "WARNING: there are several response files available"
        respfile = self.resp_file_dict(seedrespdir)[stn][chan][0]
        outdir = os.path.dirname(sacfn)
        target = os.path.join(outdir,os.path.basename(respfile))
        shutil.copy(respfile, target)
        print "--> cp ", respfile,' ', target
        
    
    def proc_mseed(self, mseedir, sacdir):
        """main function to process mseed files"""
        files = os.listdir(mseedir)
        for file in files:
            if os.path.isfile(mseedir+file):
                if not os.path.isdir(mseedir+outputdir):
                    os.mkdir(mseedir+outputdir)
                command = self.rdseedir+'rdseed -f '+mseedir+file+' -g '+self.dataless+' -q '+\
                          mseedir+self.outputdir+' -o 1 -d 1>/dev/null 2>/dev/null '
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
    
    rdseedir = '/home/behrya/src/rdseed4.7.5/'
    bindir   = '/home/behrya/dev/auto/bin/'
    mseedir  = '/Volumes/stage/stage/yannik78/datasets/geonet/geonet_xcorr/2005/'
    sacdir   = './testsac/'
    dataless = '/Volumes/stage/stage/yannik78/nord-geonet/nz.dataless.seed.national'
    respdir = '/Volumes/stage/stage/yannik78/nord-geonet/respfiles/'
    outputdir = 'sacfiles'

    t = SaFromMseed(dataless, respdir, outputdir, bindir, rdseedir)
    t(mseedir, sacdir)
