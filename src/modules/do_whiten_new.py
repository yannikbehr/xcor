"""module for calling filter4.f and whiten_phamp.f with appropriate values
and creating output directory\n
$Log$
Revision 1.7  2007/07/09 02:01:01  behrya
obtaining tempdir-name from config-file

"""

import os, os.path, string, shutil, glob, sys
from ConfigParser import SafeConfigParser

class TwirlyBar:
    """show progress of program"""
    def __init__(self):
        self.__state = 0
        self.__bar = ('[|]', '[/]', '[-]', '[\\]')

    def ShowProgress(self):
        sys.stdout.write('\b\b\b' +self.__bar[self.__state])
        sys.stdout.flush()
        self.__state = self.__state + 1
        if self.__state > 3: self.__state = 0


class ProcLst: pass


class DoWhiten:
    """class that comprises routines for performing filtering\n
    and spectral whitening"""
    def __init__(self, cnffile):
        conf = SafeConfigParser()
        conf.read(cnffile)
        self.sacdir = conf.get("database", "sacdirroot")
        self.sacbin = conf.get("database", "sacdir")
        self.tmpdir = conf.get("database", "tmpdir")
        self.bindir = conf.get("local_settings", "bindir")
        # frequency band +- 20% as taper
        self.upperp = int(conf.get("processing", "upperperiod"))
        self.lowerp = int(conf.get("processing", "lowerperiod"))
        self.eqband = [50, 15]
        #self.months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        self.months = ['Aug']
	self.cnffilename = cnffile
        self.npow = 1
        self.tb = TwirlyBar()
        self.complst = ['LHZ']
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
        child = os.popen(filtercmd, 'w')
        for i in self.proclst.ydaydir:
            for j in self.complst:
                for k in i[j]:
                    src, tar, eqtar = k
                    self.tb.ShowProgress()
                    print >>child, ltaper, lowerp, upperp, utaper, self.npow, src, tar
                    print >>child, eqltaper, self.eqband[0], self.eqband[1], equtaper, self.npow, tar, eqtar
        err = child.close()
        if err:
            raise RuntimeError, '%r failed with exit code %d' %(filtercmd, err)
            return 0
        else:
            return 1


    def white_1_comp(self, upperp, lowerp):
        """ call sac routines conduct whitening for Z-component"""
        utaper = upperp - (float(upperp)/100)*20
        ltaper = lowerp + (float(lowerp)/100)*20
        saccmd = self.sacbin+'/sac'+' 2>/dev/null 1>/dev/null'
        child1 = os.popen(saccmd, 'w')
        whitefilter = self.bindir+'/white_1cmp'+' 2>/dev/null 1>/dev/null'
        child2 = os.popen(whitefilter, 'w')
        for i in self.proclst.ydaydir:
            for j in self.complst:
                for k in i[j]:
                    src, tar, eqtar = k
                    self.tb.ShowProgress()
                    print >>child1, "r %s" %(eqtar)
                    print >>child1, "abs"
                    print >>child1, "smooth mean h 128"
                    print >>child1, "w a1.avg"
                    print >>child1, "r %s" %(tar)
                    print >>child1, "divf a1.avg"
                    print >>child1, "w over %s" %(tar)
                    if os.path.isfile('a1.avg'):
                        os.unlink('a1.avg')
                    self.tb.ShowProgress()
                    print >>child2, ltaper, lowerp, upperp, utaper, self.npow, tar
        err1 = child1.close()
        err2 = child2.close()
        if err1:
            raise RuntimeError, '%r failed with exit code %d' %(saccmd, err)
            return 0
        if err2:
            raise RuntimeError, '%r failed with exit code %d' %(whitefilter, err)
            return 0
        else:
            return 1


    def white_2_comp(self, fileinEeqb, fileinNeqb, fileinE, fileinN, \
                     fileoutE, fileoutN, upperp, lowerp):
        """ call sac routines conduct whitening for North and East component"""
        self.tb.ShowProgress()
        utaper = upperp - (float(upperp)/100)*20
        ltaper = lowerp + (float(lowerp)/100)*20
        saccmd = self.sacbin+'/sac'
        child = os.popen(saccmd, 'w')
        print >>child, "r %s %s" %(fileinEeqb, fileinNeqb)
        print >>child, "abs"
        print >>child, "smooth mean h 128"
        print >>child, "w aaa bbb"
        print >>child, "r aaa"
        print >>child, "subf bbb"
        print >>child, "abs"
        print >>child, "addf aaa"
        print >>child, "addf bbb"
        print >>child, "div 2"
        print >>child, "w a1.avg"
        print >>child, "r %s %s" %(fileinE, fileinN)
        print >>child, "divf a1.avg"
        print >>child, "w over %s %s" %(fileoutE, fileoutN)
        err = child.close()
        if os.path.isfile('aaa'):
            os.unlink('aaa')
        if os.path.isfile('bbb'):
            os.unlink('bbb')
        if os.path.isfile('a1.avg'):
            os.unlink('a1.avg')
        if err:
            raise RuntimeError, '%r failed with exit code %d' %(saccmd, err)
            return 0
        else:
            whitefilter = self.bindir+'/white_2cmp'
            child = os.popen(whitefilter, 'w')
            print >>child, ltaper, lowerp, upperp, utaper, self.npow, fileoutE, fileoutN
            err = child.close()
            if err:
                raise RuntimeError, '%r failed with exit code %d' %(whitefilter, err)
                return 0
            else:
                return 1


    def create_dir_struct(self, dirname, month):
        """ creates the dir-structure for the filtering and whitening step\n
        and calls the filter and whitening subroutines"""
        dirlist = os.listdir(dirname+'/'+month)
        if not len(dirlist) >0:
            raise Exception
        bpfile = `self.upperp`+'to'+`self.lowerp`
        if not os.path.isdir(dirname+'/'+month+'/'+bpfile):
            os.mkdir(dirname+'/'+month+'/'+bpfile)
        print "Creating dir structure: ", month
        for day in dirlist:
            if day != bpfile and string.find(day, '.svn') == -1 and string.find(day, '5to100') == -1:
                self.tb.ShowProgress()
                self.cnt = self.cnt + 1
                self.proclst.ydaydir.append({})
                self.proclst.ydaydir[self.cnt]['name'] = day
                if not os.path.isdir(dirname+'/'+month+'/'+bpfile+'/'+day):
                    os.mkdir(dirname+'/'+month+'/'+bpfile+'/'+day)
                if not os.path.isdir(dirname+'/'+month+'/'+bpfile+'/'+day+'/eqband'):
                    os.mkdir(dirname+'/'+month+'/'+bpfile+'/'+day+'/eqband')
                # get all ft-files with channel name given in complst;
                # write them into strct
                for i in range(0,len(self.complst)):
                    tmplist = glob.glob(dirname+'/'+month+'/'+day+'/ft_*'+self.complst[i]+'*')
                    self.proclst.ydaydir[self.cnt][self.complst[i]] = []
                    for file in tmplist:
                        file = os.path.basename(file)
                        src = dirname+'/'+month+'/'+day+'/'+file
                        tar = dirname+'/'+month+'/'+bpfile+'/'+day+'/'+file
                        eqtar = dirname+'/'+month+'/'+bpfile+'/'+day+'/eqband/'+file
                        self.proclst.ydaydir[self.cnt][self.complst[i]].append((src,tar,eqtar))


    def process(self):
        print "processing...."
        #self.filter4_f(self.upperp, self.lowerp)
        if len(self.complst) < 2:
            self.white_1_comp(self.upperp, self.lowerp)


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
    config = 'config.txt' 
    test = DoWhiten(config)
    os.path.walk(test.sacdir, test.dir_walk, 0)
    test.process()
