"""perform tests for each processing step\n
$Rev:$
$Author$
$LastChangedDate:$
"""

import sys, os.path, os, optparse, string, shutil
from ConfigParser import SafeConfigParser
from numpy import *

sys.path.append('../src/modules')
import pysacio, seed_db, do_whiten, mk_input_ev_seed

########################## COMMAND LINE ARGUMENTS ###################################
cmdargs = []
if len(sys.argv) < 2:
    cmdargs.append("-h")
else:
    cmdargs = sys.argv[1:]
    p = optparse.OptionParser()
    p.add_option('--configfile','-c')
    options, arguments = p.parse_args(args=cmdargs)
    try:
        if os.path.isfile(options.configfile) == 0:
            raise Exception
    except Exception:
        print options.configfile, "is not a valid config filename!",e
    else:
        cp = SafeConfigParser()
        cp.read(options.configfile)

############################# TESTING SA_FROM_SEED_MOD ###############################
        if cp.get('processing','initdb')=='1':
            print "--------------------------------------"
            print "TESTING: sa_from_seed_mod"
            print "--------------------------------------"
            err = 0
            print "-->creating sqlite database file"
            try:
                seedb = seed_db.Initialize_DB(cp)
                if cp.get('database','datatype') == 'seed':
                    sqlitefile = cp.get('database','databasefile')
                    sacdir = cp.get('database','sacdirroot')
                    if os.path.isfile(sqlitefile):
                        os.remove(sqlitefile)
                    if os.path.isdir(sacdir):
                        shutil.rmtree(sacdir)
                    err = seedb.start_seed_db()
                if err != 0:
                    raise Exception
            except Exception:
                print "ERROR: creating sqlite database file not succesful!"
                sys.exit(1)
            else:
                try:
                    print "-->running sa_from_seed_mod"
                    err = os.system('../bin/sa_from_seed_mod -c '+options.configfile+' >/dev/null')
                    if err != 0:
                        raise Exception
                except Exception:
                    print "ERROR: executing sa_from_seed_mod not succesful!"
                    sys.exit(1)
                else:
                    try:
                        print "-->comparing results with fanchi's"
                        file1 = "./testdata/test/2003/Jan/2003_1_2_0_0_0/MATA.BHZ.SAC"
                        file2 = "./testdata/test/2003/Jan/2003_1_2_0_0_0/TIKO.BHZ.SAC"
                        fcmp1 = "./testdata/fanchi/Jan/2003_1_2_0_0_0/MATA.BHZ.SAC"
                        fcmp2 = "./testdata/fanchi/Jan/2003_1_2_0_0_0/TIKO.BHZ.SAC"
                        [hf1,hi1,hs1,seis1,ok1] = pysacio.ReadSacFile(file1)
                        [hf2,hi2,hs2,seis2,ok2] = pysacio.ReadSacFile(file2)
                        [hf3,hi3,hs3,refseis1,ok3] = pysacio.ReadSacFile(fcmp1)
                        [hf4,hi4,hs4,refseis2,ok4] = pysacio.ReadSacFile(fcmp2)
                        if ok1==0:
                            raise Exception, file1
                        elif ok2==0:
                            raise Exception, file2
                        elif ok3==0:
                            raise Exception, fcmp1
                        elif ok4==0:
                            raise Exception, fcmp2
                    except Exception, e:
                        print "ERROR: cannot read in sac-file ", e
                    else:
                        try:
                            if not all(seis1==refseis1):
                                raise Exception
                            if not all(seis2==refseis2):
                                raise Exception
                        except Exception:
                            print "ERROR: test failed"
                            print "       either results are not identical or"
                            print "       test didn't work"
                        else:
                            print "--------------------------------------"
                            print "-->testing sa_from_seed_mod was succesful"
                            # cleaning up
                            tmpdir = cp.get('database','tmpdir')
                            if os.path.isfile(sqlitefile):
                                os.remove(sqlitefile)
                            if os.path.isdir(sacdir):
                                shutil.rmtree(sacdir)
                            if os.path.isfile(tmpdir+'event_station.tbl'):
                                os.remove(tmpdir+'event_station.tbl')
                            if os.path.isfile(tmpdir+'from_seed'):
                                os.remove(tmpdir+'from_seed')
                            if os.path.isfile(tmpdir+'seed_test.db'):
                                os.remove(tmpdir+'seed_test.db')
                            if os.path.isfile(tmpdir+'sac_db.out'):
                                os.remove(tmpdir+'sac_db.out')
                            print "--------------------------------------"


############################### TESTING CUT_TRANS_MOD ##############################
        if cp.get('processing','rmresp')=='1':
            print "--------------------------------------"
            print "TESTING: cut_trans_mod"
            print "--------------------------------------"
            err = 0
            print "-->writing sac_db.out file"
            try:
                err = os.system('../bin/initsac_db -c '+options.configfile)
                if err != 0:
                    raise Exception
            except Exception:
                print "ERROR: initsac_db didn't complete normally"
                sys.exit(1)
            else:
                try:
                    print "-->running cut_trans_mod"
                    tmpdir = cp.get("database","tmpdir")
                    command = '../bin/cut_trans_mod '+cp.get("processing","lowercut")+' '+\
                              cp.get("processing","uppercut")+' -c '+options.configfile+\
                              " >/dev/null"
                    err = os.system(command)
                    if err !=0:
                        raise Exception
                except Exception:
                    print "ERROR: cut_trans_mod didn't execute normally"
                    sys.exit(1)
                else:
                    try:
                        print "-->comparing results with fanchi's"
                        basedir = cp.get("database","sacdirroot")
                        file1 = basedir+"ft_MATA.BHZ.SAC"
                        file2 = basedir+"ft_TIKO.BHZ.SAC"
                        fcmp1 = basedir+"fanchi_ft_MATA.BHZ.SAC"
                        fcmp2 = basedir+"fanchi_ft_TIKO.BHZ.SAC"
                        [hf1,hi1,hs1,seis1,ok1] = pysacio.ReadSacFile(file1)
                        [hf2,hi2,hs2,seis2,ok2] = pysacio.ReadSacFile(file2)
                        [hf3,hi3,hs3,refseis1,ok3] = pysacio.ReadSacFile(fcmp1)
                        [hf4,hi4,hs4,refseis2,ok4] = pysacio.ReadSacFile(fcmp2)
                        if ok1==0:
                            raise Exception, file1
                        elif ok2==0:
                            raise Exception, file2
                        elif ok3==0:
                            raise Exception, fcmp1
                        elif ok4==0:
                            raise Exception, fcmp2
                    except Exception, e:
                        print "ERROR: cannot read in sac-file ", e
                    else:
                        try:
                            if not all(seis1==refseis1):
                                raise Exception
                            if not all(seis2==refseis2):
                                raise Exception
                        except Exception:
                            print "ERROR: test failed"
                            print "       either results are not identical or"
                            print "       test didn't work"
                        else:
                            print "-->testing cut_trans_mod was succesful"
                            os.remove(file1)
                            os.remove(file2)
                            os.remove(tmpdir+"sac_db.out")
                            os.remove(tmpdir+"sac_bp_respcor")
                            print "--------------------------------------"
                            

############################### TESTING DO_WHITEN #################################
        if cp.get('processing','white')=='1':
            print "--------------------------------------"
            print "TESTING: do_whiten"
            print "--------------------------------------"
            err = 0
            try:
                print "-->running do_whiten.py"
                dowh = do_whiten.DoWhiten(cp, options.configfile)
                err = dowh.start()
                if err != 0:
                    raise Exception
            except Exception:
                print "ERROR: while executing do_whiten.py"
                sys.exit(1)
            else:
                try:
                    print "-->comparing results with fanchi's"
                    basedir = cp.get("database","sacdirroot")
                    testdir = basedir+"Jan/"+cp.get("processing","upperperiod")+\
                              "to"+cp.get("processing","lowerperiod")+\
                              "/2003_1_10_0_0_0/"
                    basedir = basedir+"Jan/5to100/2003_1_10_0_0_0/"
                    file1 = basedir+"ft_MATA.BHZ.SAC.am"
                    file2 = basedir+"ft_MATA.BHZ.SAC.ph"
                    fcmp1 = testdir+"ft_MATA.BHZ.SAC.am"
                    fcmp2 = testdir+"ft_MATA.BHZ.SAC.ph"
                    [hf1,hi1,hs1,seis1,ok1] = pysacio.ReadSacFile(file1)
                    [hf2,hi2,hs2,seis2,ok2] = pysacio.ReadSacFile(file2)
                    [hf3,hi3,hs3,refseis1,ok3] = pysacio.ReadSacFile(fcmp1)
                    [hf4,hi4,hs4,refseis2,ok4] = pysacio.ReadSacFile(fcmp2)
                    if ok1==0:
                        raise Exception, file1
                    elif ok2==0:
                        raise Exception, file2
                    elif ok3==0:
                        raise Exception, fcmp1
                    elif ok4==0:
                        raise Exception, fcmp2
                except Exception, e:
                    print "ERROR: cannot read in sac-file ", e
                else:
                    try:
                        if not all(seis1==refseis1):
                            raise Exception
                        if not all(seis2==refseis2):
                            raise Exception
                    except Exception:
                        print "ERROR: test failed"
                        print "       either results are not identical or"
                        print "       test didn't work"
                    else:
                        print "-->testing do_whiten was succesful"
                        # cleaning up
                        tmpdir1 = cp.get("database","tmpdir")
                        tempdir2 = cp.get("database","sacdirroot")+\
                                   "Jan/"+cp.get("processing","upperperiod")+\
                                    "to"+cp.get("processing","lowerperiod")
                        if os.path.isdir(tempdir2):
                            shutil.rmtree(tempdir2)
                        if os.path.isfile(tmpdir1+'param.dat'):
                            os.remove(tmpdir1+'param.dat')
                        if os.path.isfile(tmpdir1+'param_test.dat'):
                            os.remove(tmpdir1+'param_test.dat')
                        print "--------------------------------------"


############################### TESTING MK_INPUT_EV_SEED ############################
        if cp.get('processing','initevseed')=='1':
            print "--------------------------------------"
            print "TESTING: mk_input_ev_seed"
            print "--------------------------------------"
            err = 0
            try:
                print "-->running mk_input_ev_seed.py"
                newev = mk_input_ev_seed.InitInputEvSeed(cp)
                newev.start_seed_db()
            except Exception:
                print "ERROR: while executing mk_input_ev_seed.py"
                sys.exit(1)
            else:
                try:
                    print "-->running sa_from_seed_new"
                    err = os.system('../bin/sa_from_seed_new -c '+options.configfile)
                    if err != 0:
                        raise Exception
                except Exception:
                    print "ERROR: executing sa_from_seed_mod not succesful!"
                    sys.exit(1)
