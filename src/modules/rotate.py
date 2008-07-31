#!/usr/bin/env python
import numpy as np
import array as a
import pysacio as p
import os.path, glob, re, sys
from math import *
sys.path.append('/home/behrya/dev/proc-scripts/')
import delaz

def one_pair(sacfile, stat1, stat2):
    sacbin = '/Volumes/data/yannik78/src/linux/sac/bin/'
    saccmd = sacbin+'/sac 1>/dev/null'
    child = os.popen(saccmd, 'w')
    print >>child, "r %s" %(sacfile)
    print >>child, "ch kevnm %s" %(stat1)
    print >>child, "ch kstnm %s" %(stat2)
    print >>child, "w %s" %(sacfile)
    print >>child, "cut 0 2900"
    print >>child, "r %s" %(sacfile)
    print >>child, "ch o 0"
    print >>child, "ch kevnm %s" %(stat1)
    print >>child, "w %s_p" %(sacfile)
    print >>child, "cut -2900 0"
    print >>child, "r %s" %(sacfile)
    print >>child, "reverse"
    print >>child, "ch b 0"
    print >>child, "ch e 2900"
    print >>child, "ch o 0"
    print >>child, "w %s_n" %(sacfile)
    print >>child, "cut off"
    print >>child, "addf %s_p" %(sacfile)
    print >>child, "ch o 0"
    print >>child, "div 2"
    print >>child, "w %s_s" %(sacfile)
    err = child.close()
    if err:
        raise RuntimeError, '%r failed with exit code %d' %(saccmd, err)
    return 0



if __name__ == '__main__':

    stackdir = '/home/behrya/dev/auto/testing/testdata/fanchi_horiz/STACK'
    pattern  = r'COR_(\w*_\w*).SAC_(\w*)'
    statpair = {}
    for myfile in glob.glob(stackdir+'/COR*.SAC*'):
        mt = re.search(pattern, myfile)
        if mt:
            if mt.group(1) not in statpair.keys():
                statpair[mt.group(1)] = {}
                statpair[mt.group(1)][mt.group(2)] = myfile
            elif mt.group(2) not in statpair[mt.group(1)].keys():
                statpair[mt.group(1)][mt.group(2)] = myfile
            else:
                print 'ERROR: cannot assign %s to dictionary!' %(myfile)

    for i in statpair.keys():
        for j in statpair[i].keys():
            if j == 'EE':
                [hfEE,hiEE,hsEE,seisEE,okEE] = p.ReadSacFile(statpair[i][j])
                if not okEE:
                    print "ERROR: cannot read in sacfile %s!" %(statpair[i][j])
            if j == 'NN':
                [hfNN,hiNN,hsNN,seisNN,okNN] = p.ReadSacFile(statpair[i][j])
                if not okNN:
                    print "ERROR: cannot read in sacfile %s!" %(statpair[i][j])
            if j == 'EN':
                [hfEN,hiEN,hsEN,seisEN,okEN] = p.ReadSacFile(statpair[i][j])
                if not okEN:
                    print "ERROR: cannot read in sacfile %s!" %(statpair[i][j])
            if j == 'NE':
                [hfNE,hiNE,hsNE,seisNE,okNE] = p.ReadSacFile(statpair[i][j])
                if not okNE:
                    print "ERROR: cannot read in sacfile %s!" %(statpair[i][j])
        st1lat = hfNN[31]
        st1lon = hfNN[32]
        st2lat = hfNN[35]
        st2lon = hfNN[36]
        dist, az, baz = delaz.delaz(st1lat, st1lon, st2lat, st2lon, 0)
        tmp1 = ((az - 180)/180)*pi
        cos1=cos(tmp1);
        sin1=sin(tmp1);
        tmp2 = ((baz -180)/180.0)*pi
        cos2=cos(tmp2);
        sin2=sin(tmp2);
        #print i,tmp1,sin1,cos1,tmp2,sin2,cos2
        rotmat = np.array([[-1*cos1*cos2, +cos1*sin2, -sin1*sin2, sin1*cos2],
                           [-1*sin1*sin2, -sin1*cos2, -cos1*cos2, -cos1*sin2],
                           [-1*cos1*sin2, -cos1*cos2, sin1*cos2, sin1*sin2],
                           [-1*sin1*cos2, sin1*sin2, cos1*sin2, -cos1*cos2]])
        tracemat = np.array([seisEE,seisEN,seisNN,seisNE])
        resmat = np.dot(rotmat, tracemat)
        fileTT = os.path.join(stackdir,'COR_'+i+'.SAC_TT')
        fileRR = os.path.join(stackdir,'COR_'+i+'.SAC_RR')
        fileTR = os.path.join(stackdir,'COR_'+i+'.SAC_TR')
        fileRT = os.path.join(stackdir,'COR_'+i+'.SAC_RT')
        p.WriteSacBinary(fileTT, hfNN, hiNN, hsNN, a.array('f',resmat.tolist()[0]))
        p.WriteSacBinary(fileRR, hfNN, hiNN, hsNN, a.array('f',resmat.tolist()[1]))
        p.WriteSacBinary(fileTR, hfNN, hiNN, hsNN, a.array('f',resmat.tolist()[2]))
        p.WriteSacBinary(fileRT, hfNN, hiNN, hsNN, a.array('f',resmat.tolist()[3]))
        stations = i.split('_')
        stat1 = stations[0]; stat2 = stations[1]
        one_pair(fileTT, stat1, stat2)
        one_pair(fileRR, stat1, stat2)
        one_pair(fileTR, stat1, stat2)
        one_pair(fileRT, stat1, stat2)
        
            
