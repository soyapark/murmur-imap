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

    def add_flags(self, flags):
        if type(flags) is not list:
            raise Exception('add_flags(): args flags must be a list of strings')

        for f in flags:
            if not isinstance(f, str):
                raise Exception('add_flags(): args flags must be a list of strings')

        self.imap.add_flags(self.get_IDs(), flags) 
        print ("Successfuly add flags: " + str(flags))

    def setSearch_criteria(self, search_criteria):
        self.search_criteria = search_criteria

    def get_IDs(self):
        return self.imap.search( self.search_criteria )

    def get_count(self):
        writeLog ("info", "Mmail getCount(): " + self.search_criteria)
        messages = self.imap.search( self.search_criteria )
        # print (messages)
        return len(messages)

    def get_date(self):
        return self.get_email('Date', True)

    def get_flags(self):
        messages = self.imap.search( self.search_criteria )

        flags = {}
        for msgid, data in self.imap.get_flags(messages).items():
            print('   ID %d: flags=%s ' % (msgid,
                                            data))
            # print (int.from_bytes(msgid, byteorder='little'))                              
            flags[msgid] = data

        return flags

    def get_subjects(self):
        return self.get_email('Subject')

    def get_senders(self):
        return self.get_email('From')

    def get_recipients(self):
        return self.get_email('To')

    def get_contents(self):
        return self.get_email('To')

    def get_email(self, header, inCludeID=False):
        unreads = self.get_unread_emails()

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

        self.mark_read(False, unreads)
        if not inCludeID:
            return results

        return id_results

    def get_unread_emails(self):
        messages = self.imap.search( self.search_criteria )

        flags = self.get_flags()

        if flags is None:
            return []

        read_emails = []

        for msgid, data in flags.items(): 
            if b'\\Seen' not in data:
                read_emails.append(msgid)

        return read_emails

    def mark_read(self, inIsSeen, inMsgs):
        # if true, add SEEN flags
        if inIsSeen: 
            self.imap.set_flags(inMsgs, '\\Seen')            
        else: 
            self.imap.remove_flags(inMsgs, '\\Seen')     
    

    