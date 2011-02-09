#! /usr/bin/env mypython
"""
Python script to replace initsac_db (one less item to worry about compiling)
01/02/2011
"""

import os, os.path, sys, glob, string
from sac_db import *
from obspy.sac import *
from ConfigParser import SafeConfigParser
import ctypes

DEBUG=True

class PyDb(SacDb):
    def __init__(self,flag,prefix,dbname):
        self.flag = flag
        self.prefix = prefix
        self.dbname = dbname
        self.nev = 0
        self.nst = 0
        
    def __call__(self,datadir,skipdir,spat,respdir):
        self.initPyDb(datadir,skipdir,spat,respdir)


    def initPyDb(self,datadir,skipdir,spat,respdir):
        """
        Create PyDb using sac_db classes...
        """

        for dir in datadir.split(','):
            if not os.path.isdir(dir):
                print "ERROR: %s isn't a valid directory!" % dir
                continue
            
            for sp in spat.split(','):
                if DEBUG:
                    print "searching for files matching: ", sp
                os.path.walk(dir,self.ls,sp)
            # Walk the tree... and glob all files...but skip out any skipdirs...
        
    def ls(self,sp, dirname, filelist):
        a = glob.glob(os.path.join(dirname,sp))
        if len(a) > 0:
            for file in a:
                self.extractHead(file)
    
    def searchStat(self, station):
        """
        If station isn't in DB, add it
        Else, return index of station in DB
        """
        cnt = -1
        list = [i.name for i in self.st]
        if station in list:
            cnt = list.index(station)
            return cnt
        else:
            return cnt
    
    
    def yearDay(self, year, month, day):
        """
        Calculate  yearday from YY/MM/DD format
        """        
        
        days = [[0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
                [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]]
        
        leap = (year % 4 == 0 & year % 100 != 0) | year % 400 == 0
        
        for i in range(1,int(month)):
            day += days[leap][i]
        
        return day
    
    def absTime(self, yy, jday, hh, mm, ss, ms):
        nyday = 0
        for i in range(1901, yy):
            if i % 4 == 0:
                nyday = nyday + 366
            else:
                nyday = nyday + 365
        return 24.*3600.*(nyday+jday) + 3600.*hh + 60.*mm + ss + 0.001*ms
                           
    def monthDay(self, year, yearday):
        """
        Calculate monthday from yearday
        """
        days = [[0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
                [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]]        
        
        leap = (year % 4 ==0 & year % 100 != 0) | year % 400 == 0
        
        for i in range(1, yearday):
            while yearday > days[leap][i]:
                yearday -= days[leap][i]
        pmonth = i
        pday = yearday
        
        return pmonth, pday
        
        
    def searchEv(self,event):
        
        index = -1
        for i in range(0, len(self.ev)):
            if event == self.ev[i].t0:
                index = i
                break
            
        return index        
            
    def extractHead(self, file):
        """
        Extract sac-header info and write into DB structure
        """
        p = SacIO(file, headonly=True)
        station = p.GetHvalue('kstnm')
        # If station isn't in database, add it...
        index = self.searchStat(station)
        if index == -1:
            ns = self.nst
            self.st[ns].lat = p.GetHvalue('stla')
            self.st[ns].lon = p.GetHvalue('stlo')
            self.st[ns].name = station
        else:
            ns = index
        if 0:
            print file
        date = os.path.dirname(file).split('/')[-1]
        date = date.split('_')
        year = int(date[0])
        month = int(date[1])
        day = int(date[2])
        yday = self.yearDay(year, month, day)
        t0 = self.absTime(year, yday, 0, 0, 0, 0)
        
        index = self.searchEv(t0)  
        if index == -1:
            ne = self.nev
            self.ev[ne].name = os.path.dirname(file)
            self.nev += 1
        else:
            ne = index
            self.ev[ne].name = os.path.dirname(file)
        
        self.rec[ne][ns].fname = os.path.basename(file)
        self.rec[ne][ns].ft_fname = self.prefix+'_'+os.path.basename(file)
        if DEBUG:
            chan = p.GetHvalue('kcmpnm')
            self.rec[ne][ns].chan = ctypes.c_char_p(chan)
        else:
            self.rec[ne][ns].chan = p.GetHvalue('kcmpnm')
        
        self.ev[ne].yy = year
        self.ev[ne].jday = yday
        self.ev[ne].mm, self.ev[ne].dd = self.monthDay(year, yday)
        self.ev[ne].h = 0
        self.ev[ne].m = 0
        self.ev[ne].s = 0
        self.ev[ne].ms = 0.
        self.ev[ne].t0 = t0
        
        self.rec[ne][ns].dt = p.GetHvalue('delta')
        self.rec[ne][ns].n = p.GetHvalue('npts')
        self.rec[ne][ns].t0 = self.absTime(p.GetHvalue('nzyear'),
                                           p.GetHvalue('nzjday'),
                                           p.GetHvalue('nzhour'),
                                           p.GetHvalue('nzmin'),
                                           p.GetHvalue('nzsec'),
                                           p.GetHvalue('nzmsec'))
        
        # Find response files
        
        if not os.path.isdir(respdir):
            print "Cannot find response file directory!"
        elif self.resptype == 'PAZ':
            respattern = respdir+'/SAC_PZs*'+p.GetHvalue('kstnm')+'*'+p.GetHvalue('kcmpnm')+'*'
        elif self.resptype == 'RESP':
            respattern = respdir+'/RESP*'+p.GetHvalue('kstnm')+'*'+p.GetHvalue('kcmpnm')
        else:
            print "Invalid response-file type!\n"
            print "Specify either 'PAZ' or 'RESP'!"
            
        respfiles = glob.glob(respattern)
        if len(respfiles) > 0:
            if len(respfiles) > 1:
                print "WARNING: more than 1 response file available for %s\n" %  file
                print " ---> taking the first one\n"
                if self.resptype == 'RESP':
                    self.rec[ne][ns].resp_fname = respfiles[0]
                elif self.resptype == 'PAZ':
                    self.rec[ne][ns].paz_fname = respfiles[0]
        elif len(respfiles) == 1:
            if self.resptype == 'RESP':
                self.rec[ne][ns].resp_fname = respfiles[0]
            elif self.restpye == 'PAZ':
                self.rec[ne][ns].pz_fname = respfiles[0]
        else:
            print "ERROR: no response file found for %s\n" % file
            
        if self.flag == 1:
            respattern = os.path.dirname(file)+'/'+self.prefix+'_*'+p.GetHvalue('kstnm')+'*'+p.GetHvalue('kcmpnm')+'.SAC'
            
            ftfiles = glob.glob(respattern)
            if len(ftfiles) > 0:
                if len(ftfiles) > 1:
                    print "WARNING: more than 1 ft file available for: %s \n" % file
                    print " ---> taking the first one\n"
                    
                    p = SacIO(ftfiles[0], headonly=True)
                    self.rec[ne][ns].n = p.GetHValue('npts')
                    self.rec[ne][ns].dt = p.GetHValue('delta')
                elif len(ftfiles) == 1:
                    p = SacIO(ftfiles[0], headonly=True)
                    self.rec[ne][ns].n = p.GetHValue('npts')
                    self.rec[ne][ns].dt = p.GetHValue('delta')
            else:
                print "ERROR: no ft-file found for %s\n" % file
                self.rec[ne][ns].n = 0    
        
if __name__ == '__main__':
    try:
        if string.find(sys.argv[1], '-c') != -1:
            cnffile = sys.argv[2]
            conf = SafeConfigParser()
            conf.read(cnffile)
            datadir = conf.get("init_pydb","search_directories")
            skipdir = conf.get("init_pydb","skip_directories")
            spat = conf.get("init_pydb","search_string")
            respdir = conf.get("init_pydb","resp_dir")
            flag = conf.get("init_pydb","flag")
            prefix = conf.get("init_pydb","prefix")
            dbname = conf.get("init_pydb","dbname")
            
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        cnffile = 'config.txt'
            
    if not os.path.isfile(cnffile):
        print "no config file found"
        sys.exit(1)
    if 0:
        print datadir
        print skipdir
        print spat
        print respdir
        print flag
        print prefix
        print dbname    
    a = PyDb(flag,prefix,dbname)
    a(datadir,skipdir,spat,respdir)
    dbname = a.dbname
    a.flag = None
    a.prefix = None
    a.dbname = None
    write_db(a,dbname)


        
        
        
        
        
        
        
        
            
