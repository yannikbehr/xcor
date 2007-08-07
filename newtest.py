"""module to compare directory trees of old an automated version
of Fan Chis Code
\n18/6/2007"""
import sys
sys.path.append('./modules')
import  os, os.path, string, pysacio
from numpy import *
class TestDir:
    """ class to compare dir-structure of automated procedure
    with conventional dir-structure\n
    class needs 2 args at initialisation: 1st arg is dir of
    automated procedure, 2nd arg is dir of conventional procedure"""
    def __init__(self):
        self.count = 0
        self.diff = []
        
    def check_sac_head(self, file1, file2):
        try:
            [hf1,hi1,hs1,seis1,ok1] = pysacio.ReadSacFile(file1)
            [hf2,hi2,hs2,seis2,ok2] = pysacio.ReadSacFile(file2)
            if ok1==0:
                self.diff.append(file1)
                raise Exception, file1
            elif ok2==0:
                self.diff.append(file2)
                raise Exception, file2
        except Exception, e:
            self.count = self.count +1
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
            try:
                if hf1 != hf2 or hi1 != hi2 or hs1 != hs2:
                    message = "some header-values are not identical"
                    raise Exception, message
                if len(seis1) != len(seis2):
                    message = "seismic traces don't have equal length"
                    raise Exception, message
            except Exception, e:
                self.count = self.count + 1
                self.diff.append(file1)
                self.diff.append(file2)
                print "sac-files ", file1, " and ", file2, " are not identical: ", e

    def check_sac_trace(self, file1, file2):
        try:
            [hf1,hi1,hs1,seis1,ok1] = pysacio.ReadSacFile(file1)
            [hf2,hi2,hs2,seis2,ok2] = pysacio.ReadSacFile(file2)
            if ok1==0:
                self.diff.append(file1)
                raise Exception, file1
            elif ok2==0:
                self.diff.append(file2)
                raise Exception, file2
        except Exception, e:
            self.count = self.count +1
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
            try:
                if hf1[6] != hf2[6] or hi1 != hi2 or hs1 != hs2:
                    message = "some header-values are not identical"
                    raise Exception, message
                if len(seis1) != len(seis2):
                    message = "seismic traces don't have equal length"
                    raise Exception, message
            except Exception, e:
                self.count = self.count + 1
                self.diff.append(file1)
                self.diff.append(file2)
                print "sac-files ", file1, " and ", file2, " are not identical: ", e
            try:
                if not all(seis1==seis2):
                    message = "seismic traces are not identical"
                    raise Exception, message
            except Exception, e:
                self.count = self.count + 1
                self.diff.append(file1)
                self.diff.append(file2)
                print "sac-files ", file1, " and ", file2, " are not identical: ", e
        

    def check_resp(self, file1, file2):
        try:
            stat1 = os.stat(file1)
            stat2 = os.stat(file2)
        except Exception, e:
            "Cannot check resp-file ", file1, "or", file2
        else:
            try:
                if stat1.st_size != stat2.st_size:
                    message = "RESP files have not equal size"
                    self.diff.append(file1)
                    self.diff.append(file2)
                    raise Exception, message
            except Exception, e:
                self.count = self.count + 1
                print e
                

    def walk_dir(self, sac1, sac2):
        try:
            print "checking: ", sac1, sac2
            os.path.isdir(sac1)
            os.path.isdir(sac2)
        except Exception, e:
            print "ERROR: one or both directories don't exist: ", e
        else:
            try:
                list1 = os.listdir(sac1)
                list2 = os.listdir(sac2)
                if len(list1) != len(list2):
                    self.diff.append(sac1)
                    self.diff.append(sac2)
                    self.count = self.count+1
                    tmplist = list1 + list2
                    whatsnew = []
                    for item in tmplist:
                        if item not in list1 or item not in list2:
                            whatsnew.append(item)
                    print whatsnew
                    raise Exception, "contents list not of equal length"
                for q,a in zip(list1, list2):
                    if q == a:
                        newsac1 = sac1+'/'+q
                        newsac2 = sac2+'/'+a
                        if string.find(q, 'SAC')!=-1:                        
                            self.check_sac_trace(newsac1, newsac2)
                        elif string.find(q, 'RESP')!=-1:
                            self.check_resp(newsac1, newsac2)
                        else:
                            self.walk_dir(newsac1, newsac2)
                    else:
                        self.diff.append(q)
                        self.diff.append(a)
                        self.count = self.count+1
                        raise Exception, (q,a)
            except Exception, e:
                print "ERROR in comparing lists", e

                
            

    def feedback(self):
        if self.count != 0:
            print "differences occured in: ", self.diff
        else:
            print "directories are identical!"

if __name__ == '__main__':
    test = TestDir()
    test.walk_dir('./COR', '/home/behrya/dev/FanChi/2005/Apr/5to100/COR')
    test.feedback()
    
