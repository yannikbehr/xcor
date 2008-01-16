"""class to test COR-directory; problem: different order of stations
==> as correlations are only calculated once for each station pair
    results might differ concerning file name and can be time reversed\n
$Log$
Revision 1.1  2007/07/20 03:26:26  behrya
*** empty log message ***

"""
import sys
sys.path.append('./modules')
import os, string, pysacio
from array import *
from numpy import *

class TestCor:
    """class to compare COR-directories"""
    def __init__(self, dir1, dir2):
        self.dir1 = dir1
        self.dir2 = dir2

    def comp_file_name(self):
        try:
            dirlist1 = os.listdir(self.dir1)
            dirlist2 = os.listdir(self.dir2)
        except os.error,v:
            print "Cannot get dir-content: ", v[0], v[1]
        else:
            try:
                for i in dirlist1:
                    a = string.split(i,'_')
                    b = string.split(a[2],'.')
                    match1='_'+a[1]+'_'+b[0]+'.'
                    match2='_'+b[0]+'_'+a[1]+'.'
                    for j in dirlist2:
                        if string.find(j,match1) != -1 or string.find(j,match2) != -1:
                            self.check_sac_trace(i,j)

            except Exception:
                print "Cannot find any matching filenames"
                
    def check_sac_trace(self, filename1, filename2):
        try:
            file1 = self.dir1+'/'+filename1
            file2 = self.dir2+'/'+filename2
            print "Checking: ", file1, file2
            [hf1,hi1,hs1,seis1,ok1] = pysacio.ReadSacFile(file1)
            [hf2,hi2,hs2,seis2,ok2] = pysacio.ReadSacFile(file2)
            if ok1==0:
                raise Exception, file1
            elif ok2==0:
                raise Exception, file2
        except Exception, e:
            print "Cannot read in sac-file ", e
        else:
            try:
                ok1=pysacio.IsValidSacFile(file1)
                ok2=pysacio.IsValidSacFile(file2)
                if ok1==0:
                    raise Exception, file1
                elif ok2==0:
                    raise Exception, file2
            except Exception, e:
                print e," is not a valid SAC binary file"
#            try:
#                if hf1[6] != hf2[6] or hi1 != hi2 or hs1 != hs2:
#                    message = "some header-values are not identical"
#                    raise Exception, message
#                if len(seis1) != len(seis2):
#                    message = "seismic traces don't have equal length"
#                    raise Exception, message
#            except Exception, e:
#                print "sac-files ", file1, " and ", file2, " are not identical: ", e
            try:
                if filename1 != filename2:
                    seis1.reverse()
                if not all(seis1==seis2):
                    message = "seismic traces are not identical"
                    raise Exception, message
            except Exception, e:
                print "sac-files ", file1, " and ", file2, " are not identical: ", e
        



if __name__ == '__main__':
    TestCor('/home/behrya/dev/sacroot/2005/Apr/5to100/COR','/home/behrya/dev/FanChi/2005/Apr/5to100/COR').comp_file_name()
