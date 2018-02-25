from Log import *
from Mmail import * 

class EmailQueue():
    def __init__(self, imap, messages, full_when, folder):
        self.imap = imap
        self.full_when = full_when
        self.folder = folder
        self.messages = messages
        self.messagesID = []

    def checkFull(self):
        if self.full_when(self.messages):
            writeLog("info", "Murmur: EmailQueue is full") 
            # self.imap.move(self.messagesID, 'INBOX')

            ##TODO: more flexible search criteria
            incoming_emails = "UID %s:*" % str( self.messagesID[-1] +1 )
            self.messages.setSearch_criteria( incoming_emails )
            self.messagesID = []
            
            # send(destination='soyapark2535@gmail.com', subject='Murmur: Your email queue is full')
            return True

        return False
            
    def getMmail(self):
        return self.messages

    def push(self, emailID):
        self.messagesID.append(emailID)

        return not self.checkFull()
        