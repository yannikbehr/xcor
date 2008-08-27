#!/usr/bin/env python
"""script to extract all available data from seed-files into daylong
sacfiles and put them in the right directory structure\n
The script accounts for 3 different cases: \n
1. the seed file contains data for one day only\n
2. the seed file contains data for several days\n
3. several seed files contain data for the same day\n

In the last case it is decided whether to merge, or delete one
of the sac files that correspond to the same date"""

import seed_info
import sys
from pylab import *
import os, os.path
import subprocess as sp
import time, glob, re
sys.path.append('./modules')
import pysacio as p
import pytutil as pt

class SaFromSeed(seed_info.SeedInfo):
    def __init__(self, rdseedir, bindir, sacroot):
        self.rdseedir = rdseedir
        self.sacroot = sacroot
        self.bindir  = bindir
        seed_info.SeedInfo.__init__(self,rdseedir)


    def __call__(self, filelist):
        self.extract_sac(filelist)


    def rdseed_extr(self,filename, station, channel, date1, date2):
        """run rdseed-command to extract daylong sacfiles and
        corresponding response-file"""
        command = self.rdseedir+'rdseed 2>/dev/null 1>/dev/null'
        buffersize = 8640000
        p = sp.Popen(command, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
        child = p.stdin
        print >>child, '%s' %(filename)     # Input  file
        print >>child, ''                   # Output file 
        print >>child, ''                   # Volume
        print >>child, 'd'                  # Options
        print >>child, ''                   # Summary file
        print >>child, '%s' %(station)      # Station list
        print >>child, '%s' %(channel)      # channel list
        print >>child, ''                   # Network list
        print >>child, ''                   # Loc Ids
        print >>child, '1'                  # Output format
        print >>child, 'N'                  # Output filenames include endtime?
        print >>child, 'N'                  # Output poles and zeroes?
        print >>child, '0'                  # Check Reversal
        print >>child, ''                   # Select Data Type
        print >>child, '%s' %(date1)        # Start time(s)
        print >>child, '%s' %(date2)        # End time(s)
        print >>child, '%d' %(buffersize)   # Sample buffer length
        print >>child, 'Y'                  # Extract Responses?
        print >>child, 'quit'               # Input file or 'Quit' to exit
        err = p.stdin.close()
        rcode = p.wait()
        if err or rcode != 0:
            raise RuntimeError, '%r failed with exit code %d' %(command, err)
        else:
            return 1


    def merge_sac(self,filelist, outputfn):
        """run c-code to merge several sac-files of the same day into
        one big sac-file"""
        try:
            mergesaccmd = self.bindir+"/merge_sac "+outputfn
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
    

    def comp_sac(self, oldfile, newfile):
        """if there are two sac-files for the same date decide
        whether to merge them or delete the shorter one"""
        [hf1,hi1,hs1,ok1] = p.ReadSacHeader(oldfile)
        [hf2,hi2,hs2,ok2] = p.ReadSacHeader(newfile)
        if ok1 and ok2:
            T1 = p.GetHvalue('user0',hf1,hi1,hs1)
            T2 = p.GetHvalue('user1',hf1,hi1,hs1)
            year = p.GetHvalue('nzyear',hf2,hi2,hs2)
            yday = p.GetHvalue('nzjday',hf2,hi2,hs2)
            hour = p.GetHvalue('nzhour',hf2,hi2,hs2)
            mint = p.GetHvalue('nzmin',hf2,hi2,hs2)
            sec  = p.GetHvalue('nzsec',hf2,hi2,hs2)
            msec = p.GetHvalue('nzmsec',hf2,hi2,hs2)
            npts = p.GetHvalue('npts',hf2,hi2,hs2)
            delta = p.GetHvalue('delta',hf2,hi2,hs2)
            sec = sec + msec/1000
            T21, ok = pt.dt2seconds(year,yday,hour,mint,sec)
            T22 = T21 + npts*delta
            if T2<T21 or T1>T22:
                return 1
            elif (T2-T1) > (T22 - T21):
                return 2
            elif (T2-T1) < (T22 - T21):
                return 3
            else:
                return -1
        elif not ok1:
            print "ERROR: cannot read ", oldfile
            return -1
        elif not ok2:
            print "ERROR: cannot read ", newfile
            return -1
        
        
    
    def extract_sac(self,filelist):
        """get seed-file info and based on that extract everything
        (every station, every channel) into daylong sacfiles"""
        for fn in filelist:
            print fn
            g = self.extract_sd(fn)
            if g == 0:
                print "ERROR: cannot extract seed file meta information for %s" %(fn)
                continue
            a = g.start; b = g.end
            for i in range(int(a),int(b)+1):
                for stat in g.records.keys():
                    for comp in g.records[stat].keys():
                        respattern = r'RESP.\w*.%s.\w*.%s' %(stat,comp)
                        j = num2date(i)
                        dlist1 = j.utctimetuple()
                        date1 = `dlist1[0]`+'.'+`dlist1[7]`+'.00:00:01'
                        date2 = `dlist1[0]`+'.'+`dlist1[7]`+'.23:59:59'
                        print "extracting %s (%s) between %s and %s" %(stat,comp,date1,date2)
                        self.rdseed_extr(fn, stat, comp, date1, date2)
                        sacfiles = glob.glob('*.SAC')
                        if len(sacfiles) > 0:
                            if not os.path.isdir(self.sacroot):
                                print "creating ", self.sacroot
                                os.mkdir(self.sacroot)
                            yeardir = self.sacroot+'/'+`dlist1[0]`
                            if not os.path.isdir(yeardir):
                                print "creating ", yeardir
                                os.mkdir(yeardir)
                            daydir = self.sacroot+'/'+`dlist1[0]`+'/'+`dlist1[0]`+'_'+`dlist1[1]`+'_'+`dlist1[2]`+'_0_0_0'
                            if not os.path.isdir(daydir):
                                print "creating ", daydir
                                os.mkdir(daydir)
                            outputfn = stat+'.'+comp+'.SAC'
                            self.merge_sac(sacfiles, outputfn)
                            if os.path.isfile(outputfn) and not \
                                   os.path.isfile(os.path.join(daydir,outputfn)):
                                os.rename(outputfn,os.path.join(daydir,outputfn))
                            elif os.path.isfile(os.path.join(daydir,outputfn)):
                                oldfile = os.path.join(daydir,outputfn)
                                newfile = outputfn
                                retval = self.comp_sac(oldfile, newfile)
                                if retval == 1:
                                    self.merge_sac([oldfile, newfile], newfile+'_tmp')
                                    if os.path.isfile(newfile+'_tmp'):
                                        os.rename(newfile+'_tmp',
                                                  os.path.join(daydir,newfile+'_tmp'))
                                elif retval == 2:
                                    pass
                                elif retval == 3:
                                    os.rename(newfile,os.path.join(daydir,newfile))
                                elif retval == -1:
                                    print "ERROR: unexpected error while comparing sac files"
                            for rf in glob.glob('./RESP*'):
                                match = re.search(respattern,rf)
                                if match and not \
                                       os.path.isfile(os.path.join(daydir,os.path.basename(rf)))\
                                       and os.path.isfile(os.path.join(daydir,outputfn)):
                                    os.rename(rf,os.path.join(daydir,os.path.basename(rf)))
                                else:
                                    for rf in glob.glob('./RESP*'):
                                        os.remove(rf)
                                    
                            for sf in glob.glob('./*.SAC'):
                                os.remove(sf)
                        else:
                            for rf in glob.glob('./RESP*'):
                                os.remove(rf)
        for errf in glob.glob('./rdseed.err_log.*'):
            os.remove(errf)

if __name__ == '__main__':
    rdseedir = '/home/behrya/src/rdseed4.7.5/'
    bindir   = '/home/behrya/dev/auto/bin/'
    sacroot  = './testsac'
    filelist = ['/data/hawea/yannik/SAPSE/xc/SAPSE_XC.10.20115']
    t = SaFromSeed(rdseedir, bindir, sacroot)
    t(filelist)

#This is the specification for the date format given by the
#rdseed-manual:
#"Start Time(s) (FIRST) :
# a list of seismogram start times of the form YYYY.DDD.HH:MM:SS.FFFF
# or YYYY/MM/DD.HH:MM:SS.FFFF separated by spaces. YYYY may be YY i.e.
# "90" for "1990". Least significant parts may be omitted, in which
# case they become zero i.e. "90.270" is time 00:00:00.000 of the
# 270th day of 1990...."

# At the moment this script is extracting all available channels.
# I did that, because I thought it's easier to delete the channels
# that aren't needed afterwards than deciding automatically
# which channels should be extracted and which shouldn't
