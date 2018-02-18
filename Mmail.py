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

    def getIDs(self):
        return self.imap.search( self.search_criteria )

    def getCount(self):
        writeLog ("info", "Mmail getCount(): " + self.search_criteria)
        messages = self.imap.search( self.search_criteria )
        # print (messages)
        return len(messages)

    def getDate(self):
        return self.getEmail('Date', True)

    def getFlags(self):
        messages = self.imap.search( self.search_criteria )

        flags = {}
        for msgid, data in self.imap.get_flags(messages).items():
            print('   ID %d: flags=%s ' % (msgid,
                                            data))
            # print (int.from_bytes(msgid, byteorder='little'))                              
            flags[msgid] = data

        return flags

    def getSubject(self):
        return self.getEmail('Subject')

    def getSender(self):
        return self.getEmail('From')

    def getRecipient(self):
        return self.getEmail('To')

    def getContent(self):
        return self.getEmail('To')

    def getEmail(self, header, inCludeID=False):
        unreads = self.getUnreadEmails()

        results = []
        id_results = []
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
            id_results.append( (msgid, msg[header]) )

        self.markRead(False, unreads)
        if not inCludeID:
            return results

        return id_results

    def getUnreadEmails(self):
        messages = self.imap.search( self.search_criteria )

        flags = self.getFlags()

        if flags is None:
            return []

        read_emails = []

        for msgid, data in flags.items(): 
            if b'\\Seen' not in data:
                read_emails.append(msgid)

        return read_emails

    def markRead(self, inIsSeen, inMsgs):
        # if true, add SEEN flags
        if inIsSeen: 
            self.imap.set_flags(inMsgs, '\\Seen')            
        else: 
            self.imap.remove_flags(inMsgs, '\\Seen')     
    

    