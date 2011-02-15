#!/usr/bin/env mypython
'''
Script to convert mseed files to sac files

Written by: Yannik Behr
Modifed by: Adam Carrizales

'''

import os, os.path, glob, sys, string, time, shutil
import subprocess as sp
from ConfigParser import SafeConfigParser
from obspy.sac import *

DEBUG = False

class mSeed2Sac:
    def __init__(self, dataless, respdir, outputdir, bindir, rdseed):
        self.dataless = dataless
        self.respdir = respdir
        self.outputdir = outputdir
        self.bindir = bindir
        self.rdseed = rdseed
        self.monthdict = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May', \
                          6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct', \
                          11:'Nov',12:'Dec'}
        self.flist = []        

    def __call__(self, mseedir, outputdir, spat):
        self.procMSeed(mseedir, outputdir, spat)
        
    def respFileDict(self, dirname):
        """
        Create dictionary from all response files in 'dirname'
        """
        respdict = {}
        for file in glob.glob(os.path.join(dirname,'/RESP*')):
            fn = os.path.basename(file)
            a = string.split(fn, '.')
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
    
    def ls(self, sp, dirname, filelist):
        """
        List all files matching pattern 'sp' and append to global list
        """
        a = glob.glob(os.path.join(dirname, sp))
        if len(a) > 0:
            self.flist.append(a)
            
    
    
    def makeFilename(self, stn, chan, d, outputdir):
        """
        Construct filename out of station-, channel-, date-info
        """
        monstr = self.monthdict[d.tm_mon]
        ddir = outputdir+'/'+`d.tm_year`+'/'+monstr+'/'+\
               `d.tm_year`+'_'+`d.tm_mon`+'_'+`d.tm_mday`+'_0_0_0/'
        if not os.path.isdir(ddir):
            os.makedirs(ddir)
        filename = ddir+'/'+stn+'.'+chan+'.SAC'
        return filename
    
    def getMsInfo(self, dir):
        """
        Get info about sacfiles from sac-header
        """
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
    
    def mergeList(self, seq):
        """
        Merge sequence of lists into a single list
        """
        list = []
        for s in seq:
            for x in s:
                list.append(x)
        return list

    def mergeSac(self, filelist, outputfn):
        """
        Call C-code to merge sac-files of same day into one file
        """
        try:
            command = os.path.join(self.bindir, "merge_sac")+ " "+outputfn
            p = sp.Popen(command, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
            child = p.stdin
            for i in filelist:
                print >>child, i
            err = child.close()
            rcode = p.wait()
            if err or rcode != 0:
                raise RuntimeError, '%r failed with exit code %d' % (command, err)
        except Exception, e:
            if DEBUG:
                print "ERROR: while merging sacfiles"
            return 0
        else:
            return 1
        
    def copyResp(self, stn, chan, fn):
        """
        Copy response file for station(stn) channel(chan) to 
        appropriate location
        (not used)
        """
        if len(self.respFileDict(self.respdir)[stn][chan]) > 1:
            print "WARNING: there are several response files available"
        respfile = self.respFileDict(self.respdir)[stn][chan][0]
        outdir = os.path.dirname(fn)
        target = os.path.join(outdir, os.path.basename(respfile))
        shutil.copy(respfile, target)
        if DEBUG:
            print "--> cp ", respfile, ' ', target
            
    def procMSeed(self, mseedir, outputdir, spat):
        """
        Main processing loop
        """
        if not os.path.isdir(mseedir):
            print "ERROR: Master directory doesn't exist!\n"
            print "Check that 'MSEEDIR' in config file is valid."
            return
        
        for sp in spat.split(','):
            if DEBUG:
                print "searching for files matching: ", sp
            
            """ ..."""
            
            
            os.path.walk(mseedir, self.ls, sp)
            files = self.mergeList(self.flist)
            if DEBUG:
                print "No. of files to process: ", len(files)
            if len(files) < 1:
                print "no files found for pattern: ", sp
                continue
            for fn in files:
               # if DEBUG:
                  #  print fn
                if os.path.isfile(fn):
                    tempout = os.path.join(mseedir, outputdir)
                    if not os.path.isdir(tempout):
                        os.mkdir(tempout)
                command = self.rdseed+' -f '+fn+' -g '+self.dataless+' -q '+\
                          tempout+' -b 900000000 -o 1 -d 1 -z 3  >/dev/null 2>/dev/null'
                os.system(command)
                if DEBUG:
                    print command
                g = self.getMsInfo(tempout)
                for i in g.keys():
                    for j in g[i].keys():
                        if j != 'date':
                            filename = self.makeFilename(i, j, g[i]['date'], outputdir)
                            if os.path.isfile(filename):
                                for k in g[i][j]:
                                    os.remove(k)
                                continue
                            if DEBUG:
                                print "--> writing file: ", filename
                            if self.mergeSac(g[i][j], filename):
                                pass
                                #self.copyResp(i, j, filename) 
                            for k in g[i][j]:
                                os.remove(k)
                            if DEBUG:
                                print "To remove: ", g[i][j]
                                    
if __name__ == '__main__':
    try:
        if string.find(sys.argv[1], '-c') != -1:
            config = sys.argv[2]
            print "config file is: ", sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            rdseed    = cp.get('mseed2sac','rdseed')
            bindir    = cp.get('mseed2sac','bindir')
            mseedir   = cp.get('mseed2sac','mseedir')
            outputdir = cp.get('mseed2sac','outputdir')
            dataless  = cp.get('mseed2sac','dataless')
            respdir   = cp.get('mseed2sac','respdir')
            spat      = cp.get('mseed2sac','search_pattern')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "usage: %s -c config-file" % os.path.basename(sys.argv[0])
        sys.exit(1)
        
    t = mSeed2Sac(dataless, respdir, outputdir, bindir, rdseed)
    t(mseedir, outputdir, spat)
                

