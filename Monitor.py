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
from Utils import *

# TODO: Support SMTP log handling for CRITICAL errors.

class Monitor(): 
    def __init__(self, USERNAME, PASSWORD, HOST):
        # self.imap = imap
        self.NEWEST_EMAIL_ID = -1

        self.QUEUE = []
        self.onArrive = ''
        self.onCustom = ''
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

        if not self.imap:
            return False

        folder = "INBOX"

        self.selectFolder(folder)
        
        self.setLatestEmailID(self.fetchLatestEmailID())

    def createFolder(self, inInboxName):
        if not self.imap.folder_exists(inInboxName):
            writeLog('info', '%s Create folder name %s' % (self.imap.create_folder(inInboxName), inInboxName), self.USERNAME)
            #print('%s folder not exist! TERMINATE' % INBOX_NAME)
            #sys.exit()

    def fetchLatestEmailID(self):
        # Retrieve and process all unread messages. Should errors occur due
        # to loss of connection, attempt restablishing connection 
        writeLog ("info", "fetch new ", "UID %s:*" % str(max([self.getLatestEmailID(), 0]) + 1))
        result = self.search("UID %s:*" % str(max([self.getLatestEmailID(), 0]) + 1))
        # print ("hello world")
        response = self.imap.fetch(result, ['FLAGS'])
        # print ("welkjfsld" + response)
        return max(msgid for msgid, v in response.items()) if response else self.getLatestEmailID()

    def getLatestEmailID(self):
        return self.NEWEST_EMAIL_ID

    def process_email(self, mail_, download_, log_):
        """Email processing to be done here. mail_ is the Mail object passed to this
        function. download_ is the path where attachments may be downloaded to.
        log_ is the logger object.
        
        """
        log_.info(mail_['subject'])
        return 'return meaningful result here'

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

    def send(self, to_address, subject, content):
        send_message(self.USERNAME, to_address, subject, content)

    def setLatestEmailID(self, inID):
        writeLog ("info", "Set Last email is " + str(inID))
        self.NEWEST_EMAIL_ID = inID

    def installOnArrive(self, action, folder):
        incoming_emails = "UID %s:*" % str(max(self.getLatestEmailID() +1, 1))
        # print ("onCustom generate" + incoming_emails)
        m = Mmail(self.imap, incoming_emails)

        def full_when(x):
            return True
        self.QUEUE = EmailQueue(self.imap, m, full_when, folder)
        self.onArrive = action
        writeLog('info', 'MURMUR: %s the onArrive has been successfully installed' % (self.USERNAME))
        
    # Digest and give notifation only for N emails 
    def installOnCustom(self, action, full_when, folder):
        if full_when == None:
            return "Raise error"
        
        incoming_emails = "UID %s:*" % str(max(self.getLatestEmailID() +1, 1))
        # print ("onCustom generate" + incoming_emails)
        m = Mmail(self.imap, incoming_emails)
        self.QUEUE = EmailQueue(self.imap, m, full_when, folder)
        self.onCustom = action
        writeLog('info', 'MURMUR: %s the onCustom has been successfully installed' % (self.USERNAME))

