#!/usr/bin/env mypython
"""
wrapper for initsac_db C-routine
"""

import os, os.path, sys, glob
from subprocess import *


def initsacdb(datdir,regex='[!^ft]*Z.SAC',cnf='./config.txt',
                  srchflag='0',prefix='ft',sacdbf='sac_db.out',
                  tmpdir='./tmp/',resp_dir='./'):
    _path = os.environ['AUTO_SRC']
    output = open(cnf,"w")
    outlines = []
    outlines.append("[init_sacdb]\n")
    outlines.append("search_directories="+datdir+"\n")
    outlines.append("skip_directories=5.0to100.0, eqband, 1to40\n")
    outlines.append("flag="+srchflag+"\n")
    outlines.append("search_string="+regex+"\n")
    outlines.append("resp_dir="+resp_dir+"\n")
    outlines.append("prefix="+prefix+"\n")
    outlines.append("dbname="+sacdbf+"\n")
    outlines.append("tmpdir="+tmpdir+"\n")
    output.writelines(outlines)
    output.close()
    initcmd = os.path.join(_path,'bin/initsac_db')
    out,err = Popen([initcmd,'-c',cnf],stdout=PIPE,stderr=PIPE).communicate()
    f = open(os.path.join(tmpdir,'initsacdb.out'),'w')
    f.write(out)
    f.close()
    f = open(os.path.join(tmpdir,'initsacdb.err'),'w')
    f.write(err)
    f.close()
   # if os.path.isfile(cnf):
   #     os.remove(cnf)


if __name__ == "__main__":
    try:
        if string.find(sys.argv[1],'-c')!=-1:
            cnffile=sys.argv[2]
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        cnffile = 'config.txt' 

    if not os.path.isfile(cnffile):
        print "no config file found"
        sys.exit(1)

    _path = '/Users/home/carrizad/xcorr/'
    initcmd = os.path.join(_path,'bin/initsac_db')
    out,err = Popen([initcmd,'-c',cnffile]).communicate()
