from Log import *
from Mmail import * 

class EmailQueue():
    def __init__(self, imap, messages, full_when):
        self.imap = imap
        self.full_when = full_when
        self.messages = messages
        self.old_messages = messages
        self.messagesID = []

    def checkFull(self):
        if self.full_when(self.messages):
            writeLog("info", "Murmur: EmailQueue is full") 
            # self.imap.move(self.messagesID, 'INBOX')

            ##TODO: more flexible search criteria
            incoming_emails = "UID %s:*" % str( self.messagesID[-1] +1 )

            self.old_messages = Mmail( self.imap, self.messages.search_criteria)

            self.messages.setSearch_criteria( incoming_emails )
            self.messagesID = []
            
            # send(destination='soyapark2535@gmail.com', subject='Murmur: Your email queue is full')
            return True

        return False
            
    def getMmail(self):
        return self.old_messages

    def push(self, emailID):
        self.messagesID.append(emailID)
        first_email = self.messages.search_criteria.split("UID ")[1].split(":")[0]
        self.messages.search_criteria = "UID %s:%s" % (first_email, str(emailID))
        
        return not self.checkFull()
        