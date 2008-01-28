"""module to modify start and end date of RESP-files according to the
corresponding SAC-files
$Rev$
$Author$
$LastChangedDate$
"""
import sys
sys.path.append('./modules')
import  os, os.path, string, pysacio

class CheckResp:
    """class to check and, if necessary, modify response files"""


    def check_resp(self, file1):
        try:
            stat1 = os.stat(file1)
        except Exception, e:
            "Cannot check resp-file ", file1
        else:
            try:
                dirname, basename = os.path.split(file1)
                explode = string.split(basename,'.')
            except Exception, e:
                print e
            else:
                try:
                    for ffile in os.listdir(dirname):
                        if string.find(ffile, 'SAC')!=-1 and string.find(ffile, explode[2])!=-1:
                            ffile = dirname+'/'+ffile
                            [hf,hi,hs,ok] = pysacio.ReadSacHeader(ffile)
			    khole = pysacio.GetHvalue('khole', hf, hi, hs)
                            if ok == 0:
                                message = "Cannot read in SAC-file-header"
                                raise Exception, message
                except Exception,e:
                    print "Error in pysacio-part: ", message
                else:
                    try:
                        tempfile = file1+'_tmp'
                        output = open(tempfile,'w')
                        input = open(file1,'r')
                        outlines = []
                    except Exception,e:
                        print "problems to open input/output-files ",e
                    else:
                        try:
                            # processing the RESP-file
                            alllines = input.readlines()
                            if len(alllines) < 20:
                                message = "corrupt response file: "+file1
                                output.close()
                                os.remove(tempfile)
                                raise Exception, message
                            
                            for lines in alllines:
			  
                                if string.find(lines,'Location')!=-1:
				    loc_resp1 = string.split(lines)
				    newline = loc_resp1[0]+'     '+loc_resp1[1]+\
				    '    '+khole+'\n'
				    outlines.append(newline)
				
                                elif string.find(lines,'Start date')!=-1:
                                    date_resp1 = string.split(lines)	
                                    date_resp2 = string.split(date_resp1[3],',')
                                    # following line-layout is exactly the one
                                    # from the seed-RESP-file;
                                    hi[1] = hi[1]-1
                                    if hi[1]<10:
                                        yday = '00'+`hi[1]`
                                    elif hi[1]<100:
                                        yday = '0'+`hi[1]`
                                    else:
                                        yday = `hi[1]`
                                    newline = date_resp1[0]+'     '+date_resp1[1]+\
                                              ' '+date_resp1[2]+'  '+`hi[0]`+','+\
                                              yday+','+'00:00:00\n'
                                    outlines.append(newline)
                                #elif string.find(lines,'No Ending Time')!=-1:
                                    #outlines.append(lines)
                                elif string.find(lines,'End date')!=-1:
				    
                                    date_resp1 = string.split(lines)
                                    
				    #date_resp2 = string.split(date_resp1[3],',')
                                    if not 'Not' in (date_resp1[3]):
				       # following line-layout is exactly the one
                                       # from the seed-RESP-file;
                                       hi[1] = hi[1]+2
                                       if hi[1]<10:
                                          yday = '00'+`hi[1]`
                                       elif hi[1]<100:
                                          yday = '0'+`hi[1]`
                                       else:
                                          yday = `hi[1]`
                                       newline = date_resp1[0]+'     '+date_resp1[1]+\
                                              ' '+date_resp1[2]+'    '+`hi[0]`+','\
                                              +yday+','+'23:59:59\n'
                                       outlines.append(newline)
				    else:
				       yday = yday+2
				       newline = date_resp1[0]+'     '+date_resp1[1]+\
                                              ' '+date_resp1[2]+'    '+`hi[0]`+','\
                                              +yday+','+'23:59:59\n'
                                       outlines.append(newline)
                                else:
                                    outlines.append(lines)
                        except Exception,e:
                            print "problems with processing the RESP-files ",e
                            return
                        else:
                            try:
                                # writing new temporary RESP-file and
                                # copying it to the original one
                                input.close()
                                output.writelines(outlines)
                                output.close()
                                os.rename(tempfile,file1)
                            except Exception,e:
                                print "problems with closing or writing ",e
                        
    def walk_dir(self, sac1):
        try:
            print "checking: ", sac1
            os.path.isdir(sac1)
        except Exception, e:
            print "ERROR: directory doesn't exist: ", e
        else:
            try:
                list1 = os.listdir(sac1)
                for a in list1:
                    newsac1 = sac1+'/'+a
                    if string.find(a, 'SAC')!=-1:                        
                        pass
                    elif string.find(a, 'RESP')!=-1:
                        #print a
                        self.check_resp(newsac1)
                    elif os.path.isfile(newsac1):
                        continue
                    else:
                        self.walk_dir(newsac1)
            except Exception, e:
                print "ERROR in comparing lists", e

if __name__ == '__main__':
    test = CheckResp()
    test.walk_dir('/Users/home/rawlinza/Zara/sac_from_seed/Tasmanxcor/')
