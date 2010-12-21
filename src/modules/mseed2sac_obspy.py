#! /usr/bin/env python
'''
Created on Oct 12, 2010

@author: Adam Carrizales


'''
import os, os.path, sys, shutil, string, datetime, time, glob


from obspy.sac import *
from obspy.core import read
from obspy.mseed import *
from obspy.xseed.parser import Parser
from ConfigParser import SafeConfigParser
from math import fabs

import numpy as np
import progressbar as pg
import subprocess as sp

DEBUG = False


class mseed2sac:
    def __init__(self, dataless, respdir, outputdir, bindir):
        self.bindir = bindir
        self.dataless = dataless
        self.respdir = respdir
        self.outputdir = outputdir
        self.monthdict = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'June',\
                           7:'July', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
        
    def __call__(self, mseedir, sacdiroot, spat):
        self.procMseed(mseedir, sacdiroot, spat)
        
          
    
    def readDataless(self, dataless):
        """ Read dataless mSEED and return
        necessary SAC header fields as a dictionary
        """
        
        try:
            dataless = Parser(dataless)
            headerDict = {}
            
            for station in dataless.stations:
                for blockette in station:
                    if blockette.id == 50:
                        stationID = blockette.station_call_letters.strip()
                        stlo = blockette.longitude
                        stla = blockette.latitude
                        stel = blockette.elevation
                        
                        headerDict[stationID] = {}
                        headerDict[stationID]['stlo'] = stlo
                        headerDict[stationID]['stla'] = stla
                        headerDict[stationID]['stel'] = stel
                        
        except SacIOError:
            print "ERROR: cannot read dataless file"
            
        return headerDict
    
    def writeSacHead(self, file, headerDict):
        """ Write values stored in a SAC header dict
        from readDataless() into SAC header of a file """
        
        try:
            header = SacIO(file, headonly=True)
            station = header.hs[0].strip()
            
            for field in headerDict [station]:
                
                header.SetHvalue(field, headerDict[station][field])
                
#            header.ListStdValues()
            # For debugging header values
            
            header.WriteSacHeader(file)
        
        except SacIOError:
            print "ERROR: cannot read in SAC-header: %s" % file
            
            
    def makeFilename(self, stn, chan, d, sacdir):
        """ Construct filename out of station-, channel-, and date-info"""
        
        monstr = self.monthdict[d.tm_mon]
        ddir = sacdir+'/'+`d.tm_year`+'/'+monstr+'/'+\
                `d.tm_year`+'_'+`d.tm_mon`+'_'+`d.tm_mday`+'_0_0_0/'
        if not os.path.isdir(ddir):
            os.makedirs(ddir)
        
        filename = ddir+'/'+stn+'.'+chan+'.SAC'
        
        return filename


    def getMsInfo(self, stream):
        """ Get info about sacfiles from the mseed data """
        

        trace = stream[0]
        datestr = trace.stats.starttime
        year = datestr.year
        yday = datestr.julday
        stn = trace.stats.station
        chan = trace.stats.channel
        date = time.strptime(str(year)+" "+str(yday),"%Y %j")
            
        return stn, chan, date    
    
    def respFileDict(self, dirname):
        """create a dictionary from all responsefiles in 'dirname'"""
        respdict = {}
        for file in glob.glob(dirname+'/SAC_PZ*'):
            fn = os.path.basename(file)
            a  = string.split(fn,'_')
            if a[3] not in respdict.keys():
                respdict[a[3]] = {}
                respdict[a[3]][a[4]] = []
                respdict[a[3]][a[4]].append(file)
            elif a[4] not in respdict[a[3]].keys():
                respdict[a[3]][a[4]] = []
                respdict[a[3]][a[4]].append(file)
            else:
                respdict[a[3]][a[4]].append(file)
        return respdict
    
    def copyResp(self, stn, chan, sacfn):
        """ copy response file for station(stn) channel (chan) to
        appropriate location """
        
        if len(self.respFileDict(self.respdir)[stn][chan]) > 1:
            print "WARNING: there are several response files available"
            
        respfile = self.respFileDict(self.respdir)[stn][chan][0]
        outdir = os.path.dirname(sacfn)
        target = os.path.join(outdir,os.path.basename(respfile))
        shutil.copy(respfile, target)
        
        if DEBUG:
            print "---> cp ", respfile, ' ', target
            
    def mergeSac(self, filelist, outputfn):
        """
        Call c-code to merge sac-files of same day into one file
        """
        try:
            command = os.path.join(self.bindir, "merge_sac")+" "+ outputfn
            p = sp.Popen(command, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
            child = p.stdin
            for i in filelist:
                print >>child, i
            err  = child.close()
            rcode = p.wait()
            if err or rcode != 0:
                raise Exception, "%r failed with exit code" % (command)
        except Exception, e:
            if DEBUG:
                print "ERROR: while merging sacfiles"
            return 0
        else:
            return 1         
    
    def mergeSac_CLess(self, filelist, outputfn):
        """
        mergeSac without using C-...see if it can integrate with obspy merge
        
        Pseudo-code:
        
        [1] - for every file in the filelist, read into a 'stream'
            --> this way all traces can have their .stats with them (structure)
        [2] - assign t1[j] & t2[j] = datetime objects
        [3] - find longest time series and earliest start time...
        [4] - Assign T1/T2 into the user[0][1] variable in sac header
        [5] - Work out the threshold for too many holes!
        [6] ...
        """
        # Initialize empty stream to hold traces 
        st = Stream()
        #Initialize the threshold values
        T1 = 1.e25
        T2 = 100.
        t1 = []
        t2 = []
        
        cnt = -1
        
        # Read all file headers and extract headers into stream object
        
        for i in filelist:
            try:
                s0 = read(i, headonly=True)
            except SacIOError:
                print "ERROR: cannot read: ", i
                continue
            
            # In case each file has multiple traces...
            for j, trace in enumerate(s0):
                # Add trace into temporary stream
                st.append(s0[j])
                cnt += 1
                t1.append(time.gmtime(st[cnt].stats.starttime)) #Seconds since epoch
                t2.append(st[cnt].stats.endtime - st[cnt].stats.starttime) # Total seconds of record
                
                # Find longest time series and earliest start time
                if t1[cnt] < T1:
                    T1 = t1[cnt]
                    nfirst = cnt
                
                if t2[cnt] > T2:
                    T2 = t2[cnt]
            if DEBUG:
                print "Count is: ", cnt
            nf = cnt
            
        s0 = Stream()
        s0.append(st[nfirst])
        s0[0].stats.sac.user0 = T1
        s0[0].stats.sac.user1 = T2
        
        N = int(round(((T2-T1)/s0[0].stats.delta)))
        npts = s0[0].stats.npts
        
        sig0 = 1.e30 * np.ones(N,dtype=float)
        
        for j in range(0, nf):
            try:
                sig1 = read(filelist[j])
            except SacIOError:
                print "ERROR: Unable to read: ", filelist[j]
                continue
            
            if fabs(st[j].stats.delta - s0[0].stats.delta) > .0001:
                print "ERROR: incompatible dt in file %s\n" % filelist[j]
                continue
            ti = time.gmtime(st[j].stats.starttime)
            nb = int(round((ti-T1)/s0[0].delta))
            
            # FInd all values higher than 1e29
            for k in range(0, st[j].stats.npts):
                jj = nb + k
                
                if sig0[jj] > 1.e29:
                    sig0[jj] = sig1[k]
                    
        Nholes = 0
        
        for j in range(0, N):
            if sig0[j] > 1.e29:
                Nholes += 1
        
        if float(Nholes)/float(N) > 0.1:
            print "ERROR: too many holes\n"
            return 0
        
        for j in range(0, N):
            if sig0[j] > 1.e29:
                npart = 16
                
                while sig0[j] > 1.e29:
                    av = self.avSig(sig0, j, N, N/npart)
                    if av < 1.e29:
                        break
                    if npart == 1:
                        av = 0.
                        break
                    npart = npart/2
                
                sig0[j] = av
                
        s0[0].data = sig0
        s0.write(outputfn, format='SAC')
        
        return 1
                
    def avSig(self, sig, i, N, nwin):
        """
        Compute average of signal between sig[i-N/2] and sig[i+N/2]
        """
        av = 0.
        nav = 0
        
        if nwin > N:
            nwin = N
        n1 = i - nwin/2
        if n1 < 0:
            n1 = 0
        n2 = n1 + nwin - 1
        if n2 > (N-1):
            n2 = N-1
        n1 = n2 - nwin + 1
        for j in range(n1, n2):
            if sig[j] < 1.e29:
                av += sig[j]
                nav += 1
            else:
                av = av/float(nav)
        
        return av
            
    def procMseed(self, mseedir, sacdir, spat):
        """ Main function to process mseed files """
        if DEBUG:
            print "searching for pattern %s" % os.path.join(mseedir, spat)
        
        files = glob.glob(os.path.join(mseedir,spat))
        
        if len(files) < 1:
            print "No files found!"
            return
        
        if DEBUG:
            print "Reading in dataless file..."
        
        headerDict = self.readDataless(self.dataless)
        
        cnt = 0
        if not DEBUG:
            widgets = ['mSEED2sac: ', pg.Percentage(), ' ', pg.Bar('#'), ' ', pg.ETA()]
            pbar = pg.ProgressBar(widgets=widgets, maxval=len(files)).start()
            
        for fn in files:
            if DEBUG:
                print fn
            else:
                cnt += 1
                pbar.update(cnt)
                
            if os.path.isfile(fn):
                tempout = os.path.join(mseedir,'temp')
                
                if not os.path.isdir(tempout):
                    os.mkdir(tempout)
                
                mseed = read(fn)
                stn, chan, date = self.getMsInfo(mseed)
                filename = self.makeFilename(stn, chan, date, sacdir)
                #print "Filename is: ", filename
                #print "tempout dir is: ", tempout
                if os.path.isfile(filename):
                    if DEBUG:
                        print "File exists:", filename
                else:
                    fout = os.path.basename(filename)
                    mseed.write(os.path.join(tempout, fout),format='SAC')
                    
                    files = glob.glob(os.path.join(tempout,fout.rstrip('.SAC')+'*.SAC'))
                    
                    #for f in files:    
                    #    self.writeSacHead(f, headerDict)
                    if DEBUG:
                        print "--> merging sac files", files                  
                    #If only one file exists (i.e one trace) then do not mergesac, just copy into targetdir
                    if len(files) == 1:
                        shutil.copy(files[0], os.path.dirname(filename))
                        self.writeSacHead(filename, headerDict)
                    else:
                        if self.mergeSac(files, filename):
                            if DEBUG:
                                print "--> files merged!"
                            self.writeSacHead(filename, headerDict)
                            
                    for f in files:
                            os.remove(f)
                    
                if not DEBUG:
                    pbar.finish()


if __name__ == '__main__':

    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
#            rdseed = cp.get('mseed2sac','rdseed')
            bindir   = cp.get('mseed2sac','bindir')
            mseedir  = cp.get('mseed2sac','mseedir')
            outputdir = cp.get('mseed2sac','outputdir')
            dataless = cp.get('mseed2sac','dataless')
            respdir= cp.get('mseed2sac','respdir')
            spat     = cp.get('mseed2sac','search_pattern')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "usage: %s -c config-file" % os.path.basename(sys.argv[0])
        sys.exit(1)
        
    t = mseed2sac(dataless, respdir, outputdir, bindir)
    t(mseedir, outputdir, spat)
            
        
            
            
        
                        
        
        






