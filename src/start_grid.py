#! /usr/bin/env mypython
import os, os.path, sys, glob

DEBUG = False

def makeConfig(routine,dbname,tmpdir,dbdir):
    """
    Create a config.txt_ style file different routines using params in this script.
    """
    date = os.path.basename(dbname).split('_')
    tmpcnf = routine+'_'+date[2]+'_'+date[3]+'_'+date[4]+'.txt'
    # if cnffile is already the    re, remove it
    if os.path.isfile(tmpcnf):
        os.remove(tmpcnf)
        
    if routine is 'rm_resp':
        
        # Define config values for rm_resp
        # start_t
        # npts
        # rm_opt
        # sampling
        # plow
        # phigh
        # prefix
        
        start_t  = "1000"
        npts     = "84000"
        rm_opt   = "1"
        sampling = "1.0"
        plow     = "160."
        phigh    = "4."
        prefix = "ft"
        
        # Write config file
        
        output = open(os.path.join(tmpdir,tmpcnf),"w")
        outlines = []
        outlines.append("[rm_resp]\n")
        outlines.append("sacbin=/usr/local/sac101.3b/bin/sac\n")
        outlines.append("prefix="+prefix+"\n")
        outlines.append("dbname="+dbname+"\n")
        outlines.append("tmpdir="+dbdir+"\n")
        outlines.append("start_t="+start_t+"\n")
        outlines.append("npts="+npts+"\n")
        # 1 = eval resp, 0 = pole-zero file
        outlines.append("rm_opt="+rm_opt+"\n")
        outlines.append("sampling="+sampling+"\n")
        outlines.append("plow="+plow+"\n")
        outlines.append("phigh="+phigh+"\n")
        output.writelines(outlines)
        output.close()
        
        return os.path.join(tmpdir,tmpcnf)
    
    if routine is 'whiten':
        
        # Define config values for whitening
        # rootdir (where to store bandpass files)
        # upperperiod
        # lowerperiod
        # polarity
        # plow
        # phigh
        
        rootdir = "/Users/home/carrizad/test/sac/"
        upperperiod = "5"
        lowerperiod = "100"
        polarity    = "vertical"
        bindir      = "/Users/home/carrizad/xcorr/bin/"
        
        output = open(os.path.join(tmpdir,tmpcnf),"w")
        outlines = []
        outlines.append("[whitening]\n")
        outlines.append("rootdir="+rootdir+"\n")
        outlines.append("sacbin=/usr/local/sac101.3b/bin/sac\n")
        outlines.append("bindir="+bindir+"\n")
        outlines.append("tmpdir="+dbdir+"\n")
        outlines.append("upperperiod="+upperperiod+"\n")
        outlines.append("lowerperiod="+lowerperiod+"\n")
        outlines.append("dbname="+dbname+"\n")
        outlines.append("polarity="+polarity+"\n")
        output.writelines(outlines)
        output.close()
        
        return os.path.join(tmpdir,tmpcnf)
        
    if routine is 'xcor':
        #Define config values for 'xcor' routine
        # cordir
        # prefix
        # pbdir
        # lag
        
        cordir = 'xcorr'
        pbdir  = '/Users/home/carrizad/test/sac/5.0to100.0'
        lag    = '3000'
        prefix = 'ft'
        
        output = open(os.path.join(tmpdir,tmpcnf),"w")
        outlines = []
        outlines.append("[xcor]\n")
        outlines.append("tmpdir="+dbdir+"\n")
        outlines.append("cordir="+cordir+"\n")
        outlines.append("pbdir="+pbdir+"\n")
        outlines.append("lag="+lag+"\n")
        outlines.append("dbname="+dbname+"\n")
        outlines.append("prefix="+prefix+"\n")
        output.writelines(outlines)
        output.close()
        
        return os.path.join(tmpdir,tmpcnf)
    

    return
        
if __name__ == "__main__":
    
    """ 
    Define config values here
    """
    # Path to xcorr routines (root dir)
    maindir = '/Users/home/carrizad/xcorr'
    # Working directory for scripts (like run_grid.sh)
    workdir = '/Users/home/carrizad/test/'
    # Database directory holding daily sac_DBs
    dbdir = '/Users/home/carrizad/test/tmp/'
    # tmp dir to hold config files (can be quite spammy if you don't remove them!)
    tmpdir = '/Users/home/carrizad/test/configs/'
    # Name of qsubmission script to be produced
    gridcnf = 'py_grid.sh'
    # Name of routine to process
    routine = 'xcor'
    # define mypython just in case
    mypython = '/usr/local/python2/bin/mypython'
    
    # dbname is the prefix for all daily sac_DBs
    dbname = 'sac_db'
    
    
    
    """
    Processing...
    """
    # Paths to routines/legal routine defs
    routines = {'rm_resp':'/src/modules/rm_inst2.py',\
                 'whiten':'/src/modules/do_whiten_new.py',\
                  'xcor':'/bin/justCOR'}
    # Error checking
    if routine not in routines:
        print "Invalid routine specified: %s " % (routine)
        sys.exit(1)
    
    if not os.path.isdir(dbdir):
        print "Database directory doesn't exist! - %s" % (dbdir)
        sys.exit(1)
    
    if os.path.isfile(os.path.join(workdir,gridcnf)):
        os.remove(os.path.join(workdir,gridcnf))
    
    # Create shell script for grid submission
    output = open(os.path.join(workdir,gridcnf),"w")
    outlines = []
    outlines.append("#! /bin/sh\n")
    outlines.append("#$ -o "+workdir+"output.txt\n")
    outlines.append("#$ -e "+workdir+"error.txt\n")
    outlines.append("#$ -wd "+workdir+"\n")
    outlines.append("#$ -S /bin/sh\n")
    outlines.append("export SACHOME=/usr/local/sac101.3b\n")
    outlines.append("export PATH=${PATH}:${SACHOME}/bin\n")
    outlines.append("export SACAUX=${SACHOME}/aux\n")
    outlines.append("export SAC_PPK_LARGE_CROSSHAIRS=1\n")
    outlines.append("export AUTO_SRC="+maindir+"\n")
    outlines.append("#$ -v PATH\n")
    outlines.append("#$ -v SACAUX\n")
    outlines.append("#$ -v SAC_PPK_LARGE_CROSSHAIRS\n")
    outlines.append("#$ -v AUTO_SRC\n")
    outlines.append("#command\n")
    
    if routine == 'xcor':
        # don't prepend python
        outlines.append(maindir+routines['xcor']+" -c ${1}")
    else:
        # do prepend python
        outlines.append(mypython+" "+maindir+routines[routine]+" -c ${1}")
        
    output.writelines(outlines)
    output.close()

    if not os.path.isdir(tmpdir):
        os.mkdir(tmpdir)
    
    for db in glob.glob(os.path.join(dbdir,dbname+'*')):
        tmpcnf = makeConfig(routine,os.path.basename(db),tmpdir,dbdir)
        
        cmd = "qsub -t 1-1 -q all.q -m n " \
        +os.path.join(workdir,gridcnf)+" "+tmpcnf
        if DEBUG:
            print cmd
        else:
            os.system(cmd)

