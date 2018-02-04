# Copyright (c) 2014, Menno Smits
# Released subject to the New BSD License
# Please see http://en.wikipedia.org/wiki/BSD_licenses

from imapclient import IMAPClient
# from backports import ssl
from Oauth2 import Oauth2
import sys
import email
from email import message
import sys 
from threading import Event, Thread

class Auth(): 
    #context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

    def __init__(self, USERNAME, PASSWORD, HOST):
        self.USERNAME = USERNAME
        self.PASSWORD = PASSWORD
        self.HOST = HOST

        ## Connect, login and select the INBOX
        self.server = IMAPClient(self.HOST)

        options = {}
        options['generate_oauth2_token'] = True
        options['client_id'] = self.client_id
        options['client_secret'] = self.client_secret

        oauth = Oauth2()

        response = {}
        OAUTH = False
        DEBUG_AUTH = True

        if OAUTH:
            if DEBUG_AUTH:
                response = oauth.generate_oauth2_token(options)
                options['refresh_token'] = response['refresh_token']

            else:
                options['refresh_token'] = "1/IOkqlvDe9M0BMTTSkn1VFFIseSR-1TVAKiDRCtowkx8u9fpKrsKkQluBLMLO-vPB"
                response = oauth.refresh_token(options)

            self.server.oauth2_login(self.USERNAME, response['access_token'])

        else:
            try:
                self.server.login(self.USERNAME, self.PASSWORD)
            except Exception:
                print "Auth fail", self.USERNAME, self.HOST
                self.server = False

    def getServer(self):
        return self.server