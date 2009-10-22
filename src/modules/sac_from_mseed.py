#!/usr/bin/env python
"""extract mseed data from geonet download and put them into the right\n
directory structure together with their corresponding response files"""


import glob, os, string, sys, os.path, time, shutil
import subprocess as sp
import pysacio as p
from ConfigParser import SafeConfigParser
import progressbar as pg

DEBUG = False

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


    def __call__(self, mseedir, sacdiroot, spat):
        self.proc_mseed(mseedir, sacdiroot, spat)



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
        monstr = self.monthdict[d.tm_mon]
        #ydir = sacdir+'/'+`d.tm_year`
        #mdir = sacdir+'/'+`d.tm_year`+'/'+monstr
        ddir = sacdir+'/'+`d.tm_year`+'/'+monstr+'/'+\
               `d.tm_year`+'_'+`d.tm_mon`+'_'+`d.tm_mday`+'_0_0_0/'
        if not os.path.isdir(ddir):
            os.makedirs(ddir)
        #if not os.path.isdir(sacdir):
        #    print "ERROR: directory for sac-files doesn't exist"
        #    sys.exit(1)
        #if not os.path.isdir(ydir):
        #    os.mkdir(ydir)
        #    if DEBUG:
        #        print "---> creating dir ", ydir
        #if not os.path.isdir(mdir):
        #    os.mkdir(mdir)
        #    if DEBUG:
        #        print "---> creating dir ", mdir
        #if not os.path.isdir(ddir):
        #    os.mkdir(ddir)
        #    if DEBUG:
        #        print "---> creating dir ", ddir
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
            mergesaccmd = os.path.join(self.bindir,"merge_sac")+" "+outputfn+" 2>/dev/null 1>/dev/null"
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
        if len(self.resp_file_dict(self.respdir)[stn][chan]) > 1:
            print "WARNING: there are several response files available"
        respfile = self.resp_file_dict(self.respdir)[stn][chan][0]
        outdir = os.path.dirname(sacfn)
        target = os.path.join(outdir,os.path.basename(respfile))
        shutil.copy(respfile, target)
        if DEBUG:
            print "--> cp ", respfile,' ', target
        
    
    def proc_mseed(self, mseedir, sacdir, spat):
        """main function to process mseed files"""
        if DEBUG:
            print "searching for pattern %s"%os.path.join(mseedir,spat)
        files = glob.glob(os.path.join(mseedir,spat))
        cnt = 0
        if not DEBUG:
            widgets = ['mSEED2sac: ', pg.Percentage(), ' ', pg.Bar('#'),
                            ' ', pg.ETA()]
            pbar = pg.ProgressBar(widgets=widgets, maxval=len(files)).start()
        for fn in files:
            if DEBUG:
                print fn
            else:
                cnt +=1
                pbar.update(cnt)

            if os.path.isfile(fn):
                if not os.path.isdir(mseedir+self.outputdir):
                    os.mkdir(mseedir+self.outputdir)
                command = self.rdseedir+'rdseed_4.7.5 -f '+fn+' -g '+self.dataless+' -q '+\
                          mseedir+self.outputdir+' -b 90000 -o 1 -d 1 -z 3  >/dev/null 2>/dev/null'
                if DEBUG:
                    print command
                os.system(command)
                g = self.get_ms_cont(mseedir+self.outputdir)
                for i in g.keys():
                    for j in g[i].keys():
                        if j != 'date':
                            filename = self.mk_fn(i,j,g[i]['date'], sacdir)
                            if DEBUG:
                                print "--> writing file ", filename
                            if self.merge_sac(g[i][j],filename):
                                self.cp_resp(i, j, filename)
                            for k in g[i][j]:
                                os.remove(k)
        if not DEBUG:
            pbar.finish()


if __name__ == '__main__':

    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            rdseedir = cp.get('mseed2sac','rdseedir')
            bindir   = cp.get('mseed2sac','bindir')
            mseedir  = cp.get('mseed2sac','mseedir')
            sacfiles = cp.get('mseed2sac','sacfiles')
            dataless = cp.get('mseed2sac','dataless')
            respfiles= cp.get('mseed2sac','respfiles')
            spat     = cp.get('mseed2sac','search_pattern')
            outputdir = 'sacfiles'
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "using standard parameters"
        rdseedir = '/home/behrya/src/rdseed4.7.5/'
        bindir   = '/home/behrya/dev/auto/bin/'
        mseedir  = './2003/'
        sacfiles = './SacFiles/'
        dataless = '/home/behrya/dev/proc-scripts/wsdl/gsoap/miniseed/C/example/dataless/nz.dataless.seed'
        respfiles= './respfiles/'
        outputdir= 'sacfiles'
        spat     = '*'

    t = SaFromMseed(dataless, respfiles, outputdir, bindir, rdseedir)
    t(mseedir, sacfiles, spat)
