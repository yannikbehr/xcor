""" this request function is hard-wired to the request of 24-h
seed-data from the autodrm@geonet.org.nz database"""

import smtplib, string
from ConfigParser import SafeConfigParser


class sendrequest:
    def __init__(self, sender, smtpserver, recipient):
        self.fromaddr = sender
        self.toaddrs  = recipient
        self.smtpsrv = smtpserver

    def request(self, body):
        msg = body

        try:
            server = smtplib.SMTP(self.smtpsrv)
        except Exception, error:
            print "Cannot connect to smpt-server: ", error
        else:
            try:
                server.set_debuglevel(0)
                server.sendmail(self.fromaddr, self.toaddrs, msg)
            except Exception, error:
                print "Cannot send mail: ", error
            server.quit()

class makerequest:
    def __init__(self, confdat):
        self.year = string.atoi(confdat.get('rawdata', 'year'))
        self.month = string.split(confdat.get('rawdata', 'month'))
        self.msgid = confdat.get('rawdata', 'message-id')
        self.email = confdat.get('rawdata', 'return-email')
        self.stat = string.split(confdat.get('rawdata', 'station-list'))
	self.chan = confdat.get('rawdata', 'channel')
        self.smtpserver = confdat.get('rawdata', 'smtpserver')
        self.senderaddress = confdat.get('rawdata', 'senderaddress')
        self.recipient = string.split(confdat.get('rawdata', 'recipient-address'))
        
        self.mday = {}
        self.body = []
        
    def mkrequest(self):
        try:
            self.mday = {'1':31,'3':31,'4':30,'5':31,'6':30,'7':31,'8':31,'9':30,
                         '10':31,'11':30,'12':31}
            for n in self.month:
                if n == '2':
                    if self.year == 4*(self.year/4):
                        self.mday['2'] = 29
                    else:
                        self.mday['2'] = 28
        except Exception:
            print "something 's wrong with date-format!"
            return 1
        else:
            counter = 0
	    for s in self.stat:    
                for j in self.month:
                    for i in range(1,self.mday[j]+1):
                        try:
			    if len(str(i))<2:
			       day="0"+str(i)
			    else:
			       day=str(i)
			    if len(str(j))<2:  
			       mnth="0"+str(j)
			    else:
			       mnth=str(j)
                            self.body = "BEGIN GSE2.0\nMSG_TYPE REQUEST\n"
                            self.body = self.body + "MSG_ID " +s+"-"+day+":"+mnth+":"+str(self.year)+" ANY_NDC\n"
                            self.body = self.body + "EMAIL " +self.email + "\n"
                            self.body = self.body + "FTP " +self.email + "\n"
                            self.body = self.body + "STA_LIST " +s+ "\n"
                            self.body = self.body + "CHAN_LIST " +self.chan + "\n"
                            self.body = self.body + "TIME " +str(self.year)+"/"+mnth+"/"+day\
                                        +" 00:00:01 TO " +str(self.year)+"/"+mnth+"/"+day\
                                        +" 23:59:59\n"
                            self.body = self.body + "WAVEFORM SEED\nSTOP"
                        except Exception:
                            print "Cannot produce message-body!"
                            return 1
                        else:
                            try:
                                # sending the request as email
                                mailsend = sendrequest(self.senderaddress, self.smtpserver, self.recipient)
                                mailsend.request(self.body)
                                counter = counter + 1
                            except Exception, e:
                                print "Cannot send request email"
                                return 1
            print "number of requested files is: ", counter
            return 0

if __name__ == '__main__':
    # reading config-file
    cp = SafeConfigParser()
    cp.read('nord.cfg')

    # building request mail-body and
    # sending it
    timespan = makerequest(cp)
    err = timespan.mkrequest()

