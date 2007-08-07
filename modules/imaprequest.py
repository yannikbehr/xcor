""" module to extract ftp-download site from a autodrm-request;
configuration is read in from 'config.txt'; the name of the config file
can be changed easily without understanding the code;
the structure of the config-file is:\n
[rawdata]\n
download-dir=./local/download/dir/\n
imapserver=yourimapserver\n
imapusername=youraccountname\n
just copy this into a file called 'config.txt' located in the same
directory as 'imaprequest.py', adapt the settings and then run 'python imaprequest.py';
it only works with imap-email-accounts and only if the autodrm-mails are
still marked as 'unseen' or 'unread'
"""
import getpass, imaplib, string, ftplib
from ConfigParser import SafeConfigParser

class ftpdownload:
    """class to download data from autodrm-request"""
    def __init__(self,ftpmatrix, downloaddir):
        self.ftpinfo = ftpmatrix
        self.ftpusr = 'ftp'
        self.ftppwd = 'ftp'
        self.dwnld = downloaddir

    def getftp(self):
        try: con = ftplib.FTP(self.ftpinfo[0][0])
        except Exception, error:
            print "Cannot connect: ", error
        else:
            try: con.login(self.ftpusr, self.ftppwd)
            except Exception, error:
                print "Cannot login: ", error
            else:
                print "ftp-login successful"
                try: con.cwd(self.ftpinfo[0][1])
                except Exception, error:
                    print "Cannot change directory: ", error
                else:
                    print "change to directory ", self.ftpinfo[0][1], " successful"
                    try:
                        con.set_pasv(0)
                        counter = 0
                        for i in self.ftpinfo:
                            print "Starting download of file: ", i[2]
                            con.retrbinary('RETR '+i[2], open(self.dwnld +i[2],'wb').write)
                            counter = counter+1
                    except Exception, error:
                        print "Cannot retrieve file: ", error
                    else:
                        print "number of downloaded files is: ", counter

class msg:
    def __init__(self,text):
        self.lines = string.split(text, '\015\012')
    def readline(self):
        try: return self.lines[12] + '\n'
        except: return ''


class mailwatcher:
    """class to check mailbox for autodrm-mails; gets a pointer to
    a config-file"""
    def __init__(self,confdat):
        self.ims = confdat.get('rawdata','imapserver')
        self.usr = confdat.get('rawdata','imapusername')
        self.pwd = getpass.getpass()
        self.dwnld = confdat.get('rawdata', 'download-dir')
        self.list = []
        self.ftpmat = []

    def getmail(self):
        """function to check imap-mailbox for autodrm-mails and
        calls ftpdownload class """
        try:
            M = imaplib.IMAP4(self.ims)
            M.login(self.usr, self.pwd)
        except Exception, e:
            self.list.insert(-1, ('IMAP login error: ',e))
            return self.list

        try:
            result, message = M.select(readonly=1)
            if result != 'OK':
                raise Exception, message
            typ, data = M.search(None, '(UNSEEN FROM "autodrm@geonet.org.nz")')
            for num in string.split(data[0]):
                try:
                    f = M.fetch(num, '(BODY[TEXT])')
                    # now comes the ftp-site extraction part
                    # if autodrm-format changes this part has
                    # to be changed as well
                    aaa = msg(f[1][0][1])
                    tmpstr = aaa.readline()
                    ftpbeg = string.find(tmpstr,'ftp')
                    ftpend = string.find(tmpstr, ']', ftpbeg)
                    serverst = string.find(tmpstr,'ftp', ftpbeg+1)
                    serverend = string.find(tmpstr, '/', serverst)
                    serverstr = tmpstr[serverst:serverend]
                    dirend = string.find(tmpstr, '/', serverend+1)
                    dirstr = tmpstr[serverend+1:dirend]
                    filestr = tmpstr[dirend+1:ftpend-1]
                    tmpmat = [serverstr, dirstr, filestr]
                    self.ftpmat.append(tmpmat)
                except KeyError:
                    self.list.insert(-1, 'KeyError')
                    return self.list
        except Exception, e:
            print "Cannot get message!"
            self.list.insert(-1, ('IMAP read error ', e))
            return self.list
        else:
            try:
                ftpfile=ftpdownload(self.ftpmat, self.dwnld)
                ftpfile.getftp()
            except Exception, e:
                print "Call of ftpdownload-class not successful!", e
        M.logout()





if __name__ == '__main__':
    # reading config-file
    cp = SafeConfigParser()
    cp.read('config.txt')

    # checking imap-server for autodrm-mail
    mail=mailwatcher(cp)
    list=mail.getmail()






