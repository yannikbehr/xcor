#!/usr/bin/env python
"""extract mseed data from geonet download and put them into the right\n
directory structure together with their corresponding response files"""


import glob, os, string, sys, os.path, time, shutil
import subprocess as sp
import pysacio as p
from ConfigParser import SafeConfigParser
import progressbar as pg
from obspy.sac import *

DEBUG = True

class SaFromMseed:
    def __init__(self, dataless, respdir, outputdir, bindir, rdseed):
        self.dataless  = dataless
        self.respdir   = respdir
        self.outputdir = outputdir
        self.bindir    = bindir
        self.rdseed    = rdseed
        self.monthdict = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May', \
                          6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct', \
                          11:'Nov',12:'Dec'}


    def __call__(self, mseedir, sacdiroot, spat):
        self.proc_mseed(mseedir, sacdiroot, spat)
    #def __call__(self, mseedir, sacdiroot, spat):
        #self.proc_mseed_file(mseedfile, sacdiroot, mseedir)



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
        ddir = sacdir+'/'+`d.tm_year`+'/'+monstr+'/'+\
               `d.tm_year`+'_'+`d.tm_mon`+'_'+`d.tm_mday`+'_0_0_0/'
        if not os.path.isdir(ddir):
            os.makedirs(ddir)
	filename = os.path.join(ddir,stn+'.'+chan+'.SAC')

        #filename = ddir+'/'+stn+'.'+chan+'.SAC'
        return filename
    

    def get_ms_cont(self, dir):
        """get info about extracted sacfiles from sac-file header"""
        listfiles = glob.glob(dir+'/*.SAC')
        stations = {}
        for file in listfiles:
             
            try:
		trace = SacIO(file, headonly=True)
	    except SacIOError:	
		print "ERROR: cannot read in sac-header: ", file
            else:
                year = `trace.GetHvalue('nzyear')`
                yday = `trace.GetHvalue('nzjday')`
                stn  = trace.GetHvalue('kstnm').strip()
                chan = trace.GetHvalue('kcmpnm').strip()
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
            #mergesaccmd = os.path.join(self.bindir,"merge_sac")+" "+outputfn+" 2>/dev/null 1>/dev/null"
	    mergesaccmd = os.path.join(self.bindir,"merge_sac")+" "+outputfn
	    if DEBUG:
		print "Merge cmd: ", mergesaccmd
            p = sp.Popen(mergesaccmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
            child = p.stdin
            for i in filelist:
                print >>child, i
            err = child.close()
            rcode = p.wait()
            if err or rcode != 0:
                raise RuntimeError, '%r failed with exit code %d' %(mergesaccmd, err)
        except Exception, e:
            if DEBUG:
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
	if len(files) < 1:
		print "No files found!"
		return
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
                tempout = os.path.join(mseedir,'sacfiles_local')
                #tempout = os.path.join(mseedir,self.outputdir)
		if not os.path.isdir(tempout):
                    os.mkdir(tempout)
                command = self.rdseed+' -f '+fn+' -g '+self.dataless+' -q '+\
                          tempout+' -b 512000000 -o 1 -d 1 -z 3  >/dev/null 2>/dev/null'
                if DEBUG:
                    print command
                os.system(command)
                g = self.get_ms_cont(tempout)
                for i in g.keys():
                    for j in g[i].keys():
                        if j != 'date':
                            filename = self.mk_fn(i,j,g[i]['date'], sacdir)
			    
			    if os.path.isfile(filename):
			      pass
			    else:
			    
			      if DEBUG:
				  print "--> writing file ", filename
			      if self.merge_sac(g[i][j],filename):
				  pass
				#self.cp_resp(i, j, filename)
				# file name is not actually being transferred i nthis function but in merge_sac which is not working
				
                            for k in g[i][j]:
                                pass
				#os.remove(k)
        if not DEBUG:
            pbar.finish()
            
    def proc_mseed_file(self, mseedfile, sacdir, mseedir):
        """main function to process mseed files"""
        if DEBUG:
            print "searching for file: %s" % os.path.join(mseedfile)
        files = glob.glob(os.path.join(mseedfile))
	if len(files) < 1:
		print "No files found!"
		return
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
                tempout = os.path.join(mseedir,self.outputdir)
		if not os.path.isdir(tempout):
                    os.mkdir(tempout)
                command = self.rdseed+' -f '+fn+' -g '+self.dataless+' -q '+\
                          tempout+' -b 9000000 -o 1 -d 1 -z 3  >/dev/null 2>/dev/null'
                if DEBUG:
                    print command
                os.system(command)
                g = self.get_ms_cont(tempout)
                for i in g.keys():
                    for j in g[i].keys():
                        if j != 'date':
                            filename = self.mk_fn(i,j,g[i]['date'], sacdir)
			    
                            if DEBUG:
                                print "--> writing file ", filename
                            if self.merge_sac(g[i][j],filename):
                                pass
				#self.cp_resp(i, j, filename)
				# file name is not actually being transferred i nthis function but in merge_sac which is not working
				
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
            rdseed = cp.get('mseed2sac','rdseed')
            bindir   = cp.get('mseed2sac','bindir')
            mseedir  = cp.get('mseed2sac','mseedir')
            outputdir = cp.get('mseed2sac','outputdir')
            dataless = cp.get('mseed2sac','dataless')
            respdir = cp.get('mseed2sac','respdir')
            spat     = cp.get('mseed2sac','search_pattern')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "usage: %s -c config-file"%os.path.basename(sys.argv[0])
        sys.exit(1)

    t = SaFromMseed(dataless, respdir, outputdir, bindir, rdseed)
    t(mseedir, outputdir, spat)
