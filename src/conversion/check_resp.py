#!/usr/bin/env python
"""module to modify start and end date of RESP-files according to the
corresponding SAC-files
$Rev: 492 $
$Author: $
$LastChangedDate: 2008-01-28 16:41:35 +1300 (Mon, 28 Jan 2008) $
"""
import sys
sys.path.append('./modules')
import  os, os.path, string, pysacio, glob, re

class CheckResp:
    """class to check and, if necessary, modify response files"""
    def __init__(self):
        pass

    def __call__(self, dirname):
        os.path.walk(dirname, self.check_resp, None)
        

    def check_resp(self, arg, dirname, files):
        print dirname
        for fn in glob.glob(dirname+'/[!^ft]*HZ.SAC'):
            [hf,hi,hs,ok] = pysacio.ReadSacHeader(fn)
            if ok == 0:
                print "ERROR: cannot read in SAC-file-header for %s"%(fn)
                return
            else:
                stat  = pysacio.GetHvalue('kstnm', hf, hi, hs).rstrip()
                comp  = pysacio.GetHvalue('kcmpnm', hf, hi, hs).rstrip()
                khole = pysacio.GetHvalue('khole', hf, hi, hs).rstrip()
            respfiles = glob.glob(dirname+'/RESP*'+stat+'*'+comp+'*')
            if len(respfiles) > 1:
                print 'ERROR: more than one response file for the same station/channel'
                print respfiles
                return 0
            for f in respfiles:
                tempfile = f + '_tmp'
                output = open(tempfile,'w')
                input = open(f,'r')
                outlines = []
                # processing the RESP-file
                alllines = input.readlines()
                if len(alllines) < 20:
                    print "corrupt response file: "+fn
                    output.close()
                    os.remove(tempfile)
                    return 0
                for lines in alllines:
                    if string.find(lines,'Location')!=-1:
                        loc_resp1 = string.split(lines)
                        if len(khole.rstrip()) > 0:
                            newline = loc_resp1[0]+'     '+loc_resp1[1]+\
                                      '    '+khole.rstrip()+'\n'
                        else:
                            newline = loc_resp1[0]+'     '+loc_resp1[1]+\
                                      '    '+'??'+'\n'
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
                        else:
                            yday = yday+2
                            newline = date_resp1[0]+'     '+date_resp1[1]+\
                                      ' '+date_resp1[2]+'    '+`hi[0]`+','\
                                      +yday+','+'23:59:59\n'
                        outlines.append(newline)
                    elif string.find(lines,'Station')!=-1:
                        stat_resp1 = string.split(lines)
                        if len(stat.rstrip()) > 0:
                            newline = stat_resp1[0]+'     '+stat_resp1[1]+\
                                      '     '+stat.rstrip()+'\n'
                        else:
                            newline = lines
                        outlines.append(newline)
                    else:
                        outlines.append(lines)
                # writing new temporary RESP-file and
                # copying it to the original one
                input.close()
                output.writelines(outlines)
                output.close()
                os.rename(tempfile,f)
                        

if __name__ == '__main__':
    test = CheckResp()
    test('/data/hawea/yannik/nord/nord-sac-EN/2003/May/')
