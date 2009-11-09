#!/usr/bin/env mypython
"""script to extract information from seed-files using the 'rdseed -cf seedfile'
and 'rdseed -Sf' command"""

import os, re, string, glob, pytutil, time, math
import subprocess as sp
from pylab import *
import datetime, sys

class SeedInfoException(Exception):
    pass

class SeedStr: pass

class SeedInfo:
    def __init__(self, rdseedir):
        self.rdseedir = rdseedir
        
    
    def __call__(self, filen):
        return self.extract_sd(filen)
        

    def get_time(self, line):
        """extract time and convert into epoch-days"""
        pattern = r'(\d+),(\d+),(\d+):(\d+):(\d+)\.\d+'
        match = re.search(pattern,line)
        if match:
            year = int(match.group(1))
            yday = int(match.group(2))
            month, mday, err = pytutil.monthdate(year, yday)
            if err == -1:
                print "ERROR: problems in 'pytutil.monthdate'"
                return 0
            hour = int(match.group(3))
            mins = int(match.group(4))
            sec  = int(match.group(5))
            wday = 0                        # weekday set to Monday
            dayls = -1                      # I don't care about daylight saving
            a = (year, month, mday, hour, mins, sec, wday, yday, dayls)
            eptime = time.mktime(a)
            eptime = datetime.datetime.fromtimestamp(eptime)
            return date2num(eptime)
        else:
            return 0
    
    
    def get_stat_inf(self, line, g):
        """fill in structure with channel/timespan information"""
        elmts = string.split(line)
        stime = self.get_time(elmts[5])
        if stime == 0:
            stime = self.get_time(elmts[4])
            if stime == 0:
                print "WARNING: cannot extract time", line
                return 0
        etime = self.get_time(elmts[8])
        if etime == 0:
            etime = self.get_time(elmts[7])
            if etime == 0:
                print "WARNING: cannot extract time", line
                return 0
    
        if len(elmts) > 11:
            if elmts[1] in g.records.keys():
                if elmts[3] in g.records[elmts[1]].keys():
                    g.records[elmts[1]][elmts[3]].append((stime, etime-stime))
                    return 1
                else:
                    g.records[elmts[1]][elmts[3]] = []
                    g.records[elmts[1]][elmts[3]].append((stime, etime-stime))
                    return 1
            else:
                g.records[elmts[1]] = {}
                g.records[elmts[1]][elmts[3]] = []
                g.records[elmts[1]][elmts[3]].append((stime, etime-stime))
                return 1
            
        elif len(elmts) == 11:
            if elmts[1] in g.records.keys():
                if elmts[2] in g.records[elmts[1]].keys():
                    g.records[elmts[1]][elmts[2]].append((stime, etime-stime))
                    return 1
                else:
                    g.records[elmts[1]][elmts[2]] = []
                    g.records[elmts[1]][elmts[2]].append((stime, etime-stime))
                    return 1
            else:
                g.records[elmts[1]] = {}
                g.records[elmts[1]][elmts[2]] = []
                g.records[elmts[1]][elmts[2]].append((stime, etime-stime))
                return 1
        else:
            print "WARNING: unknown format of line: ", line
            return 0
    
    def run_rdseed(self, filename):
        """run the rdseed commands; errors are sent to space; output from
        'rdseed -cf'-command is returned as a list of lines; the file
        'rdseed.stations' is written by the 'rdseed -Sf'-command"""
        # get timespan information from seed-volume
        print filename
        p = sp.Popen([self.rdseedir,'-cf',filename],stdout=sp.PIPE,stderr=sp.PIPE)
        stdout,stderr = p.communicate()
        data = stdout.split('\n')
        if len(data) < 2:
            raise SeedInfoException("rdseed -cf failed for file %s"%filename)

        # get station + lat/lon/elev information 
        command =self.rdseedir+' -Sf '+filename+' 2>/dev/null'
        retcode = sp.call(command,shell=True)
        #a=os.system(command)
        if retcode != 0 and not os.path.isfile('rdseed.stations'):
            raise SeedInfoException("rdseed -Sf failed for file %s"%filename)
        # remove rdseed error log
        for ii in glob.glob('./rdseed.err_log*'):
            os.remove(ii)
        return data
         
    
    def extract_sd(self, filename):
        """main-function that gets passed the seed-filename and returns a structure that
        contains all the information on seed-volume"""
        data = self.run_rdseed(filename)
        if data != 0:
            # extract lines by seed key
            pattern = r'^B074F03-16'
            patterns = r'^B010F05'
            patterne = r'^B010F06'
            patternst = r'^B011F04-05'
            g = SeedStr()
            g.stations = {}
            g.records = {}
            for line in data:
                matchstat = re.search(pattern, line)
                if matchstat:
                    if not self.get_stat_inf(line, g):
                        print filename
                        print '-->', line
                        continue
                matchstat = re.search(patterns, line)
                if matchstat:
                    g.start = self.get_time(line.split()[6])
                matchstat = re.search(patterne, line)
                if matchstat:
                    g.end = self.get_time(line.split()[6])
                matchstat = re.search(patternst, line)
                if matchstat:
                    stat = line.split()[1]
                    if stat not in g.stations.keys():
                        g.stations[stat] = {}
                    
            for line in open('rdseed.stations').readlines():
                tmpline = line.split()
                if tmpline[0] in g.stations.keys():
                    g.stations[tmpline[0]]['lat'] = tmpline[2]
                    g.stations[tmpline[0]]['lon'] = tmpline[3]
                    g.stations[tmpline[0]]['elv'] = tmpline[4]
                else:
                    print "station %s not in station-list" %(tmpline[0])
            os.unlink('rdseed.stations')
            return g
        else:
            return 0




if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except:
        filename = '/data/hawea/yannik/nord/nord-geonet/ouz/seed/GN-20040229-000001-27437.seed'
    print "+++++++++++++++++++++ SUMMARY ++++++++++++++++++++++++++++++"
    rdseedir = '/usr/local/bin/rdseed'
    t = SeedInfo(rdseedir)
    g = t(filename)
    print "stations: %s "%(' '.join(g.records.keys()))
#    for _s in g.records.keys():
#        chan = g.records[_s].keys()[0]
#        start, length = g.records[stat][chan][0]
#    print "station: %s  channel: %s  start: %s  length (in days): %f" %(stat,chan,num2date(start),length)
#    print "latitude: %s  longitude: %s elevation: %s" %(g.stations[stat]['lat'],g.stations[stat]['lon'],g.stations[stat]['elv'])
    print "volume start: %s  volume end: %s" %(num2date(g.start), num2date(g.end))
    print g.records
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
