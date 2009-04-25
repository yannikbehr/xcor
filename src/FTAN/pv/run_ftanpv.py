#!/usr/bin/python


"""driver for ftan method to measure phase-velocities"""
import os, sys, string, glob
sys.path.append('/home/behrya/dev/proc-scripts')
import pysacio as p
import ftanpv
from pylab import *

####################### FTAN PARAMETERS #######################
t0      = 0
nfin    = 32
npoints = 10
perc    = 50.0
dt      = 1
vmin    = 1.
vmax    = 5.
tmin    = 4.
tmax    = 40.
thresh  = 20.
taperl  = 0.5
snr     = 0.2
fmatch  = 2.0
piover4 = -1
ffact   = 1


############## result from fanchi's code 1st FTAN run ######
compdisp = './COR_GSC_R06C.SAC_s_1_DISP.1'
f = open(compdisp,'r')
vel = []; per = []
for i in f.readlines():
    a=i.split()
    per.append(a[1])
    vel.append(a[3])
f.close()

############## result from fanchi's code 2nd FTAN run ######
compdisp = './COR_GSC_R06C.SAC_s_2_DISP.1'
f = open(compdisp,'r')
vel1 = []; per1 = []
for i in f.readlines():
    a=i.split()
    per1.append(a[1])
    vel1.append(a[3])
f.close()

################################## 1st FTAN run ##################################

fn = './COR_GSC_R06C.SAC_s'
[hf,hi,hs,seis,ok] = p.ReadSacFile(fn)
stat1 = string.rstrip(p.GetHvalue('kstnm',hf,hi,hs))
stat2 = string.rstrip(p.GetHvalue('kevnm',hf,hi,hs))
n = p.GetHvalue('npts',hf,hi,hs)
delta = p.GetHvalue('dist',hf,hi,hs)
times = arange(int(delta/vmax),int(delta/vmin))
vels  = [ delta/i for i in times]

trace = zeros(32768)
for i in range(0,len(seis)):
    if i < 32767:
        trace[i] = seis[i]

phper = [18,20,25,29,33,40,50,67,83,100,111,125,143]
phvel = [3.450,3.530,3.653,3.712,3.761,3.793,3.815,3.854,3.910,3.978,4.027,4.088,4.179]
phprper = zeros(300)
phprvel = zeros(300)
nphpr = len(phper)
for i in range(0,nphpr):
    phprper[i] = phper[i]
    phprvel[i] = phvel[i]

nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,amp,ierr = ftanpv.aftanpg(piover4,n,trace,t0,dt,
                                                                 delta,vmin,vmax,tmin,
                                                                 tmax,thresh,ffact,perc,
                                                                 npoints,taperl,nfin,snr,
                                                                 nphpr,phprper,phprvel)
        
if ierr == 2 or ierr == 1 or nfout2 == 2:
    print "ERROR in ftan "
    exit

subplot(2,1,1)
x = array(arr2[0][0:nrow])
y = array(vels)
z = amp[0:len(vels),0:nrow]
plot(x,arr2[2][0:nrow],'k')
plot(per,vel,'b--')
contourf(x,y,z,250)
xlabel('Period [s]')
ylabel('Group velocity [km/s]')



################################## 2nd FTAN run ##################################

pred = zeros((300,2))
for i in range(0,nfout2):
    pred[i][0] = arr2[1][i]
    pred[i][1] = arr2[2][i]

ffact = 2.0
fmatch = 2.0
npred  = nfout2
tmin = arr2[1][0];
tmax = arr2[1][nfout2-1];
amp   = []
arr1  = []
arr2  = []


nfout1,arr1,nfout2,arr2,tamp,nrow,ncol,amp,ierr = ftanpv.aftanipg(piover4,n,trace,t0,dt,
                                                                  delta,vmin,vmax,tmin,
                                                                  tmax,thresh,ffact,perc,
                                                                  npoints,taperl,nfin,
                                                                  snr,fmatch,npred,pred,
                                                                  nphpr,phprper,phprvel)



if ierr == 2 or ierr == 1 or nfout2 == 2:
    print "ERROR in ftan "
    exit

subplot(2,1,2)
x = array(arr2[0][0:nrow])
y = array(vels)
z = amp[0:len(vels),0:nrow]
plot(x,arr2[2][0:nrow],'k')
plot(per1,vel1,'b--')
contourf(x,y,z,250)
xlabel('Period [s]')
ylabel('Group velocity [km/s]')
show()
