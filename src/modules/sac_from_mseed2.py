#! /usr/bin/env python

'''
Created on 1 Oct 2010

@author: Adam Carrizales

Modification to make sac_from_mseed a file-only function rather than a directory class.
For grid computing purposes.
'''
import sys, os, os.path, glob, time, shutil
from obspy.sac import *
from datetime import datetime
import subprocess as sp
import pysacio as p



DEBUG = False

masterdir = '/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/master'
dataless = '/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/X2.10.SAHKE_db.20102570910.dataless'
respdir = '/Volumes/GeoPhysics_03/users-data/carrizad/SAHKE/paz'
outputdir = '/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/sac'
bindir = '/Users/home/carrizad/Desktop/xcorr/xcorr_git/bin'
rdseed = '/usr/local/bin/rdseed'
monthdict = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'July', 8:'Aug',\
              9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}


# mseed = sys.argv[1] not needed!


def procMseed(mseed,mseedir=masterdir,sacdir=outputdir,dataless=dataless,bindir=bindir,rdseed=rdseed):
    """Grid version of proc_mseed """
    if DEBUG:
        print "Searching for file: %s" % os.path.join(mseedir,mseed)
        
        if not os.path.isfile(os.path.join(mseedir,mseed)):
            print "No file exists by that name in this directory."
            return
    
    fn = os.path.join(mseedir,mseed)    
    if os.path.isfile(fn):
        tempout = os.path.join(mseedir,sacdir)
        
        if not os.path.isdir(tempout):
            os.mkdir(tempout)
        
        command = rdseed+' -f '+fn+' -g '+dataless+' -q '+tempout+ ' -b 9000000 -o 1 -d 1 -z 3 >/dev/null 2>/dev/null'
        
        if DEBUG:
            print command
        os.system(command)
        g = getMsCont(tempout)
        for i in g.keys():
            for j in g[i].keys():
                if j != 'date':
                    filename = makeFilename(i,j,g[i]['date'], sacdir)
                    
                    if DEBUG:
                        print "--> writing file ", filename
			writetime = datetime.now()
			print "The time is: %s" % writetime
                    if mergeSac(g[i][j], filename):
                        pass
                    
                    for k in g[i][j]:
                        os.remove(k)


def getMsCont(dir):
    """ get info about extracted sacfiles from sac-file header"""
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

def makeFilename(stn, chan, d, sacdir):
    """ construct filename out of station-, channel-, date-info """
    monstr = monthdict[d.tm_mon]
    ddir = sacdir+'/'+`d.tm_year`+'/'+monstr+'/'+\
    `d.tm_year`+'_'+`d.tm_mon`+'_'+`d.tm_mday`+'_0_0_0/'
    if not os.path.isdir(ddir):
        os.makedirs(ddir)
    filename = ddir+'/'+stn+'.'+chan+'.SAC'
    return filename


def mergeSac(filelist, outputfn):
    """ Call C-code to merge sac-files of same day into a big sac file"""
    try:
        mergesaccmd = os.path.join(bindir,"merge_sac")+ " "+outputfn
        p = sp.Popen(mergesaccmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
        child = p.stdin
        for i in filelist:
            print >>child, i
        err = child.close()
        rcode = p.wait()
        if err or rcode != 0:
            raise RuntimeError, '%r failed with exit code %d' % (mergesaccmd, err)
        
    except Exception, e:
        if DEBUG:
            print "ERROR: while merging sac files"
        return 0
    else:
        return 1
    
