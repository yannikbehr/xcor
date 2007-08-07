"""module to call justCOR subroutine\n
$Log$
Revision 1.1  2007/07/10 05:10:31  behrya
driver module for justCOR function

"""

import os, os.path, string, shutil, glob, sys
from ConfigParser import SafeConfigParser

class Xcorr:

    def __init__(self, conf):
        self.sacdir = conf.get("database", "sacdirroot")
        self.tmpdir = conf.get("database", "tmpdir")
        self.upperp = conf.get("processing", "upperperiod")
        self.lowerp = conf.get("processing", "lowerperiod")
        self.months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    def create_dir(self, dirname, i):
        bpfile = self.upperp+'to'+self.lowerp
        if not os.path.isdir(dirname+'/'+i+'/'+bpfile):
            print "directory ", bpfile, " doesn't exist"
            return
        else:
            try:
                os.mkdir(dirname+'/'+i+'/'+bpfile+'/COR')
            except os.error, v:
                    
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
        os.path.walk(self.sacdir,self.dir_walk,0)




if __name__ == '__main__':
    cp = SafeConfigParser()
    cp.read('config.txt')
    
    test = Xcorr(cp)
    test.start()
