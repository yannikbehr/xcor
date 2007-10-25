"""script to test COR-directory; problem: different order of stations
==> as correlations are only calculated once for each station pair
    results might differ concerning file name and can be time reversed\n
$Rev:$
$Author:$
$LastChangedDate:$
"""


import sys
sys.path.append('./modules')
import  os, os.path, string, pysacio, filecmp
from numpy import *

#dir1st = '/home/behrya/dev/nord-sac/fanchi/2003/STACK/SAC/'
#dir2nd = '/home/behrya/dev/disp-monthly/Jan-Feb-Mar-03/STACK/'
dir1st = '/home/behrya/dev/test-auto/UNSORTEDCOR/stacks/'
dir2nd = '/home/behrya/dev/test-auto/SORTEDCOR/stacks/'
#dir1 = '/home/behrya/dev/auto/testcor_auto/'
#dir2 = '/home/behrya/dev/auto/testcor_auto_nosort/'

def check_cor(dir1, dir2):
    """compare correlation results"""
    list1 = os.listdir(dir1)
    list2 = os.listdir(dir2)
    for file1 in list1:
        for file2 in list2:
            if file1.startswith('COR_') and file2.startswith('COR_'):
                stations = []
                base1 = os.path.basename(file1)
                base2 = os.path.basename(file2)
                trunk1 = string.split(base1,'.')
                trunk2 = string.split(base2,'.')
                tmparr1 = string.split(trunk1[0],'_')
                tmparr2 = string.split(trunk2[0],'_')
                stations.append(tmparr1[1])
                stations.append(tmparr1[2])
                stations.append(tmparr2[1])
                stations.append(tmparr2[2])
                for i in range(0,len(stations)):
                    if stations[i] == 'OUZV':
                        stations[i] = 'OUZ'
                    elif stations[i] == 'WCZV':
                        stations[i] = 'WCZ'
                        
                if stations[0] == stations[2] and stations[1] == stations[3] or \
                       stations[0] == stations[3] and stations[1] == stations[2]:
                    print "comparing: ", file1, file2
                    file1 = dir1+'/'+file1
                    file2 = dir2+'/'+file2
                    try:
                        [hf1,hi1,hs1,seis1,ok1] = pysacio.ReadSacFile(file1)
                        [hf2,hi2,hs2,seis2,ok2] = pysacio.ReadSacFile(file2)
                        if ok1==0:
                            raise Exception, file1
                        elif ok2==0:
                            raise Exception, file2
                    except Exception, e:
                        print "Cannot read in sac-file ", e
                    else:
                        if stations[0]==stations[3]:
                            seis1.reverse()
                        if not all(seis1==seis2):
                            print "--->seismic traces are not identical"

if __name__ == '__main__':
    check_cor(dir1st, dir2nd)
