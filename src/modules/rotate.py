#!/usr/bin/env mypython
import numpy as np
import array as a
from obspy.sac import *
#import pysacio as p
import os.path, glob, re, sys, string
from ConfigParser import SafeConfigParser
from math import *
sys.path.append('/home/behrya/dev/proc-scripts/')
import delaz

DEBUG = True

def one_pair(sacfile, stat1, stat2, sacbin):
    saccmd = sacbin+' 1>/dev/null'
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
    print >>child, "quit"
    err = child.close()
    if err:
        raise RuntimeError, '%r failed with exit code %d' %(saccmd, err)
    return 0



if __name__ == '__main__':

    try:
        if string.find(sys.argv[1],'-c')!=-1:
            config=sys.argv[2]
            print "config file is: ",sys.argv[2]
            cp = SafeConfigParser()
            cp.read(config)
            stackdir = cp.get('rotate','stackdir')
            sacbin   = cp.get('rotate','sacbin')
        else:
            print "encountered unknown command line argument"
            raise Exception
    except Exception:
        print "no configuration file found"
        sys.exit(1)

    pattern  = r'COR_(\w*_\w*).SAC_(EE\w*)'
    statpair = {}
    for myfile in glob.glob(stackdir+'/COR*.SAC_EE*'):
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
            if j != 'EE_s':
                try:
                    fn_ee = statpair[i][j]
                    #[hfEE,hiEE,hsEE,seisEE,okEE] = p.ReadSacFile(fn_ee)
                    tr_ee = SacIO(fn_ee)
                    #if not okEE:
                    #    print "ERROR: cannot read in sacfile %s!" %(fn_ee)
                    fn_nn = fn_ee.replace('EE','NN')
                    tr_nn = SacIO(fn_nn)
                    #[hfNN,hiNN,hsNN,seisNN,okNN] = p.ReadSacFile(fn_nn)
                    #if not okNN:
                    #    print "ERROR: cannot read in sacfile %s!" %(fn_nn)
                    fn_en = fn_ee.replace('EE','EN')
                    tr_en = SacIO(fn_en)
                    #[hfEN,hiEN,hsEN,seisEN,okEN] = p.ReadSacFile(fn_en)
                    #if not okEN:
                    #    print "ERROR: cannot read in sacfile %s!" %(fn_en)
                    fn_ne = fn_ee.replace('EE','NE')
                    tr_ne = SacIO(fn_ne)
                    #[hfNE,hiNE,hsNE,seisNE,okNE] = p.ReadSacFile(fn_ne)
                    #if not okNE:
                    #    print "ERROR: cannot read in sacfile %s!" %(fn_ne)
                    #if DEBUG:
                    #    print fn_ee
                    #    print fn_nn
                    #    print fn_en
                    #    print fn_ne
                except SacIOError,e:
                    print e
                    continue
            #st1lat = hfNN[31]
            #st1lon = hfNN[32]
            #st2lat = hfNN[35]
            #st2lon = hfNN[36]
            st1lat = tr_nn.stla
            st1lon = tr_nn.stlo
            st2lat = tr_nn.evla
            st2lon = tr_nn.evlo
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
            #tracemat = np.array([seisEE,seisEN,seisNN,seisNE])
            tracemat = np.array([tr_ee.seis,tr_en.seis,tr_nn.seis,tr_ne.seis])
            resmat = np.dot(rotmat, tracemat)
            fileTT = fn_ee.replace('EE','TT')
            fileRR = fn_ee.replace('EE','RR')
            fileTR = fn_ee.replace('EE','TR')
            fileRT = fn_ee.replace('EE','RT')
            tr_nn.seis = resmat[0,:]
            tr_nn.WriteSacBinary(fileTT)
            tr_nn.seis = resmat[1,:]
            tr_nn.WriteSacBinary(fileRR)
            tr_nn.seis = resmat[2,:]
            tr_nn.WriteSacBinary(fileTR)
            tr_nn.seis = resmat[3,:]
            tr_nn.WriteSacBinary(fileRT)
            #p.WriteSacBinary(fileTT, hfNN, hiNN, hsNN, a.array('f',resmat.tolist()[0]))
            #p.WriteSacBinary(fileRR, hfNN, hiNN, hsNN, a.array('f',resmat.tolist()[1]))
            #p.WriteSacBinary(fileTR, hfNN, hiNN, hsNN, a.array('f',resmat.tolist()[2]))
            #p.WriteSacBinary(fileRT, hfNN, hiNN, hsNN, a.array('f',resmat.tolist()[3]))
            stations = i.split('_')
            stat1 = stations[0]; stat2 = stations[1]
            if DEBUG:
                print "writing: ",fileTT
            one_pair(fileTT, stat1, stat2, sacbin)
            if DEBUG:
                print "writing: ",fileRR
            one_pair(fileRR, stat1, stat2, sacbin)
            if DEBUG:
                print "writing: ",fileTR
            one_pair(fileTR, stat1, stat2, sacbin)
            if DEBUG:
                print "writing: ",fileRT
            one_pair(fileRT, stat1, stat2, sacbin)
        
            
