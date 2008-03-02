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
import getpass, imaplib, string, ftplib, os, uu, glob, re, os.path, sys
from ConfigParser import SafeConfigParser

class ftpdownload:
    """class to download data from autodrm-request"""
    def __init__(self,ftpmatrix, downloaddir):
        self.ftpinfo = ftpmatrix
        self.ftpusr = 'ftp'
        self.ftppwd = 'ftp'
        self.dwnld = downloaddir

    def getftp(self):
        try:
            # extracting server sub-string and directory
            pattern = r'ftp://(.*)\/(.*)\/.*'
            match = re.search(pattern, self.ftpinfo[0])
            ftpserver = match.group(1)
            ftpdir = match.group(2)
        except Exception,e:
            print "ERROR: cannot extract ftp server name "
        else:
            try: con = ftplib.FTP(ftpserver)
            except Exception, error:
                print "Cannot connect to ",ftpserver, error
            else:
                try: con.login(self.ftpusr, self.ftppwd)
                except Exception, error:
                    print "Cannot login: ", error
                else:
                    print "ftp-login successful"
                    try: con.cwd(ftpdir)
                    except Exception, error:
                        print "Cannot change directory: ", error
                    else:
                        print "change to directory ", ftpdir, " successful"
                        try:
                            dirlist = os.listdir(self.dwnld)
                            con.set_pasv(1)
                            counter = 0
                            for i in self.ftpinfo:
                                pattern = r'ftp://.*\/.*\/(.*)'
                                match = re.search(pattern, i)
                                file = match.group(1)
                                if file not in dirlist:
                                    print "Starting download of file: ", file
                                    con.retrbinary('RETR '+file, open(self.dwnld +file,'wb').write)
                                    counter = counter+1
                                else:
                                    print file, "already exists in: ", self.dwnld
                        except Exception, error:
                            print "Cannot retrieve file: ", error
                        else:
                            print "number of downloaded files is: ", counter

    def py_uudecode(self, seeddir):
        try:
            dirlist = os.listdir(self.dwnld)
        except OSError, err:
            print "Cannot get dirlist or make new dir: ",err
        else:
            try:
                for i in dirlist:
                    infile = open(self.dwnld+i,'r')
                    outfile = seeddir
                    uu.decode(infile, outfile)
            except Exception, e:
                print "Cannot decode data-file. ",e

class msg:
    """extract ftp-server-string from email body"""
    def __init__(self,text):
        self.lines = string.split(text, '\015\012')

    def readline(self):
        try:
            if string.find(self.lines[4], 'error_log') != -1:
                print "WARNING: found error code in autodrm message!"
                return 1
            elif string.find(self.lines[4], 'ftp_log') != 0:
                pattern = r'\s+\[\s{1}(ftp.*)\s{1}\]'
                for line in self.lines:
                    match = re.search(pattern, line)
                    if match:
                        return match.group(1)
        except Exception,e:
            print "ERROR: cannot process email contents"
            return 1


class mailwatcher:
    """class to check mailbox for autodrm-mails; gets a pointer to
    a config-file"""
    def __init__(self,confdat):
        self.ims = confdat.get('rawdata','imapserver')
        self.usr = confdat.get('rawdata','imapusername')
        self.pwd = getpass.getpass()
        self.dwnld = confdat.get('rawdata', 'download-dir')
        self.seeddir = confdat.get('rawdata', 'seed-dir')
        self.ftpmat = []

    def getmail(self):
        """function to check imap-mailbox for autodrm-mails and
        calls ftpdownload class """
        try:
            M = imaplib.IMAP4(self.ims)
            M.login(self.usr, self.pwd)
        except Exception, e:
            print "ERROR: IMAP login not successful: ",e
            return 1
        try:
            result, message = M.select(readonly=1)
            if result != 'OK':
                raise Exception, message
            typ, data = M.search(None, '(UNSEEN FROM "autodrm@geonet.org.nz" SUBJECT "GeoNet AutoDRM Response")')
            if len(data[0]) > 0:
                for num in string.split(data[0]):
                    try:
                        f = M.fetch(num, '(BODY[TEXT])')
                        # now comes the ftp-site extraction part
                        # if autodrm-format changes this part has
                        # to be changed as well
                        aaa = msg(f[1][0][1])
                        if aaa.readline() != 1:
                            self.ftpmat.append(aaa.readline())
                    except Exception,e:
                        print "ERROR: cannot process email"
                        return 1
                if not len(self.ftpmat):
                    print "WARNING: no ftp-address extracted"
                    return 1
            else:
                print "-->No unseen autodrm emails on server"
                print "-->if there should be any, check if"
                print "-->they are marked as seen in your inbox"
                return 1
                
        except Exception, e:
            print "ERROR: Cannot get message!", e
            return 1
        else:
            try:
                #ftpfile=ftpdownload(self.ftpmat, self.dwnld)
                #ftpfile.getftp()
                ftpfile.py_uudecode(self.seeddir)
            except Exception, e:
                print "Call of ftpdownload-class not successful!", e
                return 1
            else:
                return 0
        M.logout()


            
    


if __name__ == '__main__':
    # reading config-file
    cp = SafeConfigParser()
    cp.read('/Users/home/rawlinza/Zara/sac_from_seed/modules/nord.cfg')

    # checking imap-server for autodrm-mail
    mail = mailwatcher(cp)
    err  = mail.getmail()






