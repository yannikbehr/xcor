#!/usr/bin/env python
"""perform tests for each processing step\n
$Rev:$
$Author$
$LastChangedDate:$
"""

import sys, os.path, os, getopt, string, shutil, glob
from ConfigParser import SafeConfigParser
from numpy import *

sys.path.append('../src/modules')
import pysacio, do_whiten_new, mk_ev_table

########################## COMMAND LINE ARGUMENTS ###################################
USAGE = """usage: %s proc-step [-c] [-h]
where:
   -c     -> alternative config file (default is './config.txt')
   -h     -> usage
""" %(sys.argv[0])


def doCommandLine():
    """ Get command line options, print usage message if incorrect.
    """
    args_d = {
        'cfile': './config.txt' ,
        }
    
    try:
        proc_step = sys.argv[1]
    except Exception:
        print USAGE
        sys.exit(1)
    try:
        opts, args = getopt.getopt(sys.argv[2:], 'hc:')
    except getopt.GetoptError, e:
        print >>sys.stderr, sys.argv[0] + ': ' + str(e)
        sys.exit(-1)

    if not opts:
        if not os.path.isfile('./config.txt'):
            print "ERROR: please pass valid config filename"
            print USAGE
            sys.exit(1)
        else:
            return proc_step, args_d

    for opt, val in opts:
        if opt in ['-h']:
            print USAGE
            sys.exit(0)
        elif opt in ['-c']:
            if os.path.isfile(val):
                args_d['cfile'] = val
            else:
                print "ERROR: config file is not a valid file!"
                sys.exit(1)
        else:
            print USAGE
            sys.exit(-1)

    return proc_step, args_d


if __name__ == '__main__':

    step, args_d = doCommandLine()
    configfile = args_d['cfile']
    cp = SafeConfigParser()
    cp.read(configfile)

############################### TESTING SA_FROM_SEED ############################
    if step == '1':
        print "--------------------------------------"
        print "TESTING: sa_from_seed_new"
        print "--------------------------------------"
        err = 0
        try:
            print "-->creating dir-structure"
            sacdir = cp.get('database','sacdirroot')
            if not os.path.isdir(sacdir):
                os.mkdir(sacdir)
                os.mkdir(sacdir+'/2006')
                os.mkdir(sacdir+'2006/Sep')
        except Exception, e:
            print "ERROR: cannot create test dir-structure", e
            sys.exit(1)
        try:
            print "-->running sa_from_seed_new"
            err = os.system('../bin/sa_from_seed_new -c '+configfile+' > /dev/null')
            if err != 0:
                raise Exception
        except Exception:
            print "ERROR: executing sa_from_seed_new not succesful!"
            sys.exit(1)
        else:
            try:
                print "-->comparing results with fanchi's"
                file1 = "./testdata/test_h/2006/Sep/2006_9_10_0_0_0/116A.LHE.SAC"
                file2 = "./testdata/test_h/2006/Sep/2006_9_10_0_0_0/R06C.LHE.SAC"
                fcmp1 = "./testdata/fanchi_horiz/Sep/2006_9_10_0_0_0/116A.LHE.SAC"
                fcmp2 = "./testdata/fanchi_horiz/Sep/2006_9_10_0_0_0/R06C.LHE.SAC"
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
                    print "-->testing sa_from_seed_new was succesful"
                    # cleaning up
                    tmpdir = cp.get('database','tmpdir')
                    sacdir = cp.get('database','sacdirroot')
                    #if os.path.isdir(sacdir):
                    #    shutil.rmtree(sacdir)
                    if os.path.isfile(tmpdir+'from_seed'):
                        os.remove(tmpdir+'from_seed')
                    if os.path.isfile(tmpdir+'sac_db.out'):
                        os.remove(tmpdir+'sac_db.out')
                    for i in glob.glob('./rdseed.err_log.*'):
                        os.remove(i)
                    print "--------------------------------------"


################################ TESTING CUT_TRANS_MOD ##############################
    if step == '2':
        print "--------------------------------------"
        print "TESTING: cut_trans_mod"
        print "--------------------------------------"
        err = 0
        print "-->writing sac_db.out file"
        try:
            err = os.system('../bin/initsac_db -c '+configfile)
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
                          cp.get("processing","uppercut")+' -c '+configfile+\
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
                    refdir = './testdata/fanchi_horiz/Sep/2006_9_10_0_0_0/'
                    testdir = './testdata/test_h/2006/Sep/2006_9_10_0_0_0/'
                    file1 = testdir+"ft_116A.LHE.SAC"
                    file2 = testdir+"ft_R06C.LHE.SAC"
                    fcmp1 = refdir+"ft_116A.LHE.SAC"
                    fcmp2 = refdir+"ft_R06C.LHE.SAC"
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
                        os.remove(tmpdir+"sac_db.out")
                        os.remove(tmpdir+"sac_bp_respcor")
                        print "--------------------------------------"


################################ TESTING DO_WHITEN #################################
    if step == '3':
        print "--------------------------------------"
        print "TESTING: do_whiten"
        print "--------------------------------------"
        print "-->running do_whiten_new.py"
#        dowh = do_whiten_new.DoWhiten(configfile)
#        os.path.walk(dowh.sacdir, dowh.dir_walk, 0)
#        dowh.process()
        try:
            print "-->comparing results with fanchi's"
            refdir = './testdata/fanchi_horiz/Sep/5to100_EN/2006_9_9_0_0_0/'
            testdir = './testdata/fanchi_horiz/Sep/5to100/2006_9_9_0_0_0/'
            file1 = refdir+"ft_R06C.LHE.SAC.am"
            file2 = refdir+"ft_116A.LHE.SAC.am"
            fcmp1 = testdir+"ft_R06C.LHE.SAC.am"
            fcmp2 = testdir+"ft_116A.LHE.SAC.am"
#            file1 = refdir+"ft_R06C.LHE.SAC.am"
#            file2 = refdir+"ft_R06C.LHE.SAC.ph"
#            fcmp1 = testdir+"ft_R06C.LHE.SAC.am"
#            fcmp2 = testdir+"ft_R06C.LHE.SAC.ph"
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


################################ TESTING XCORR #################################
    if step == '4':
        print "--------------------------------------"
        print "TESTING: x-correlation"
        print "--------------------------------------"
        print "-->writing sac_db.out file"
        err = 0
        try:
            err = os.system('../bin/initsac_db -c '+configfile)
            if err != 0:
                raise Exception
        except Exception:
            print "ERROR: initsac_db didn't complete normally"
            sys.exit(1)
        else:
            print "-->running justCOR_EE_EN"
            err = os.system('../bin/justCOR_EE_EN -c '+configfile)


################################ TESTING ROTATION #################################
    if step == '4':
        print "--------------------------------------"
        print "TESTING: rotation"
        print "--------------------------------------"
        print "-->writing sac_db.out file"
        err = 0
        try:
            err = os.system('../bin/initsac_db -c '+configfile)
            if err != 0:
                raise Exception
        except Exception:
            print "ERROR: initsac_db didn't complete normally"
            sys.exit(1)
        else:
            print "-->running justCOR_EE_EN"
            err = os.system('../bin/justCOR_EE_EN -c '+configfile)


#        try:
#            print "-->comparing results with fanchi's"
#            refdir = './testdata/fanchi_horiz/Sep/5to100_EN/2006_9_27_0_0_0/'
#            testdir = './testdata/test_h/2006/Sep/5to100/2006_9_27_0_0_0/'
#            file1 = refdir+"ft_R06C.LHE.SAC"
#            file2 = refdir+"ft_116A.LHE.SAC"
#            fcmp1 = testdir+"ft_R06C.LHE.SAC"
#            fcmp2 = testdir+"ft_116A.LHE.SAC"
##            file1 = refdir+"ft_R06C.LHE.SAC.am"
##            file2 = refdir+"ft_R06C.LHE.SAC.ph"
##            fcmp1 = testdir+"ft_R06C.LHE.SAC.am"
##            fcmp2 = testdir+"ft_R06C.LHE.SAC.ph"
#            [hf1,hi1,hs1,seis1,ok1] = pysacio.ReadSacFile(file1)
#            [hf2,hi2,hs2,seis2,ok2] = pysacio.ReadSacFile(file2)
#            [hf3,hi3,hs3,refseis1,ok3] = pysacio.ReadSacFile(fcmp1)
#            [hf4,hi4,hs4,refseis2,ok4] = pysacio.ReadSacFile(fcmp2)
#            if ok1==0:
#                raise Exception, file1
#            elif ok2==0:
#                raise Exception, file2
#            elif ok3==0:
#                raise Exception, fcmp1
#            elif ok4==0:
#                raise Exception, fcmp2
#        except Exception, e:
#            print "ERROR: cannot read in sac-file ", e
#        else:
#            try:
#                if not all(seis1==refseis1):
#                    raise Exception
#                if not all(seis2==refseis2):
#                    raise Exception
#            except Exception:
#                print "ERROR: test failed"
#                print "       either results are not identical or"
#                print "       test didn't work"
#            else:
#                print "-->testing do_whiten was succesful"



#        def cpfile(arg, dirname, files):
#            ftfiles = glob.glob(dirname+'/ft*.SAC')
#            for f in ftfiles:
#                newdir = testdir+os.path.basename(dirname)
#                if not os.path.isdir(newdir):
#                    os.mkdir(newdir)
#                targ = os.path.join(newdir, os.path.basename(f))
#                print "copy ", f, "to ", targ
#                shutil.copy2(f,targ)
#        #os.path.walk(refdir, cpfile, None)
#        err = 0
