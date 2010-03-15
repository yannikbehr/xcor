#!/usr/bin/env mypython
"""module for calling filter4.f and whiten_phamp.f with appropriate values
and creating output directory\n
$Log$
Revision 1.7  2007/07/09 02:01:01  behrya
obtaining tempdir-name from config-file

"""

import os, os.path, string, shutil, glob, sys
import subprocess as sp
from ConfigParser import SafeConfigParser

import pysacio as p

class ProcLst: pass


class DoWhiten:
    """class that comprises routines for performing filtering\n
    and spectral whitening"""
    def __init__(self,sacdir,rootdir,prefix,complist,sacbin='/usr/local/sac/bin/',
                 bindir=os.path.join(os.environ['AUTO_SRC'],'bin'),
                 upperp=5,lowerp=100,skipdir=[]):
        self.sacdir  = sacdir
        self.rootdir = rootdir
        self.prefix  = prefix
        self.complst = complist.split(',')
        self.sacbin  = sacbin
        self.bindir  = bindir
        self.upperp  = upperp
        self.lowerp  = lowerp
        self.skipdir = skipdir
        self.eqband = [50, 15]
        self.months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        self.npow = 1
        self.proclst = ProcLst()
        self.proclst.ydaydir = []
        self.cnt = -1


    def filter4_f(self, upperp, lowerp):
        """ calls the c-driver for the fortran 77 program filter4.f"""
        utaper = upperp - (float(upperp)/100)*20
        ltaper = lowerp + (float(lowerp)/100)*20
        equtaper = self.eqband[1] - (float(self.eqband[1])/100)*20
        eqltaper = self.eqband[0] + (float(self.eqband[0])/100)*20
        filtercmd = self.bindir+"/filter4"
        for i in self.proclst.ydaydir:
            if len(i.keys()) == len(self.complst) + 1:
                for j in self.complst:
                    for k in i[j]:
                        src, tar, eqtar = k
                        p = sp.Popen(filtercmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
                        child = p.stdin
                        print >>child, ltaper, lowerp, upperp, utaper, self.npow, src, tar
                        err = child.close()
                        ret = p.wait()
                        if err or ret != 0:
                            raise RuntimeError, '%r failed with exit code %d' %(filtercmd, err)
                        p = sp.Popen(filtercmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
                        child = p.stdin
                        print >>child, eqltaper, self.eqband[0], self.eqband[1], equtaper, self.npow, tar, eqtar
                        err = child.close()
                        ret = p.wait()
                        if err or ret != 0:
                            raise RuntimeError, '%r failed with exit code %d' %(filtercmd, err)
                        #shutil.copy2(tar,tar+'_filter')
        return 1


    def white_1_comp(self, upperp, lowerp):
        """ calls sac routines to conduct whitening for Z-component"""
        utaper = upperp - (float(upperp)/100)*20
        ltaper = lowerp + (float(lowerp)/100)*20
        saccmd = self.sacbin+' 1>/dev/null'
        #whitefilter = self.bindir+'/white_1cmp'+' 1>/dev/null'
        whitefilter = self.bindir+'/white_1cmp'
        for i in self.proclst.ydaydir:
            if len(i.keys()) == len(self.complst) +1:
                for j in self.complst:
                    for k in i[j]:
                        p1 = sp.Popen(saccmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
                        child1 = p1.stdin
                        src, tar, eqtar = k
                        print tar
                        print >>child1, "r %s" %(eqtar)
                        print >>child1, "abs"
                        print >>child1, "smooth mean h 128"
                        print >>child1, "w over a1.avg"
                        print >>child1, "r %s" %(tar)
                        print >>child1, "divf a1.avg"
                        print >>child1, "w over %s" %(tar)
                        print >>child1, "q"
                        err1 = child1.close()
                        ret1 = p1.wait()
                        if os.path.isfile('a1.avg'):
                            #shutil.copy2(tar,tar+'_smooth')
                            os.remove('a1.avg')
                        if err1 or ret1 != 0:
                            raise RuntimeError, '%r failed with exit code %d' %(saccmd, err1)
                        p2 = sp.Popen(whitefilter, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
                        child2 = p2.stdin
                        print >>child2, ltaper, lowerp, upperp, utaper, self.npow, tar
                        err2 = child2.close()
                        ret2 = p2.wait()
                        if err2 or ret2 != 0:
                            raise RuntimeError, '%r failed with exit code %d' %(whitefilter, err2)
        return 1


    def xtract_fn(self, file1, file2):
        """check if 2 sacfiles have same station name and different horiz.
        components (E and N)"""
        [hf1, hi1, hs1, ok1] = p.ReadSacHeader(file1)
        [hf2, hi2, hs2, ok2] = p.ReadSacHeader(file2)
        if ok1:
            stat1 = string.strip(p.GetHvalue('kstnm',hf1,hi1,hs1))
            comp1 = string.strip(p.GetHvalue('kcmpnm',hf1,hi1,hs1))
        else:
            print "ERROR: cannot read in sac-header for file: ", src1
            return 0
        if ok2:
            stat2 = string.strip(p.GetHvalue('kstnm',hf2,hi2,hs2))
            comp2 = string.strip(p.GetHvalue('kcmpnm',hf2,hi2,hs2))
        else:
            print "ERROR: cannot read in sac-header for file: ", src2
            return 0
        if stat1 == stat2:
            if comp1.endswith('N') and comp2.endswith('E'):
                return 1
            elif comp1.endswith('E') and comp2.endswith('N'):
                return 1
        else:
            print "ERROR: station names are not the same"
            return 0


    def white_2_comp(self, upperp, lowerp):
        """ call sac routines conduct whitening for North and East component"""
        utaper = upperp - (float(upperp)/100)*20
        ltaper = lowerp + (float(lowerp)/100)*20
        whitefilter = self.bindir+'/white_2cmp'
        saccmd = self.sacbin
        for i in self.proclst.ydaydir:
            if len(i.keys()) == len(self.complst) +1:
                for j in i[self.complst[0]]:
                    for k in i[self.complst[1]]:
                        src1, tar1, eqtar1 = j
                        src2, tar2, eqtar2 = k
                        if not self.xtract_fn(src1, src2):
                            print "ERROR: files %s and %s inadequate!" %(src1, src2)
                        else:
                            p1 = sp.Popen(saccmd, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
                            child1 = p1.stdin
                            print src1, src2
                            print >>child1, "r %s %s" %(eqtar1, eqtar2)
                            print >>child1, "abs"
                            print >>child1, "smooth mean h 128"
                            print >>child1, "w aaa bbb"
                            print >>child1, "r aaa"
                            print >>child1, "subf bbb"
                            print >>child1, "abs"
                            print >>child1, "addf aaa"
                            print >>child1, "addf bbb"
                            print >>child1, "div 2"
                            print >>child1, "w a1.avg"
                            print >>child1, "r %s %s" %(tar1, tar2)
                            print >>child1, "divf a1.avg"
                            print >>child1, "w %s %s" %(tar1, tar2)
                            print >>child1, "q"
                            err1 = child1.close()
                            ret1 = p1.wait()
                            if err1 or ret1 != 0:
                                raise RuntimeError, '%r failed with exit code %d' %(saccmd, err1)
                            if os.path.isfile('./aaa'):
                                os.remove('./aaa')
                            if os.path.isfile('./bbb'):
                                os.remove('./bbb')
                            if os.path.isfile('./a1.avg'):
                                os.remove('./a1.avg')
                            p2 = sp.Popen(whitefilter, shell=True, bufsize=0, stdin=sp.PIPE, stdout=None)
                            child2 = p2.stdin
                            print >>child2, ltaper, lowerp, upperp, utaper, self.npow, tar1, tar2
                            err2 = child2.close()
                            ret2 = p2.wait()
                            if err2 or ret2 != 0:
                                raise RuntimeError, '%r failed with exit code %d' %(whitefilter, err2)
        return 1



    def create_dir_struct(self, dirname, month):
        """ creates the dir-structure for the filtering and whitening step\n
        and calls the filter and whitening subroutines"""
        dirlist = os.listdir(dirname+'/'+month)
        if not len(dirlist) >0:
            raise Exception
        bpfile = "%.1fto%.1f"%(self.upperp,self.lowerp)
        for day in dirlist:
            try:
                for _d in self.skipdir:
                    if day.find(_d) != -1:
                        raise Exception()
            except:
                continue
#            if day != bpfile and string.find(day, '.svn') == -1 and string.find(day, '5to100') == -1 and string.find(day, '5to100_EN') == -1:
            self.cnt = self.cnt + 1
            self.proclst.ydaydir.append({})
            self.proclst.ydaydir[self.cnt]['name'] = day
            #yeardir = os.path.basename(dirname)
            yeardir = dirname.split('/')[-2]
            eqdir = os.path.join(self.rootdir,bpfile,yeardir,month,day,'eqband')
            if not os.path.isdir(eqdir):
                os.makedirs(eqdir)
            # get all ft-files with channel name given in complst;
            # write them into strct
            for i in range(0,len(self.complst)):
                pattern="%s/%s/%s/%s*.%s.SAC"\
                         %(dirname,month,day,self.prefix,self.complst[i])
                print pattern
                tmplist = glob.glob(pattern)
                if len(tmplist) > 0:
                    self.proclst.ydaydir[self.cnt][self.complst[i]] = []
                    for _fn in tmplist:
                        _fn = os.path.basename(_fn)
                        src = dirname+'/'+month+'/'+day+'/'+_fn
                        tar = os.path.join(self.rootdir,bpfile,yeardir,month,day,_fn)
                        eqtar = os.path.join(self.rootdir,bpfile,yeardir,month,day,'eqband',_fn)
                        self.proclst.ydaydir[self.cnt][self.complst[i]].append((src,tar,eqtar))

    def process(self):
        print "filtering...."
        self.filter4_f(self.upperp, self.lowerp)
        if len(self.complst) < 2:
            print "whitening...."
            self.white_1_comp(self.upperp, self.lowerp)
        elif len(self.complst) == 2:
            print "whitening 2 components...."
            self.white_2_comp(self.upperp, self.lowerp)
        else:
            print "ERROR: number of components too big or too small!"
            sys.exit(1)


    def dir_walk(self, arg, dirname, names):
        """ called by os.path.walk; checks if the directory 'dirname\n
        holds any 'month' subdirectories"""
        try:
            for i in names:
                if i in self.months:
                    self.create_dir_struct(dirname, i)
                else:
                    continue
        except Exception,e:
            print "ERROR in dir_walk function: ",e
        

if __name__ == '__main__':
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        config = 'config.txt' 

    if not os.path.isfile(config):
        print "no config file found"
        sys.exit(1)
        
    conf = SafeConfigParser()
    conf.read(config)

    # frequency band +- 20% as taper
    sacdir  = conf.get("whitening", "sacfiles")
    rootdir = conf.get("whitening","rootdir")
    sacbin  = conf.get("whitening", "sacbin")
    bindir  = conf.get("whitening", "bindir")
    prefix  = conf.get("whitening", "prefix")
    upperp  = float(conf.get("whitening", "upperperiod"))
    lowerp  = float(conf.get("whitening", "lowerperiod"))
    complst = conf.get("whitening","complist")
    skipdir = conf.get("whitening","skip_directories").split(',')
    test = DoWhiten(sacdir,rootdir,prefix,complst,sacbin=sacbin,bindir=bindir,\
                    upperp=upperp,lowerp=lowerp,skipdir=skipdir)
    os.path.walk(test.sacdir, test.dir_walk, 0)
    test.process()
