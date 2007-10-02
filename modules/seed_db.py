""" program to initialize a sqlite database and fill in with data from
seed volumes as well as creating the directory tree for the sac-files\n
$Log$
Revision 1.5  2007/07/30 22:58:22  behrya
changed sorting of 'stations'-array

Revision 1.4  2007-07-03 01:20:12  behrya
added pre_proc_driver.py

Revision 1.3  2007-06-29 00:38:44  behrya
added comment

"""

import string, sqlite, os, glob
from ConfigParser import SafeConfigParser

class Initialize_DB:


    def __init__(self,conf):
        self.cp = conf
        try:
            self.datadir = self.cp.get('database', 'databasedir')
            self.rdseed = self.cp.get('database', 'rdseeddir')
            if not os.access(self.datadir,os.F_OK) or not os.access(self.rdseed,os.F_OK):
                raise Exception, (self.datadir, self.rdseed)
        except Exception, value:
            print "ERROR: One of the given directories or files doesn't exist: ", value
        self.db_file = self.cp.get("database", "databasefile")
        self.rootdir = self.cp.get("database", "sacdirroot")
        self.channel = self.cp.get("processing", "channel")


    def extr_date(self, cont):
        """extract date information from seed-filename"""
        try:
            datelst = []
            for i in cont:
                mylist = string.split(i,'-')
                year = mylist[1][0:4]
                month = mylist[1][4:6]
                day = mylist[1][6:8]
                hh = mylist[2][0:2]
                mint = mylist[2][2:4]
                sec = mylist[2][4:6]
                path = self.datadir+i
                date = (path, year, month, day, hh, mint, sec, 'nothing', self.channel)
                datelst.append(date)
            return datelst
        except Exception, e:
            print "ERROR: ", e


    def init_stat_db(self):
        """create sqlite-database with station-table and
        seed-file information table;
        station information is extracted from seed-files"""
        self.rdseed = self.rdseed + 'rdseed'
        try:
            contents = os.listdir(self.datadir)
        except Exception, e:
            "ERROR: Cannot retrieve directory-contents: ",e
        else:
            try:
                curdir = os.getcwd()
                os.chdir(self.datadir)
                stations = []
                for i in contents:
                    command = self.rdseed + ' -Sf '+i
                    os.system(command)
                    for line in open('rdseed.stations').readlines():
                        tmpline = string.split(line)
                        t = (tmpline[0], float(tmpline[2]), float(tmpline[3]), float(tmpline[4]), self.channel)
                        # append station to list if it doesn't occur yet
                        if len(stations) != 0: 
                            cmpflag = 0
                            for ii in stations:
                                if ii[0]==tmpline[0]:
                                    cmpflag = 1
                                    break
                            if cmpflag == 0:
                                stations.append(t)
                        else:
                            stations.append(t)
                        
                    for i in glob.glob('rdseed*'):
                        os.remove(i)
                for statnum in range(0,len(stations)):
                    print "station ", statnum," is ", stations[statnum]
                os.chdir(curdir)
            except os.error, value:
                print "ERROR: problems occured in system calls: ", value[0], value[1]
            except Exception, e:
                print "ERROR: problems in the rdseed-block: ", e
            else:
                try:
                    # writing station information into database
                    conn = sqlite.connect(self.db_file)
                    c = conn.cursor()
                    try:
                        c.execute('''create table stations (station text,lon real,lat real,alt real,channel text)''')
                    except Exception, e:
                        print "SQL-warning: ", e
                        return
                    for ii in stations:
                        c.execute('insert into stations values (%s,%f,%f,%f,%s)', ii)
                    conn.commit()
                    # writing seed-file information into database
                    try:
                        c.execute('''create table seedfiles (path text, year text, month text, day text, \
                        hour text, minute text, second text, sacdir text, channel text)''')
                    except Exception, e:
                        print "SQL-warning: ", e
                        return
                    seedlst = self.extr_date(contents)
                    for jj in seedlst:
                        c.execute('insert into seedfiles values (%s,%s,%s,%s,%s,%s,%s,%s,%s)', jj)
                    conn.commit()
                except Exception, e:
                    print "ERROR: in sqlite block: ", e


    def dir_walk(self, arg, dirname, names):
        print arg, dirname, names


    def init_dat_strct(self):
        """create directory tree according to information
        in sqlite database"""
        monthdict = {'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May', \
                     '06':'Jun','07':'Jul','08':'Aug','09':'Sep','10':'Oct', \
                     '11':'Nov','12':'Dec'}
        try:
            os.path.isdir(self.db_file)
            conn = sqlite.connect(self.db_file)
            c = conn.cursor()
        except Exception, e:
            print "Cannot connect to database-file"
        else:
            try:
                c.execute('select year, month from seedfiles')
                yylist = c.fetchall()
                year = []
                month = []
                for i in yylist:
                    tmpyear, tmpmonth = i
                    year.append(tmpyear)
                    month.append(tmpmonth)
                year = set(year)
                month = set(month)
                #print year, month
            except Exception, e:
                print "ERROR: problems occured in db-read block: ", e
            else:
                try:
                    if os.path.isdir(self.rootdir):
                        print "root directory for sac-files already exists!"
                        os.path.walk(self.rootdir, self.dir_walk, '--->')
                    else:
                        os.mkdir(self.rootdir)
                    for i in year:
                        if not os.path.isdir(self.rootdir+'/'+i):
                            os.mkdir(self.rootdir+'/'+i)
                        else:
                            print "directory ",self.rootdir+'/'+i," already exists!"
                        for j in month:
                            if not os.path.isdir(self.rootdir+i+'/'+monthdict[j]):
                                os.mkdir(self.rootdir+i+'/'+monthdict[j])
                            else:
                                print "directory ",self.rootdir+i+'/'+monthdict[j]," already exists!"

                            dirname = [self.rootdir+i+'/'+monthdict[j],j,i]
                            try:
                                c.execute('''update seedfiles set sacdir=%s where month=%s and year=%s ''',dirname)
                            except Exception, e:
                                print "ERROR: cannot update sql-table seedfiles: ",e
                            else:
                                conn.commit()
                except Exception, e:
                    print "ERROR: Cannot initialise directory tree ", e


    def start_seed_db(self):
        try:
            self.init_stat_db()
        except Exception,e:
            print "problems with function 'init_stat_db' in 'seed_db.py'", e
            return 1
        else:
            try:
                self.init_dat_strct()
            except Exception,e:
                print "problems with function 'init_dat_strct' in 'seed_db.py'", e
                return 1
            else:
                return 0
        
    
if __name__ == '__main__':
    cp = SafeConfigParser()
    cp.read('config.txt')
    new = Initialize_DB(cp)
    if cp.get('database','datatype') == 'seed':
        new.start_seed_db()
