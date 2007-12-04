"""perform tests for each processing step\n
$Rev:$
$Author:$
$LastChangedDate:$
"""

import sys, os.path, os, optparse, string
from ConfigParser import SafeConfigParser
from numpy import *

sys.path.append('./modules')
import pysacio

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
        if cp.get('processing','rmresp')=='1':
            print "--------------------------------------"
            print "TESTING: cut_trans_mod"
            print "--------------------------------------"
            err = 0
            print "-->writing sac_db.out file"
            try:
                err = os.system('./initsac_db -c '+options.configfile)
                if err != 0:
                    raise Exception
            except Exception:
                print "ERROR: initsac_db didn't complete normally"
                sys.exit(1)
            else:
                try:
                    print "-->running cut_trans_mod"
                    tmpdir = cp.get("database","tmpdir")
                    command = './cut_trans_mod '+cp.get("processing","lowercut")+' '+\
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
                            