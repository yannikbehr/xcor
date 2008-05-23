#!/usr/bin/env python
"""program to combine modules written for the processing of
continous data to calculate dispersion curves\n
$Rev: 461 $
$Author$
$LastChangedDate: 2008-01-18 11:46:41 +1300 (Fri, 18 Jan 2008) $
"""
import sys
sys.path.append('../src/modules')
import string, os, do_whiten, mk_ev_table, sendrequest, imaprequest
from ConfigParser import SafeConfigParser

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
bindir=cp.get('local_settings','bindir')

err = 0

################### WRITE ASCII-DB FILE OF SEED DATA ##############
try:
    if cp.get('processing','initevtbl')=='1' and err==0:
        ascdb = mk_ev_table.InitInputEvSeed(cp)
        if cp.get('database','datatype') == 'seed':
            err = ascdb.start_seed_db()
    if err != 0:
        raise Exception
except Exception:
    print "ERROR: while executing seed_db.py"
    sys.exit(1)

####################### CONV SEED 2 SAC AND RM HOLES ###############
try:
    if cp.get('processing','seed2sac')=='1' and err==0:
        err = os.system(bindir+'sa_from_seed_new -c '+config)
    if err != 0:
        raise Exception
except Exception:
    print "ERROR: while executing sa_from_seed_new"
    sys.exit(1)

####################### REINIT SAC_DB.OUT FILE ######################
try:
    if cp.get('processing','initsacdb')=='1':
        err = os.system(bindir+'initsac_db -c '+config)
    if err != 0:
        raise Exception
except Exception:
    print "ERROR: while executing initsac_db"
    sys.exit(1)

####################### REMOVE INSTR. RESP. #########################
try:
    if cp.get('processing','rmresp')=='1' and err==0:
        command = bindir+'cut_trans_mod '+cp.get("processing","lowercut")+' '+\
                  cp.get("processing","uppercut")+' -c '+config
        err = os.system(command)
    if err != 0:
        raise Exception
except Exception:
    print "ERROR: while executing cut_trans_mod"
    sys.exit(1)

######################## WHITENING ##################################
try:
    if cp.get('processing','white')=='1' and err==0:
        dowh = do_whiten.DoWhiten(cp, config)
        err = dowh.start()
    if err != 0:
        raise Exception
except Exception:
    print "ERROR: while executing do_whiten.py"
    sys.exit(1)


######################## X-CORR ######################################
try:
    if cp.get('processing','xcorr')=='1'and err==0:
        up = cp.get('processing','upperperiod')
        lp = cp.get('processing','lowerperiod')
        command = bindir+'justCOR -c '+config+' -p '+up+'to'+lp
        err = os.system(command)
    if err != 0:
        raise Exception
except Exception:
    print "ERROR: while executing justCOR"
    sys.exit(1)

######################## STACK #######################################
try:
    if cp.get('processing','stack')=='1' and err==0:
        command = bindir+'newstack -c '+config
        err = os.system(command)
    if err != 0:
        raise Exception
except Exception:
    print "ERROR: while executing newstack"
    sys.exit(1)

######################## SYMMETRY #####################################
try:
    if cp.get('processing','sym')=='1' and err==0:
        command = bindir+'new_ch_lag -c '+config
        err = os.system(command)
    if err != 0:
        raise Exception
except Exception:
    print "ERROR: while executing new_ch_lag"
    sys.exit(1)

######################## FTAN ##########################################
try:
    if cp.get('processing','ftan')=='1' and err==0:
        command = bindir+'ftandriver -c '+config
        err = os.system(command)
    if err != 0:
        raise Exception
except Exception:
    print "ERROR: while executing ftandriver"
    sys.exit(1)
