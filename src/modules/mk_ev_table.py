"""python script to generate input_ev_seed-file needed by sa_from_seed_holes_NZ.c
from a set of seed-files"""

import string, os, glob, optparse, re, sys
from ConfigParser import SafeConfigParser

class Events: pass
class Stations: pass

class InitInputEvSeed:


    def __init__(self,conf):
        self.cp = conf
        try:
            self.rdseed = self.cp.get('database', 'rdseeddir')
            self.datadir = self.cp.get('database', 'databasedir')
            self.databasefile = self.cp.get('database', 'databasefile')
            if not os.access(self.rdseed,os.F_OK) or \
                   not os.access(self.datadir,os.F_OK):
                raise Exception, (self.rdseed, self.datadir)
        except Exception, value:
            print "ERROR: directory or file doesn't exist: ", value
        self.channel = self.cp.get("processing", "channel")
        self.rootdir = self.cp.get("database", "sacdirroot")
        self.output_stations = []
        self.output_events = []


    def extr_date(self, cont):
        """extract date information from seed-filename"""
        try:
            for i in cont:
                mylist = string.split(i,'-')
                g = Events()
                g.year = mylist[1][0:4]
                g.month = mylist[1][4:6]
                g.day = mylist[1][6:8]
                g.hh = mylist[2][0:2]
                g.mint = mylist[2][2:4]
                g.sec = mylist[2][4:6]
                g.path = self.datadir+i
                self.output_events.append(g)
        except Exception, e:
            print "ERROR: in function 'extr_date'", e


    def init_stat(self):
        """extract information from seed-files"""
        self.rdseed = self.rdseed + 'rdseed'
        try:
            contents = os.listdir(self.datadir)
        except Exception, e:
            "ERROR: Cannot retrieve directory-contents: ",e
        else:
            try:
                stations = []
                # delete .svn directory from contents!!!
                for j in range(0,len(contents)):
                    if contents[j] == '.svn':
                        del contents[j]
                        break

                for i in contents:
                    command = self.rdseed + ' -Sf '+self.datadir+i+' 2>/dev/null'
                    a=os.system(command)
                    if a != 0:
                        print "WARNING: cannot read station list from ",i
                        continue
                    
                    for line in open('rdseed.stations').readlines():
                        tmpline = string.split(line)
                        s = Stations()
                        s.name = tmpline[0]
                        s.lat  = tmpline[2]
                        s.lon  = tmpline[3]
                        s.elv  = tmpline[4]
                        
                        # append station to list if it hasn't occured yet
                        if len(stations) != 0: 
                            cmpflag = 0
                            for ii in stations:
                                if re.search('^'+ii+'$',tmpline[0],re.IGNORECASE):
                                    cmpflag = 1
                                    break
                            if cmpflag == 0:
                                stations.append(tmpline[0])
                                self.output_stations.append(s)
                        else:
                            stations.append(tmpline[0])
                            self.output_stations.append(s)
                        
                    for i in glob.glob('rdseed*'):
                        os.remove(i)
            except os.error, value:
                print "ERROR: problems occured in system calls: ", value[0], value[1]
            except Exception, e:
                print "ERROR: problems in the rdseed-block: ", e
            else:
                try:
                    self.extr_date(contents)
                except Exception, e:
                    print "ERROR: in sqlite block: ", e


    def init_dat_strct(self):
        """create directory tree according to information
        extracted from seed-files"""

        monthdict = {'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May', \
                     '06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct', \
                     '11':'Nov','12':'Dec'}
        try:
            print "--> initialising dir-structure"
            if not os.path.isdir(self.rootdir):
                os.mkdir(self.rootdir)
            for i in self.output_events:
                if not os.path.isdir(self.rootdir+i.year):
                    os.mkdir(self.rootdir+i.year)
                if not os.path.isdir(self.rootdir+i.year+'/'+monthdict[i.month]):
                    os.mkdir(self.rootdir+i.year+'/'+monthdict[i.month])
                dirname = self.rootdir+i.year+'/'+monthdict[i.month]
                i.sacdir = dirname
        except Exception, e:
            print "ERROR: Cannot initialise directory tree ", e


    def write_db_file(self):
        """write ascii database file from information in seed-files"""
        try:
            output = open(self.databasefile, 'w')
        except Exception, e:
            print "ERROR: couldn't open databasefile!", e
            sys.exit(1)
        else:
            outlines = []
            outlines.append('[stations]\n')
            for i in self.output_stations:
                outlines.append(i.name+' '+i.lat+' '+i.lon+' '+i.elv+'\n')
            outlines.append('\n[events]\n')
            for i in self.output_events:
                outlines.append(i.year+' '+i.month+' '+i.day+' '+i.hh+' '+i.mint+\
                                ' '+i.sec+' '+self.channel+' '+i.path+' '+i.sacdir+'\n')
            output.writelines(outlines)
            output.close()

        
    def start_seed_db(self):
        try:
            self.init_stat()
        except Exception,e:
            print "problems with function 'init_stat_db' in 'mk_input_ev_seed.py'", e
            return 1
        else:
            try:
                self.init_dat_strct()
            except Exception,e:
                print "problems with function 'init_dat_strct' in 'mk_input_ev_seed.py'", e
                return 1
            else:
                try:
                    self.write_db_file()
                except Exception,e:
                    print "problems with function 'write_db_file' in 'mk_input_ev_seed.py'", e
                    return 1
                else:
                    return 0
        

if __name__ == '__main__':

    cmdargs = []
    if len(sys.argv) < 2:
        configfile = 'config.txt'
    else:
        cmdargs = sys.argv[1:]
        p = optparse.OptionParser()
        p.add_option('--config','-c')
        options, arguments = p.parse_args(args=cmdargs)
        configfile = str(options.config)

    cp = SafeConfigParser()
    cp.read(configfile)
    new = InitInputEvSeed(cp)

