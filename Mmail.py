from email.parser import HeaderParser
from Log import *

def get_text(msg):
    if msg.is_multipart():
        return get_text(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)

class Mmail():
    def __init__(self, imap, search_criteria):
        self.imap = imap
        self.search_criteria = search_criteria
        writeLog ("info", self.search_criteria)

    def setSearch_criteria(self, search_criteria):
        self.search_criteria = search_criteria

    def getCount(self):
        writeLog ("info", "Mmail getCount(): " + self.search_criteria)
        messages = self.imap.search( self.search_criteria )
        # print (messages)
        return len(messages)

    def getFlags(self):
        messages = self.imap.search( self.search_criteria )

        flags = self.imap.fetch(messages, ['FLAGS'])
        results = []

        for msgid, data in flags.items():
            results.append(data[b'FLAGS'])

        return results

    def getSubject(self):
        return self.getEmail('Subject')

    def getSender(self):
        return self.getEmail('From')

    def getRecipient(self):
        return self.getEmail('To')

    def getContent(self):
        return self.getEmail('To')

    def getEmail(self, header):
        unreads = self.getUnreadEmails()

        results = []
        messages = self.imap.search( self.search_criteria )
        # raw=email.message_from_bytes(data[0][1])
        response = self.imap.fetch(messages, ['BODY[HEADER]'])
        parser = HeaderParser()

        if response is None:
            return []
            
        for msgid, data in response.items():
            # print (data[b'BODY[HEADER]'])
            msg = parser.parsestr(data[b'BODY[HEADER]'].decode("utf-8"))
            results.append( msg[header] )

        self.setSeen(False, unreads)

        return results

    def getUnreadEmails(self):
        messages = self.imap.search( self.search_criteria )

        flags = self.imap.fetch(messages, ['FLAGS'])
        read_emails = []

        for msgid, data in flags.items():
            print('   ID %d: flags=%s ' % (msgid,
                                            data[b'FLAGS']))

            if '\\Seen' not in data[b'FLAGS']:
                read_emails.append(msgid)

        return read_emails


    
    def setSeen(self, inIsSeen, inMsgs):
        # if true, add SEEN flags
        if inIsSeen: 
            self.imap.set_flags(inMsgs, '\\Seen')            
        else: 
            self.imap.remove_flags(inMsgs, '\\Seen')     
    

    