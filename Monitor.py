from imapclient import IMAPClient
from SMTP import * 

import os.path as path
import traceback
# import ConfigParser
import email
from time import sleep
from datetime import datetime, time
import random 
import string

from Oauth2 import *
from EmailQueue import * 
from Mmail import * 
from Log import *

# TODO: Support SMTP log handling for CRITICAL errors.

class Monitor(): 
    def __init__(self, USERNAME, PASSWORD, HOST, IS_OAUTH=False):
        # self.imap = imap
        self.NEWEST_EMAIL_ID = -1
        
        self.arrive = '' # {id: ~, action: ~}
        self.custom = '' # {id" ~, action: ~, cond: ~}
        self.time = '' # {id: ~, action: ~, time: ~}
        self.repeat = '' # {id: ~, action: ~, interval: ~}

        # self.ready = ready
        self.emails = [] # list to store old email IDs
        self.login = True

        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.HOST = HOST
        
        if IS_OAUTH: #wait for access code from the user side
            self.OAUTH = Oauth2()
        
        else:  # plain username/password
            self.authenticate_plain()

    def authenticate_oauth_pre(self):
        return self.OAUTH.GeneratePermissionUrl()

    def authenticate_oauth(self, code=None):
        self.imap = IMAPClient(self.HOST, use_uid=True)

        if not hasattr(self, 'REFRESH_TOKEN'):
            response = self.OAUTH.generate_oauth2_token(code)
            self.REFRESH_TOKEN = response['refresh_token']
            self.imap.oauth2_login(self.USERNAME, response['access_token'])
            self.ACCESS_TOKEN = response['access_token']
        else: 
            response = self.OAUTH.refresh_token(self.REFRESH_TOKEN)
            self.imap.oauth2_login(self.USERNAME, response['access_token'])
            self.ACCESS_TOKEN = response['access_token']

        folder = "INBOX"

        self.selectFolder(folder)
        
        self.setLatestEmailID(self.fetchLatestEmailID())

    def authenticate_plain(self):
        ## Connect, login and select the INBOX
        self.imap = IMAPClient(self.HOST, use_uid=True)

        try:
            self.imap.login(self.USERNAME, self.PASSWORD)
        except Exception:
            writeLog("critical", "Auth fail %s" % (self.USERNAME))
            self.imap = False
            return

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
        writeLog ("info", "fetch new ", "UID %s:*" % str(max([self.getLatestEmailID(), 1])))
        result = self.search("UID %s:*" % str(max([self.getLatestEmailID(), 1])))

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
        if hasattr(self, 'REFRESH_TOKEN'):
            send_message(sender=self.USERNAME, access_token=self.ACCESS_TOKEN, destination=to_address, subject=subject, content=content) 
        
        else:
            send_message(sender=self.USERNAME, password=self.PASSWORD, destination=to_address, subject=subject, content=content)

    def setLatestEmailID(self, inID):
        writeLog ("info", "Set Last email is " + str(inID))
        self.NEWEST_EMAIL_ID = inID

    def generate_random_ID(self):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

    def installOnArrive(self, action):
        self.arrive = {"id": self.generate_random_ID(), "action": action}
        
        writeLog('info', 'MURMUR: %s the onArrive has been successfully installed' % (self.USERNAME))
        
    def installOnCustom(self, action, full_when):
        incoming_emails = "UID %s:*" % str(max(self.getLatestEmailID() +1, 1))
        m = Mmail(self.imap, incoming_emails)

        self.custom = {"id": self.generate_random_ID(), "action": action, "cond": full_when, "queue": EmailQueue(self.imap, m, full_when)}
        writeLog('info', 'MURMUR: %s the onCustom has been successfully installed' % (self.USERNAME))

    def installOnTime(self, action, target_time, interval):
        self.time = {"id": self.generate_random_ID(), "action": action, "target_time": target_time, "interval": interval}
        writeLog('info', 'MURMUR: %s the onTime has been successfully installed' % (self.USERNAME))

    def installRepeat(self, action, target_time, interval):
        self.repeat = {"id": self.generate_random_ID(), "action": action, "target_time": target_time, "interval": interval}
        writeLog('info', 'MURMUR: %s the repeat has been successfully installed' % (self.USERNAME))