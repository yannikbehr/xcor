#!/usr/bin/env mypython
"""
wrapper for initsac_db C-routine

"""

"""
Need to make a new loop in initsacdb that will 'walk' each day directory in the structure
and make a new dbname + execute new init_sacdb loop for each day

produce dbname_year_jday

-> submit each one to grid processing for rest of processing steps

"""

import os, os.path, sys, string, fnmatch
from ConfigParser import SafeConfigParser
from subprocess import *

DEBUG = False

def initsacdb(datdir,regex='[!^ft]*Z.SAC',
                  srchflag='0',prefix='ft',sacdbf='sac_db.out',
                  tmpdir='./tmp/',resp_dir='./',skipdir='XXX'):
    _path = '/Users/home/carrizad/xcorr'
    tmpcnf = 'config_tmp.txt'
    if os.path.isfile(tmpcnf):
        os.remove(tmpcnf)
                 
    output = open(tmpcnf,"w")
    outlines = []
    outlines.append("[init_sacdb]\n")
    outlines.append("search_directories="+datdir+",\n")
    outlines.append("skip_directories="+skipdir+"\n")
    outlines.append("flag="+srchflag+"\n")
    outlines.append("search_string="+regex+"\n")
    outlines.append("resp_dir="+resp_dir+"\n")
    outlines.append("prefix="+prefix+"\n")
    outlines.append("dbname="+sacdbf+"\n")
    outlines.append("tmpdir="+tmpdir+"\n")
    output.writelines(outlines)
    output.close()
    initcmd = os.path.join(_path,'bin/initsac_db')
    if DEBUG:
        print initcmd, tmpcnf
    p = call([initcmd,'-c', tmpcnf])

#    out,err = Popen([initcmd,'-c',os.path.join(tmpdir,tmpcnf)],stdout=PIPE,stderr=PIPE).communicate()
#    
#    f = open(os.path.join(tmpdir,sacdbf),'w')
#    f.write(out)
#    f.close()
#    f = open(os.path.join(tmpdir,'initsacdb.err'),'w')
#    f.write(err)
#    f.close()
    os.remove(tmpcnf)





def Walk(root, recurse=1, pattern='*_*_*_0_0_0', return_folders=1,skipdir=''):
    """
    From ActiveState.com Recipe: 52664-flexible-directory-walking/
    
    Will return all 'day' directories if options are specified
    Faster than glob!
    
    Need to fix it to allow skipping of directories (like passband)
    """
    # initialize
    result = []

    # must have at least root folder
    try:
        names = os.listdir(root)
        for dir in skipdir.split(','):
            if dir in names:
                names.remove(dir)
    except os.error:
        return result

    # expand pattern
    pattern = pattern or '*'
    pat_list = string.splitfields( pattern , ',' )
    
    # check each file
    for name in names:
        fullname = os.path.normpath(os.path.join(root, name))

        # grab if it matches our pattern and entry type
        for pat in pat_list:
            if fnmatch.fnmatch(name, pat):
                if os.path.isfile(fullname) or (return_folders and os.path.isdir(fullname)):
                    result.append(fullname)
                continue
                
        # recursively scan other folders, appending results
        if recurse:
            if os.path.isdir(fullname) and not os.path.islink(fullname):
                result = result + Walk( fullname, recurse, pattern, return_folders )
            
    return result


if __name__ == "__main__":
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config = sys.argv[2]
            print "config file is: ", sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            datadir =  cp.get('init_sacdb','search_directories')
            respdir =  cp.get('init_sacdb','resp_dir')
            dbname =  cp.get('init_sacdb','dbname')
            skipdir =  cp.get('init_sacdb','skip_directories')
            spat =  cp.get('init_sacdb','search_string')
            prefix =  cp.get('init_sacdb','prefix')
            tmpdir =  cp.get('init_sacdb','tmpdir')
            flag =  cp.get('init_sacdb','flag')
            
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "usage: %s -c config-file" % os.path.basename(sys.argv[0])
        sys.exit(1)
       
    # Return all 'date' directories which hold SAC files
    daydirs = Walk(datadir)
    
    for day in daydirs:
        tmp = os.path.basename(day).split('_')
        tmp_dbname = dbname+'_%s_%s_%s' % (tmp[0],tmp[1],tmp[2])

        if DEBUG:
            print "Initializing for: ", day
        initsacdb(day,spat,flag,prefix,tmp_dbname,tmpdir,respdir,skipdir)
        


