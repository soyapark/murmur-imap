# Copyright (c) 2014, Menno Smits
# Released subject to the New BSD License
# Please see http://en.wikipedia.org/wiki/BSD_licenses

from imapclient import IMAPClient
# from backports import ssl
from Oauth2 import *
import sys
import email
from email import message
import sys 
from threading import Event, Thread
from Log import * 
from Conf import * 

class Auth(): 
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

    def __init__(self, USERNAME, PASSWORD, HOST, OAUTH, REFRESH_TOKEN=None):
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.HOST = HOST

        ## Connect, login and select the INBOX
        self.server = IMAPClient(self.HOST, use_uid=True)

        response = {}
        DEBUG_AUTH = True

        if OAUTH:
            options = {}
            options['generate_oauth2_token'] = True
            options['client_id'] = CLIENT_ID
            options['client_secret'] = CLIENT_SECRET

            oauth = Oauth2(options)

            if REFRESH_TOKEN is None:
                self.token_url = oauth.GeneratePermissionUrl()

            else:
                options['refresh_token'] = "1/IOkqlvDe9M0BMTTSkn1VFFIseSR-1TVAKiDRCtowkx8u9fpKrsKkQluBLMLO-vPB"
                response = oauth.refresh_token(options)

            self.server.oauth2_login(self.USERNAME, response['access_token'])

        else:
            try:
                self.server.login(self.USERNAME, self.PASSWORD)
            except Exception:
                writeLog("critical", "Auth fail %s" % (self.USERNAME))
                self.server = False

    def getServer(self):
        return self.server