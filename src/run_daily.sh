#!/bin/bash 

MAIN=/Users/home/carrizad/xcorr
CONFIG=config.txt
LOG=run_log.txt
# write configuration file
cat > ${CONFIG} <<EOF

[mseed2sac]
rdseed=/usr/local/bin/rdseed
bindir=${MAIN}/bin   
mseedir=/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/master
outputdir=/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/sac
dataless=/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/X2.GSN.SNZO.dataless
respdir=/Users/home/carrizad/GRID/resp
search_pattern=*.*
# search_pattern=4480.XQ..BHZ.2002.187.D

[init_sacdb]
search_directories=/Users/home/carrizad/GRID/array/sac
resp_dir=/Users/home/carrizad/GRID/resp
dbname=sac_db
skip_directories=5.0to100.0,eqband,1to40
search_string=[!^ft_grid]*Z.SAC                     
prefix=ft_grid
tmpdir=/Users/home/carrizad/GRID/scripts/array/daily/
# flag=0 -> take npts and delta from raw files
# flag=1 -> take npts and delta from ft-files
flag=1

[rm_resp]
sacbin=/usr/local/sac101.3b/bin/sac           
tmpdir=./tmp/                                   
prefix=ft
start_t=1000                                    
npts=84000
# 1=evalresp; 0=pole-zero file
rm_opt=1
dbname=sac_db_SAHKE_array_100.0
sampling=100.0
plow=160.
phigh=4.

[whitening]
rootdir=/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/sac
sacbin=/usr/local/sac101.3b/bin/sac101
bindir=${MAIN}/bindir
upperperiod=5
lowerperiod=100
dbname=sac_db_SAHKE_array_100.0
tmpdir=/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/tmp/
polarity=vertical

[xcor]
tmpdir=/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/array/tmp/
cordir=/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/xcorr/array/
pbdir=5.0to100.0
lag=3000
dbname=sac_db_SAHKE_array_100.0
prefix=ft

[stack]
cordir=/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/xcorr/array/
stackdir=/Volumes/GeoPhysics_05/users-data/carrizad/SAHKE/xcorr/array/stack
spattern=COR_(\w*_\w*).SAC

[rotate]
sacdir=/usr/local/bin/
stackdir=./Results/XCor/stack/

[ftan]
cordir=/data/sabine/yannik/Results/stack/96_01_02_03_04_05/
tmpdir=./tmp/
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
#${MAIN}/src/modules/mseed2sac.py -c ${CONFIG}

# init database file that is used by later
# processing steps
mypython ${MAIN}/src/modules/initsac_db_daily.py -c ${CONFIG}

# remove instrument response and cut trace
#${MAIN}/src/modules/rminst2.py -c ${CONFIG}

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
# ${MAIN}/src/myftan.py -c ${CONFIG}
