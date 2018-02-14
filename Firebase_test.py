import pyrebase
from Auth import Auth
from threading import Event, Thread
from Monitor import *
import sys
import traceback
try:
    from StringIO import StringIO
except ImportError:
    import io
import contextlib
from Log import *


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
from Cleanup import *
          

config = {
  "apiKey": "###",
  "authDomain": "murmur-183618.firebaseapp.com",
  "databaseURL": "https://murmur-183618.firebaseio.com",
  "storageBucket": "murmur-183618.appspot.com",
  "serviceAccount": "cert/murmur-firebase.json"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

@register_exit_fun
def cleanup():
    print("cleanup START")
    db.child("running").remove()
    print("cleanup")

# register_exit_fun(cleanup)

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

monitors = {} # uid: monitor_instance

class User():
    def __init__(self, monitor):
        self.monitor = monitor

    def __str__(self):
        return "????"

    def __enter__(self):
        return self

    def __exit__(self,  tp, value, traceback):
        pass

def pushMessage(path, message):
    writeLog("info","Send a message to a server %s %s" % (path, message))

    db.child("/".join([p for p in path])).push(message)

global execution_result
execution_result = ""

def interpret(uid, cmd, isMonitor):
    
    try:
        with User(monitors[uid]) as u, stdoutIO() as s:
            
            global queue_action 
            queue_action = {}
            def send(to_address, subject, content):
                writeLog("info","Request for sending email")
                u.monitor.send(to_address, subject, content)

                global execution_result
                execution_result += "\nRequested email sent\n"

            def queue(func, action, folders):
                writeLog("info", "Request for queue")
                global queue_action 
                queue_action = action
                u.monitor.queue(func, action, folders)

                global execution_result
                execution_result += "\nYour queue is successfully launched\n"

            def logout():
                #kill thread
                writeLog("info","Request for logout")
                u.monitor.logout()

                global execution_result
                execution_result += "\nYou're logged out shortly. Bye!\n"

            if isMonitor:
                # writeLog("info",queue_action)
                # senddd("as","wew","sdf")
                writeLog('info', '... script started', u.monitor.USERNAME)
                while True:
                    while True:
                        # <--- Start of IMAP server connection loop

                        # # then fire the ready event
                        writeLog('info', 'MURMUR: ready to execute commands', u.monitor.USERNAME)

                        loop_cnt = 1

                        while True:
                            loop_cnt = loop_cnt + 1
                            # <--- Start of mail monitoring loop
                            
                            writeLog('info', 'MURMUR: Start of mail monitoring loop', u.monitor.USERNAME)

                            if not u.monitor.login:
                                writeLog('info', 'MURMUR: Logging out', u.monitor.USERNAME)
                                u.monitor.imap.logout()
                                return 
                            
                            # After all unread emails are cleared on initial login, start
                            # monitoring the folder for new email arrivals and process 
                            # accordingly. Use the IDLE check combined with occassional NOOP
                            # to refresh. Should errors occur in this loop (due to loss of
                            # connection), return control to IMAP server connection loop to
                            # attempt restablishing connection instead of halting script.
                            u.monitor.imap.idle()
                            # TODO: Remove hard-coded IDLE timeout; place in config file
                            result = u.monitor.imap.idle_check() # sec
                            if result:
                                u.monitor.imap.idle_done()

                                # writeLog('info', "MURMUR: a new email has arrived || a user checks an email")
                                newID = u.monitor.fetchLatestEmailID()

                                # new mail
                                if u.monitor.getLatestEmailID() != newID: 
                                    writeLog('info', 'MURMUR: a new email has arrived', u.monitor.USERNAME)

                                    # Increment newest email ID
                                    u.monitor.setLatestEmailID( newID )

                                    # print "UID %s:*" % str(self.getLatestEmailID() + 1)
                                    result = u.monitor.search( "UID %s:*" % str(u.monitor.getLatestEmailID() + 1) )
                                    # response = self.imap.fetch(result, ['FLAGS', 'BODY[HEADER]'])
                                    response = u.monitor.imap.fetch(result, ['FLAGS'])

                                    # for msgid, data in response.items():
                                    #     print('   ID %d: flags=%s' % (msgid,
                                    #                                             data[b'FLAGS']))
                                    # print ""

                                    # Push at queue
                                    if u.monitor.QUEUE:
                                        print ("Queue check")
                                        if not u.monitor.QUEUE.push(newID): # if queue is full
                                            queue_action() # do defined action

                                    # self.QUEUE_CNT = self.QUEUE_CNT + 1
                                    # self.QUEUE_CNT = self.QUEUE_CNT % self.QUEUE_MAX

                                else:
                                    writeLog('info', 'MURMUR: user checks email', u.monitor.USERNAME)
                                    result = u.monitor.search('UNSEEN')

                            else:
                                u.monitor.imap.idle_done()
                                u.monitor.imap.noop()
                                writeLog('info', 'no new messages seen', u.monitor.USERNAME)
                            # End of mail monitoring loop --->
                            continue
                        
                        logout()

                        # reauthenticate
                        writeLog("info", "imap disconnected. Try reauthenticate")
                        u.monitor.authenticate() 

                        # End of IMAP server connection loop --->
                        continue

                    # End of configuration section --->

                    continue
                writeLog('info', 'script stopped ...', u.monitor.USERNAME)
              
            else:
                d = dict(locals(), **globals())
                exec( cmd, d, d)

                global execution_result
                data = {"type": "info", "content": execution_result + s.getvalue()}
                pushMessage(["messages", uid], data)
                # db.child().child(uid).push(data)

                db.child("running").child(uid).set(cmd)

    except Exception as e:
        etype, evalue = sys.exc_info()[:2]
        estr = traceback.format_exception_only(etype, evalue)
        logstr = 'Error during executing your code'
        for each in estr:
            logstr += '{0}; '.format(each.strip('\n'))

        logstr = "Execution error %s \n %s" % (str(e), logstr)
        writeLog( "critical", logstr )

        # Send this error msg to the user
        data = {"type": "error", "content": logstr}
        pushMessage(["messages", uid], data)
        # db.child("messages").child(uid).push(data)

        # Tell the client execution has been stopped
        db.child("running").child(uid).remove()

def stream_handler(message):
    # print(message["event"]) # put
    print(message["path"]) # /-K7yGTTEp7O549EzTYtI
    print ("new Message")
    print (message)

    if message["data"] == None or "data" not in message:
        return
    # print message["data"].keys()[0]

    if "type" in message["data"]:
        # print ("hello")

        if message["data"]["type"] == "auth":
            writeLog("info", "auth request", message["data"]["username"])
            monitor = Monitor(message["data"]["username"], message["data"]["password"], 'imap.gmail.com')
            server = monitor.imap
            
            uid = message["path"][1:] # uid

            db.child("users").child(message["path"][1:]).remove()

            if server == False:
                # send message to user auth fail
                data = {"code": 403, "auth": "Authentication Fail. Is it correct username/password?"}
                pushMessage(["messages", uid], data)
                # db.child("messages").child(uid).push(data)
                return

            else:
                # send message to user auth success
                data = {"code": 200, "auth": "Authentication Success."}
                pushMessage(["messages", uid], data)
                # db.child("messages").child(uid).push(data)

            monitors[uid] = monitor

            # ready.wait()
            # send message to user it's ready to play with

        elif message["data"]["type"] == "cmd":
            print ("New command", message["data"]["content"])
            
            interpret(message["data"]["uid"], message["data"]["content"], False)

            # start monitoring when executing code is requested 
            threading1 = Thread(target=interpret, args=[message["data"]["uid"], "", True])
            threading1.daemon = True
            threading1.start()


writeLog("info", "Start stream")
my_stream = db.child("users").stream(stream_handler)

import sched, time
s = sched.scheduler(time.time, time.sleep)

def do_something(sc): 
    global my_stream
    writeLog("info", "Restart stream")
    my_stream.close()
    firebase = pyrebase.initialize_app(config)
    db = firebase.database()

    my_stream = db.child("users").stream(stream_handler)

    s.enter(600, 1, do_something, (sc,))

s.enter(600, 1, do_something, (s,))
s.run()