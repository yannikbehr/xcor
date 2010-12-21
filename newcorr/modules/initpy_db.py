#! /usr/bin/env python
'''
Created on 7 Dec 2010

@author: Adam Carrizales

Write a sac_db style database in python

TODO:

Initialize db file
Search directory tree for matching files
Extract header info from the sac-header or the filename
Add entries to database


TODO:

Check the ne/ns indicies are pointing to the right event
they may need to be incremented

Use pickle to read/write the 'DB'


'''

import os, os.path, sys, glob, string
from ConfigParser import SafeConfigParser
from obspy.sac import *
import cPickle as pickle


DEBUG = False

class pythonDB:
    def __init__(self, dbname, respdir, resptype, prefix, flag):
        self.dbname = dbname
        self.respdir = respdir
        self.resptype = resptype
        self.prefix = prefix
        self.flag = flag
        
        # Set initial values
        self.nev = 0
        self.nst = 0
        
        self.st = []
        self.ev = []
        self.rec = []

    def __call__(self, searchdir, skipdir, spat):
        self.makeDB(searchdir, skipdir, spat)
        
    def absTime(self, yy, jday, hh, mm, ss, ms):
        nyday = 0
        for i in range(1901, yy):
            if i % 4 == 0:
                nyday = nyday + 366
            else:
                nyday = nyday + 365
        return 24.*3600.*(nyday+jday) + 3600.*hh + 60.*mm + ss + 0.001*ms
    

    def makeDB(self, searchdir, skipdir, spat):
        """
        Main function for creating a python list database
        """
        
        for dir in searchdir.split(','):
            if not os.path.isdir(dir):
                print "ERROR: %s isn't a valid directory!" % searchdir
                return
            
            if DEBUG:
                print "searching in: ", dir
                
            for sp in spat.split(','):
                if DEBUG:
                    print "searching for files matching: ", sp
                os.path.walk(dir, self.ls, sp)
    
    def searchEv(self, event):
        """
        If event name (day) isn't in DB, add it
        Else, return total number of events
        """
        index = -1
        for i in range(0, len(self.ev)):
            if event == self.ev[i].t0:
                index = i
                break
        
        return index
            
        
    def searchStat(self, station):
        """
        If station isn't in the DB, add it
        Else, return the index of station in DB
        """
        index = -1
        if station not in self.st:
            self.st.append(station)
            return index
        else:
            index = self.st.index(station)
            return index
                    
    def extractHead(self, file):
        """
        Extract the sac-header information and write into DB array
        """
        # Read in sacheader
        p = SacIO(file, headonly=True)
        
        station = p.GetHvalue('kstnm')
        # If station isn't in database, add it.    
        
        index = self.searchStat(station)
        
        if index == -1:
            ns = self.nst
            self.st[ns].lat = p.GetHvalue('stla')
            self.st[ns].lon = p.GetHvalue('stlo')
            self.st[ns].name = station
            self.nst += 1    
        else:
            ns = index
        
        #Get the title of directory (holds date-info)
        date = os.path.dirname(file).split('_')
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
        #### Find response files
        
        if not os.path.isdir(respdir):
            print "Cannot find response file directory!"
        elif self.resptype == 'PAZ':
            respattern = respdir+'/SAC_PZs*'+p.GetHvalue('kstnm')+'*'+p.GetHvalue('kcmpnm')+'*'
        elif self.resptype == 'RESP':
            respattern = respdir+'/SAC_PZs*'+p.GetHvalue('kstnm')+'*'+p.GetHvalue('kcmpnm')
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
        
        # Find ft_* (or other prefix) files if flag is set to '1'
            
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
                
                    
                    
    def monthDay(self, year, yearday):
        """
        Calculate monthday from yearday
        """
        days = [[0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
                [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]]        
        
        leap = (year % 4 ==0 & year % 100 != 0) | year % 400 ==0
        
        for i in range(1, yearday):
            while yearday > days[leap][i]:
                yearday -= days[leap][i]
        pmonth = i
        pday = yearday
        
        return pmonth, pday
        
        
            
    def yearDay(self, year, month, day):
        """
        Calculate  yearday from YY/MM/DD format
        """        
        
        days = [[0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
                [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]]
        
        leap = (year % 4 == 0 & year % 100 != 0) | year % 400 == 0:
        for i in range(1,int(month)):
            day += days[leap][i]
        
        return day
        
        
            
    def ls(self, sp, dirname, filelist):        
        """
        List all files and call another function to extract header of each
        """
        
        a = glob.glob(os.path.join(dirname, sp))
        if len(a) > 0:
            for file in a:
                self.extractHead(file)
            
         
if __name__ == "__main__":
    try:
        if string.find(sys.argv[1], '-c') != -1:
            config = sys.argv[2]
            print "config file is: ", sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            searchdir = cp.get('initpy_db', 'searchdir')
            skipdir = cp.get('initpy_db', 'skip_directories')
            spat = cp.get('initpy_db', 'search_pattern')
            respdir = cp.get('initpy_db', 'respdir')
            resptype = cp.get('initpy_db', 'resptype')
            flag = cp.get('initpy_db', 'flag')
            prefix = cp.get('initpy_db', 'prefix')
            dbname = cp.get('initpy_db', 'dbname')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "usage: %s -c config-file" % os.path.basename(sys.argv[0])
        sys.exit(1)

    db = pythonDB(dbname, respdir, resptype, prefix, flag)
    db(searchdir, skipdir, spat)
    
    #Open db file, pickle dump using highest available protocol (binary..)
    # Should implement a series of methods for print(), read() and write() DB...
    output = open(dbname, 'wb')
    pickle.dump(db, output, -1)
    output.close()
    
