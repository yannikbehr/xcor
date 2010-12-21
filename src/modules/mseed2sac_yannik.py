#! /usr/bin/env python
'''
Created on Oct 12, 2010

@author: Adam Carrizales


'''

from obspy.sac import *
from obspy.core import read
from obspy.mseed import *
from obspy.xseed.parser import Parser
from ConfigParser import SafeConfigParser

import numpy as np
import progressbar as pg
import os, os.path, sys, shutil, string, time, glob
import subprocess as sp

DEBUG = True


class mseed2sac:
    def __init__(self, dataless, respdir, outputdir,bindir):
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
        ddir = os.path.join(sacdir,'%d'%d.tm_year,'%s'%(monstr),
                '%d_%d_%d_0_0_0'%(d.tm_year,d.tm_mon,d.tm_mday))
        if not os.path.isdir(ddir):
            os.makedirs(ddir)
        
        filename = os.path.join(ddir,'%s.%s.SAC'%(stn,chan))
        
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
            print command
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
                print e
            return 0
        else:
            return 1         
            
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
                print "Filename is: ", filename
                print "tempout dir is: ", tempout
                if os.path.isfile(filename):
                    if DEBUG:
                        print "File exists:", filename
                else:
                    fout = os.path.basename(filename)
                    mseed.sort(keys=['starttime'])
                    mseed.write(os.path.join(tempout, fout),format='SAC')
                    
                    files = glob.glob(os.path.join(tempout,fout.rstrip('.SAC')+'*.SAC'))
                    
                    if DEBUG:
                        print "--> writing sac header"
                    for f in files:    
                        self.writeSacHead(f, headerDict)
                    if DEBUG:
                        print "--> merging sac files", files                  
                    #If only one file exists (i.e one trace) then do not mergesac, just copy into targetdir
                    if len(files) == 1:
                        shutil.copy(files[0], os.path.dirname(filename))
                    else:
                        if self.mergeSac(files, filename):
                            if DEBUG:
                                print "--> files merged!"
                            for f in files:
                                os.remove(f)
                    
                if not DEBUG:
                    pbar.finish()            

        
'/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/sac/2009/Nov/2009_11_14_0_0_0/BFZ.HHE01.SAC'


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
            
        
            
            
        
                        
        
        






