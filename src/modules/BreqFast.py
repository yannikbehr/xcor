#! /usr/bin/env python
'''
Created on Dec 8, 2010

@author: Adam Carrizales

Python script for creating and sending an IRIS BREQ_FAST request
from given input specifications

Works for multiple-stations, searching for the same channels in same network

A request may be called using...

					  
python BreqFast.py -s SNZO -n IU -c HHZ -b 2009/12/31-00:00:00 -e 2009/12/31-23:59:59 -l Testjob

'''

import os, os.path, sys, string
import argparse
import smtplib
from email.mime.text import MIMEText

DEBUG = False

class breqFast:
    '''
    This class represents a standard BREQFAST request to iris
    '''


    def __init__(self, label):
        '''
        Init the standard BREQ FAST format
        host = 'smtp.staff.vuw.ac.nz:25'        
        '''
        self.name = 'your name here'
        self.inst = 'SGEES VUW New Zealand'
        self.addr = 'PO Box 600, Wellington, New Zealand'
        self.email = 'your.name@vuw.ac.nz'
        self.phone = '+64-4463-5233'
        self.fax = '+64-4463-5233'
        self.media = 'Electronic'
        self.altMedia1 = 'DLT'
        self.altMedia2 = 'DVD'
        self.host = 'smtp.staff.vuw.ac.nz:25'
        self.iris = 'breq_fast@iris.washington.edu'
        
        self.header = '.NAME '+self.name+'\n'+\
                        '.INST '+self.inst+'\n'+\
                        '.MAIL '+self.addr+'\n'+\
                        '.EMAIL '+self.email+'\n'+\
                        '.PHONE '+self.phone+'\n'+\
                        '.FAX '+self.fax+'\n'+\
                        '.MEDIA: '+self.media+'\n'+\
                        '.ALTERNATE MEDIA: '+self.altMedia1+'\n'+\
                        '.ALTERNATE MEDIA: '+self.altMedia2+'\n'+\
                        '.LABEL '+label+'\n'+\
                        '.END\n'
        
    def __call__(self, args):
        '''
        Call the main processing function with 'args' from command-line.
        '''
        
        self.procRequest(args)
        
        
    def procRequest(self, args, verbose=True):
        '''
        Parse command-line arguments into a proper BREQ_FAST request
        Can specify multiple stations with the same channels, 
	but they must be from the same network
        '''
        
        #Intialize a request string
        request = ''
        
        # Split up the args.starttime and args.endtime into date/time BREQ_FAST format
	# YYYY MM DD HH MM SS.MS --> 2010 12 31 00 00 00.0
        startdate = args.starttime
        enddate = args.endtime
        startdate = args.starttime.split('-')
        starttime = startdate[1].split(':')
        startdate = startdate[0].split('/')
        enddate = args.endtime.split('-')
        endtime = enddate[1].split(':')
        enddate = enddate[0].split('/')
        # For each station in args.station, produce a BREQ_FAST string
        for station in args.stations:
            
            a = station+' '+args.network+' '+startdate[0]+' '+startdate[1]+\
            ' '+startdate[2]+' '+starttime[0]+' '+starttime[1]+' '+starttime[2]+'.0 '+\
            enddate[0]+' '+enddate[1]+\
            ' '+enddate[2]+' '+endtime[0]+' '+endtime[1]+' '+endtime[2]+'.0 '+str(len(args.chans))+\
            ' '+string.join(["%s" % i for i in args.chans])+'\n'
            
            request = request + a
        
        msg = MIMEText(self.header+request)
        msg['Subject'] = 'BREQ_FAST'
        msg['From'] = self.email
        msg['To'] = self.iris
 	
	if args.write:
	    file = open(args.label+'.request','w')
	    file.writelines(self.header+request)
	    file.close()
	
	if args.debug:
	    print "Request message will be:\n", msg.as_string()
	    return
	
        if verbose:
            print "Connecting to: ", self.host
        try:
            conn = smtplib.SMTP(self.host)
            
        except Exception:
            print "ERROR: cannot connect to: ", self.host 
        else:
            conn.sendmail(self.email, self.iris, msg.as_string())
            if verbose:
                print "Request sent successfully: ", args.label
            conn.quit()
	    
	return

def argParser():
    '''
    Holds argument paser functions for cleanliness
    '''
    parser = argparse.ArgumentParser(description='Create and submit BREQ_FAST requests\
                                     from input specs.')
    parser.add_argument('-s', action="store", dest='stations',
                         required=True, nargs='+', help='Specify a station code(s): SNZO WEL WAIK LE4\n\
                          --> All stations must be in the same network')
    parser.add_argument('-n', action="store", dest='network',
                         required=True, help='Specify a network code (2 letters)')
    parser.add_argument('-c', action="store", dest='chans', 
                        nargs='+', required=True, help='Specify any number of channels.\
                         -c HHE HHZ LE*')
    parser.add_argument('-b', action="store", dest='starttime',
                         required=True, help='Specify the starttime as YYYY/MM/DD-HH:MM:SS')
    parser.add_argument('-e', action="store", dest='endtime',
                         required=True, help='Specify the endtime as YYYY/MM/DD-HH:MM:SS')
    parser.add_argument('-l', action="store", dest='label', type=str, required=True,help='Specify a job label to avoid confusion.')
    parser.add_argument('-D', action="store_const", const=True, dest='debug', default=False,help='Prevent sending of request and print to screen instead (Debug).')
    parser.add_argument('-W', action="store_const", const=True, dest='write', default=False,help='Write BREQ_FAST request to  label.request in working directory.')
    
    args = parser.parse_args()
    
    return args
    
if __name__ == '__main__':
    
    args = argParser()
    breq = breqFast(args.label)
    breq(args)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
        