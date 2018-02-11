from imapclient import IMAPClient
from SMTP import * 

import os.path as path
import traceback
# import ConfigParser
import email
from time import sleep
from datetime import datetime, time

from Auth import *
from EmailQueue import * 
from Mmail import * 
from Log import *

# TODO: Support SMTP log handling for CRITICAL errors.

class Monitor(): 
    def __init__(self, USERNAME, PASSWORD, HOST):
        # self.imap = imap
        self.NEWEST_EMAIL_ID = -1
        # self.QUEUE_CNT = 0
        # self.QUEUE_MAX = 2
        self.QUEUE = ''
        # self.ready = ready
        self.emails = [] # list to store old email IDs
        self.login = True

        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.HOST = HOST

        self.authenticate()

    def authenticate(self):
        self.auth = Auth(self.USERNAME, self.PASSWORD, self.HOST)
        self.imap = self.auth.getServer()

    def process_email(self, mail_, download_, log_):
        """Email processing to be done here. mail_ is the Mail object passed to this
        function. download_ is the path where attachments may be downloaded to.
        log_ is the logger object.
        
        """
        log_.info(mail_['subject'])
        return 'return meaningful result here'

    def createFolder(self, inInboxName):
        if not self.imap.folder_exists(inInboxName):
            writeLog('info', '%s Create folder name %s' % (self.imap.create_folder(inInboxName), inInboxName), self.USERNAME)
            #print('%s folder not exist! TERMINATE' % INBOX_NAME)
            #sys.exit()

    def selectFolder(self, inFolder):
        # Select IMAP folder to monitor
        writeLog('info', 'selecting IMAP folder - {0}'.format(inFolder), self.USERNAME)
        try:
            self.createFolder(inFolder)
            self.imap.select_folder(inFolder)
            writeLog('info', 'folder selected', self.USERNAME)
        except Exception:
            # Halt script when folder selection fails
            etype, evalue = sys.exc_info()[:2]
            estr = traceback.format_exception_only(etype, evalue)
            logstr = 'failed to select IMAP folder - '
            for each in estr:
                logstr += '{0}; '.format(each.strip('\n'))
            writeLog('critical', logstr, self.USERNAME)
            return False

        return True        

    def search(self, creteria=None):
        try:
            result = self.imap.search(creteria) if creteria != None else self.imap.search()
        except Exception:
            writeLog('critical', 'Exception at SEARCH: ' + str(creteria), self.USERNAME)
            return
        # log.info('creteria : {0} / search result - {1}({2})'.format(
        #     creteria, len(result), result
        #     ))

        return result

    def fetchLatestEmailID(self):
        # Retrieve and process all unread messages. Should errors occur due
        # to loss of connection, attempt restablishing connection 
        print ("fetch new ", "UID %s:*" % str(max([self.getLatestEmailID(), 0]) + 1))
        result = self.search("UID %s:*" % str(max([self.getLatestEmailID(), 0]) + 1))
        # print ("hello world")
        response = self.imap.fetch(result, ['FLAGS'])
        # print ("welkjfsld" + response)
        return max(msgid for msgid, v in response.items()) if response else self.getLatestEmailID()

    def getLatestEmailID(self):
        return self.NEWEST_EMAIL_ID

    def setLatestEmailID(self, inID):
        print ("Set Last email is " + str(inID))
        self.NEWEST_EMAIL_ID = inID
        
    # Digest and give notifation only for N emails 
    def queue(self, full_when, folder):
        if full_when == None:
            return "Raise error"
        
        incoming_emails = "UID %s:*" % str(max(self.getLatestEmailID() +1, 1))
        print ("queue generate" + incoming_emails)
        m = Mmail(self.imap, incoming_emails)
        self.QUEUE = EmailQueue(self.imap, m, full_when, folder)
        writeLog('info', 'MURMUR: %s the queue has been successfully installed' % (self.USERNAME))
    
    def logout(self):
        self.login = False

    def monitor(self):
        writeLog('info', '... script started', self.USERNAME)
        while True:
            # <--- Start of configuration section

            # # Read config file - halt script on failure
            # try:
            # 	config_file = open('imap_monitor.ini','r+')
            # except IOError:
            # 	log.critical('configuration file is missing')
            # 	break
            # config = ConfigParser.SafeConfigParser()
            # config.readfp(config_file)
            
            # # Retrieve IMAP host - halt script if section 'imap' or value 
            # # missing
            # try:
            # 	host = config.get('imap', 'host')
            # except ConfigParser.NoSectionError:
            # 	log.critical('no "imap" section in configuration file')
            # 	break
            # except ConfigParser.NoOptionError:
            # 	log.critical('no IMAP host specified in configuration file')
            # 	break
            
            # # Retrieve IMAP username - halt script if missing
            # try:
            # 	username = config.get('imap', 'username')
            # except ConfigParser.NoOptionError:
            # 	log.critical('no IMAP username specified in configuration file')
            # 	break
            
            # # Retrieve IMAP password - halt script if missing
            # try:
            # 	password = config.get('imap', 'password')
            # except ConfigParser.NoOptionError:
            # 	log.critical('no IMAP password specified in configuration file')
            # 	break
            
            # # Retrieve IMAP SSL setting - warn if missing, halt if not boolean
            # try:
            # 	ssl = config.getboolean('imap', 'ssl')
            # except ConfigParser.NoOptionError:
            # 	# Default SSL setting to False if missing
            # 	log.warning('no IMAP SSL setting specified in configuration file')
            # 	ssl = False
            # except ValueError:
            # 	log.critical('IMAP SSL setting invalid - not boolean')
            # 	break
            
            # # Retrieve IMAP folder to monitor - warn if missing
            # try:
            # 	folder = config.get('imap', 'folder')
            # except ConfigParser.NoOptionError:
            # 	# Default folder to monitor to 'INBOX' if missing
            # 	log.warning('no IMAP folder specified in configuration file')
            # 	folder = 'INBOX'
                
            # # Retrieve path for downloads - halt if section of value missing
            # try:
            # 	download = config.get('path', 'download')
            # except ConfigParser.NoSectionError:
            # 	log.critical('no "path" section in configuration')
            # 	break
            # except ConfigParser.NoOptionError:
            # 	# If value is None or specified path not existing, warn and default
            # 	# to script path
            # 	log.warn('no download path specified in configuration')
            # 	download = None
            # finally:
            # 	download = download if (
            # 		download and path.exists(download)
            # 		) else path.abspath(__file__)
            # log.info('setting path for email downloads - {0}'.format(download))
            
            folder = "murmur-test-all"

            while True:
                # <--- Start of IMAP server connection loop
                if not self.selectFolder(folder):
                    break

                self.setLatestEmailID(self.fetchLatestEmailID())

                # # then fire the ready event
                print ("ready")
                # self.ready.put('done')
                        
                while True:
                    # <--- Start of mail monitoring loop
                    
                    if not self.login:
                        writeLog('info', 'MURMUR: Logging out', self.USERNAME)
                        self.imap.logout()
                        return 

                    # After all unread emails are cleared on initial login, start
                    # monitoring the folder for new email arrivals and process 
                    # accordingly. Use the IDLE check combined with occassional NOOP
                    # to refresh. Should errors occur in this loop (due to loss of
                    # connection), return control to IMAP server connection loop to
                    # attempt restablishing connection instead of halting script.
                    self.imap.idle()
                    # TODO: Remove hard-coded IDLE timeout; place in config file
                    result = self.imap.idle_check(60) # sec
                    if result:
                        self.imap.idle_done()

                        writeLog('info', "MURMUR: a new email has arrived || a user checks an email")
                        newID = self.fetchLatestEmailID()

                        # new mail
                        if self.getLatestEmailID() != newID: 
                            writeLog('info', 'MURMUR: a new email has arrived', self.USERNAME)

                            # Increment newest email ID
                            self.setLatestEmailID( newID )

                            # print "UID %s:*" % str(self.getLatestEmailID() + 1)
                            result = self.search( "UID %s:*" % str(self.getLatestEmailID() + 1) )
                            # response = self.imap.fetch(result, ['FLAGS', 'BODY[HEADER]'])
                            response = self.imap.fetch(result, ['FLAGS'])

                            # for msgid, data in response.items():
                            #     print('   ID %d: flags=%s' % (msgid,
                            #                                             data[b'FLAGS']))
                            # print ""

                            # Push at queue
                            if self.QUEUE:
                                print ("Queue check")
                                self.QUEUE.push(newID)
                            # self.QUEUE_CNT = self.QUEUE_CNT + 1
                            # self.QUEUE_CNT = self.QUEUE_CNT % self.QUEUE_MAX

                        else:
                            writeLog('info', 'MURMUR: user checks email', self.USERNAME)
                            result = self.search('UNSEEN')

                        # for each in result:
                        #     fetch = self.imap.fetch(each, ['RFC822'])
                        #     mail = email.message_from_string(
                        #         fetch[each]['RFC822']
                        #         )
                        #     try:
                        #         self.process_email(mail, download, log)
                        #         log.info('processing email {0} - {1}'.format(
                        #             each, mail['subject']
                        #             ))
                        #     except Exception:
                        #         log.error(
                        #             'failed to process email {0}'.format(each))
                        #         raise
                        #         continue
                    else:
                        try:
                            self.imap.idle_done()
                            self.imap.noop()
                            writeLog('info', 'no new messages seen', self.USERNAME)
                        except Exception as e:
                            # Halt script when folder selection fails
                            writeLog('critical', "No new message reset connection %s" % (str(e)), self.USERNAME)
                            break
                    # End of mail monitoring loop --->
                    continue
                
                # reauthenticate
                writeLog("info", "imap disconnected. Try reauthenticate")
                self.authenticate() 

                # End of IMAP server connection loop --->
                continue

              

            # End of configuration section --->

            continue
        writeLog('info', 'script stopped ...', self.USERNAME)