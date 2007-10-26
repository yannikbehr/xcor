#!/usr/bin/python
"""program to combine modules written for the pre-processing of
continous data before the cross-correlation\n
$Log$
Revision 1.7  2007/07/30 22:38:35  behrya
'config' variable added

Revision 1.6  2007-07-20 03:26:15  behrya
'justCOR' added

Revision 1.5  2007-07-05 05:43:28  behrya
*** empty log message ***

Revision 1.4  2007-07-05 05:26:29  behrya
added option '-c' for alternative config file

Revision 1.3  2007-07-05 01:47:41  behrya
nothing new

Revision 1.2  2007-07-03 02:32:29  behrya
changed dir structure and removed some temporary files

"""
import sys
sys.path.append('./modules')
import seed_db, string, os, do_whiten
from ConfigParser import SafeConfigParser

def confirm(progname):
    print "Next step is: ", progname
    print "Press 'y' if you want to continue or 'n' if you want to abort!"
    val = sys.stdin.readline()
    while 1:
        if string.find(val,'y')!=-1:
            return 1
        elif string.find(val, 'n')!=-1:
            return 0
        else:
            print "Please answer the question with 'y' or 'n' (case sensitive!)"
            val = sys.stdin.readline()
        
cp = SafeConfigParser()
config='./config.txt'
try:
    if string.find(sys.argv[1],'-c')!=-1:
        config=sys.argv[2]
        print "config file is: ",sys.argv[2]
    else:
        print "config file is config.txt"
except Exception:
    print "config file is config.txt"

cp.read(config)

err = 0
if cp.get('processing','initdb')=='1':
    seedb = seed_db.Initialize_DB(cp)
    if cp.get('database','datatype') == 'seed':
        err = seedb.start_seed_db()
if cp.get('processing','seed2sac')=='1' and err==0:
    err = os.system('./sa_from_seed_mod -c '+config)
elif err!=0:
    print "call of 'seed_db.py' returned non-Null value"
    exit
    
if cp.get('processing','rmresp')=='1' and err==0:
    command = './cut_trans_mod '+cp.get("processing","lowercut")+' '+\
              cp.get("processing","uppercut")+' -c '+config
    err = os.system(command)
elif err!=0:
    print "system call of 'sa_from_seed_mod' returned non-Null value"
    exit

if cp.get('processing','white')=='1' and err==0:
    dowh = do_whiten.DoWhiten(cp, config)
    err = dowh.start()
elif err!=0:
    print "system call of 'cut_trans_mod' returned non-Null value"
    exit

if cp.get('processing','xcorr')=='1'and err==0:
    command = './justCOR -c '+config
    err = os.system(command)
elif err!=0:
    print "call of 'do_whiten.py' returned non-Null value"
    exit

if cp.get('processing','stack')=='1' and err==0:
    command = './newstack -c '+config
    err = os.system(command)
elif err!=0:
    print "system call of 'justCOR' returned non-Null value"
    exit

if cp.get('processing','sym')=='1' and err==0:
    command = './new_ch_lag -c '+config
    err = os.system(command)
elif err!=0:
    print "system call of 'newstack' returned non-Null value"
    exit

if cp.get('processing','ftan')=='1' and err==0:
    command = './ftandriver -c '+config
    err = os.system(command)
elif err!=0:
    print "system call of 'new_ch_lag' returned non-Null value"
    exit

if cp.get('processing','ftan')=='1' and err!=0:
    print "system call of 'ftandriver' returned non-Null value"
    exit
