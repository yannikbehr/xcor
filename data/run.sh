#!/bin/bash 

MAIN=/home/behrya/dev/auto/
CONFIG=config.txt
LOG=run_log.txt

# write configuration file
cat > ${CONFIG} <<EOF
[seed2sac]
rdseedir=/home/behrya/src/rdseed4.7.5/          
bindir=../bin/                                   
seedfiles=./testdata/fanchi_horiz/seed/
seedfilere=S-*
sacfiles=./testdata/test_sac_from_seed/

[mseed2sac]
rdseedir=/home/behrya/src/rdseed4.7.5/          
bindir=../bin/                                   
mseedir=./mseed/                                
sacfiles=./SacFiles/                            
dataless=./nz.dataless.seed                     
respfiles=./RespFiles/                          

[init_sacdb]
search_directories=./SacFiles/                  
skip_directories=5to100, eqband, 1to40          
search_string=[!^ft]*HZ.SAC                     
prefix=ft
tmpdir=./tmp/                                   
# flag=0 -> take npts and delta from raw files
# flga=1 -> take npts and delta from ft-files
flag=0

[rm_resp]
sacdir=/usr/local/bin/               
tmpdir=./tmp/                                   
prefix=ft
start_t=1000                                    
npts=84000
# 1=evalresp; 0=pole-zero file
rm_opt=1


[whitening]
sacfiles=./SacFiles/
sacdir=/usr/local/bin/
bindir=../bin/
prefix=ft
upperperiod=5
lowerperiod=100
prefix=ft
complist=LHZ

[xcor]
tmpdir=./tmp/
cordir=./Results/XCor/
pbdir=5to100
lag=3000

[stack]
cordir=./Results/XCor/2001/
stackdir=./Results/XCor/stack/

[rotate]
sacdir=/usr/local/bin/
stackdir=./Results/XCor/stack/

[FTAN]
corfiles=./Results/XCor/stack/

#minimal group velocity, km/s
vmin=1.5
#maximal value of the group velocity, km/s
vmax=5  	
#minimal period, s
tmin=5
#maximal period, s   	
tmax=50  	
#treshold, usualy = 10
thresh=10	
#factor to automatic filter parameter, usualy =1
ffact=1  	
#factor for the left end seismogram tapering,taper = taperl*tmax
taperl=1 	
#signal-to-noise ratio (not used like that in ftan-code!!!)
snr=0.1  	
EOF

if [ ! -e ${LOG} ] ;then
    echo "Logfile for script 'run.sh'" >${LOG}
    echo "-----------------------------------------------" >>${LOG}
    echo `date` >>${LOG}
    echo ""
    echo "-----------------------------------------------" >>${LOG}
    more ${0} >>${LOG}
else
    echo "-----------------------------------------------" >>${LOG}
    echo `date` >>${LOG}
    echo ""
    echo "-----------------------------------------------" >>${LOG}
    more ${0} >>${LOG}
fi


# mseed -> sac
#${MAIN}/src/modules/sac_from_mseed.py -c ${CONFIG}

# seed -> sac
#${MAIN}/src/modules/sac_from_seed.py -c ${CONFIG}

# init database file that is used by later
# processing steps
#${MAIN}/bin/initsac_db -c ${CONFIG}

# remove instrument response and cut trace
#${MAIN}/bin/cut_trans_mod -c ${CONFIG}

# whiten spectrum and downweight earthquakes 
#${MAIN}/src/modules/do_whiten_new.py -c ${CONFIG}

# cross correlation
#${MAIN}/bin/justCOR -c ${CONFIG}

# cross correlation 2 components
#${MAIN}/bin/justCOR_EE_EN -c ${CONFIG}

# stacking
#${MAIN}/src/modules/stack_1cmp.py -c ${CONFIG}

# stacking 2 components
#${MAIN}/src/modules/stack_2cmp.py -c ${CONFIG}

# rotating 2 components into transvers and radial direction
#${MAIN}/src/modules/rotate.py -c ${CONFIG}

# FTAN
#${MAIN}/bin/ftandriver -c ${CONFIG}