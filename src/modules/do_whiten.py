"""module for calling filter4.f and whiten_phamp.f with appropriate values
and creating output directory\n
$Log$
Revision 1.7  2007/07/09 02:01:01  behrya
obtaining tempdir-name from config-file

"""

import os, os.path, string, shutil, glob, sys
from ConfigParser import SafeConfigParser

class DoWhiten:

    def __init__(self, conf, cnffile):
        self.sacdir = conf.get("database", "sacdirroot")
        self.sacbin = conf.get("database", "sacdir")
        self.tmpdir = conf.get("database", "tmpdir")
        self.bindir = conf.get("local_settings", "bindir")
        # frequency band +- 20% as taper
        self.upperp = int(conf.get("processing", "upperperiod"))
        self.utaper = self.upperp - (float(self.upperp)/100)*20
        self.lowerp = int(conf.get("processing", "lowerperiod"))
        self.ltaper = self.lowerp + (float(self.lowerp)/100)*20

        self.months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
	self.cnffilename = cnffile


    def create_dir_struct(self, dirname, i):
        bpfile = `self.upperp`+'to'+`self.lowerp`
        try:
            os.mkdir(dirname+'/'+i+'/'+bpfile)
        except os.error, value:
            print value[0], value[1]
        try:
            dirlist = os.listdir(dirname+'/'+i)
        except Exception, e:
            print "Cannot fetch dir-contents: ", e
        else:
            try:
                for j in dirlist:
                    if j != bpfile and string.find(j, '.svn') == -1 and string.find(j, '5to100') == -1:
                        tmplist = glob.glob(dirname+'/'+i+'/'+j+'/ft_*')
                        if len(tmplist) != 0:
                            f = open(self.tmpdir+'param.dat', 'w')
                            ff = open(self.tmpdir+'param_test.dat', 'w')
                            os.mkdir(dirname+'/'+i+'/'+bpfile+'/'+j)
                            os.mkdir(dirname+'/'+i+'/'+bpfile+'/'+j+'/test')
                            for jj in tmplist:
                                jj = os.path.basename(jj)
                                src = dirname+'/'+i+'/'+j+'/'+jj
                                tar = dirname+'/'+i+'/'+bpfile+'/'+j+'/'+jj
                                tar_test = dirname+'/'+i+'/'+bpfile+'/'+j+'/test/'+jj
                                shutil.copy(src,tar)
                                f.write(`self.ltaper`+' '+`self.lowerp`+' '+\
                                        `self.upperp`+' '+`self.utaper`+' 1 1 '+tar+' '+tar_test+'\n')
                                ff.write('60 50 15 12 1 1 '+tar_test+' nothing\n')
                            f.close()
                            ff.close()
                            srclist = glob.glob(dirname+'/'+i+'/'+bpfile+'/'+j+'/ft_*')
                            targetlist = [dirname+'/'+i+'/'+bpfile+'/'+j+'/test' for cnt in range(1,len(srclist)+1)]
                            command = self.bindir+'filter4 '+self.tmpdir+'/param.dat'
                            os.system(command)
                            map(shutil.copy, srclist, targetlist)
                            command_test = self.bindir+'filter4 '+self.tmpdir+'param_test.dat'
                            os.system(command_test)
                            command = self.bindir+'whiten_phamp '+self.tmpdir+'param.dat'+' -c '+self.cnffilename
                            os.system(command)
                            os.system('rm -r '+dirname+'/'+i+'/'+bpfile+'/'+j+'/test')
            except os.error, e:
                print "Cannot create directory: ", e[1]
                    

    def dir_walk(self, arg, dirname, names):
        try:
            for i in names:
                if i in self.months:
                    self.create_dir_struct(dirname, i)
                else:
                    continue
        except Exception,e:
            print "ERROR in dir_walk function: ",e

    def start(self):
        try:
            os.path.walk(self.sacdir,self.dir_walk,0)
        except Exception,e:
            print "problems in function 'start' of 'do_whiten.py'"
            return 1
        else:
            return 0



if __name__ == '__main__':
    cp = SafeConfigParser()
    config = 'config.txt' 
    cp.read(config)
    
    test = DoWhiten(cp,config)
    test.start()
