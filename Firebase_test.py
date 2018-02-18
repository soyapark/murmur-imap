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
from datetime import datetime, time, timedelta
import calendar
import sched, time

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

inbox = {}

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
    if not message:
        return

    writeLog("info","Send a message to a server %s %s" % (path, message))

    db.child("/".join([p for p in path])).push(message)

global execution_result, onArrive_func, onCustom_func, sch_ontime
execution_result = ""
sch_ontime = sched.scheduler(time.time, time.sleep)

def interpret(uid, cmd, isMonitor):
    with User(inbox[uid]["monitor"]) as u, stdoutIO() as s:
    
        def search(search_creteria):
            u.monitor.imap 

        def send(to_address, subject, content):
            writeLog("info","Request for sending email")
            u.monitor.send(to_address, subject, content)

            global execution_result
            execution_result += "<br/>Requested email sent"

        def markRead(messages, read):
            messages.markRead(read, messages.getIDs())

        def onArrive(action, folders):
            writeLog("info", "Request for onArrive")

            u.monitor.installOnArrive(action, folders)
            inbox[uid]["onArrive_func"] = action

            # global execution_result
            # execution_result += 
            print ("Your onArrive is successfully launched")

        def onCustom(action, cond, folders):
            writeLog("info", "Request for onCustom")

            u.monitor.installOnCustom(action, cond, folders)
            inbox[uid]["onCustom_func"] = action

            print ("Your onCustom is successfully launched")

        def onTime(action, interval):
            print("info", "onTime triggered")
            global sch_ontime
            sch_ontime.enter(interval, 1, onTime_helper, (action, interval, sch_ontime,))
            sch_ontime.run()

        def onTime_helper(action, interval, sc):
            # TODO: pass a pile of email 

            # get uid of emails within interval
            now = datetime.now()
            before = now - timedelta(minutes = interval)

            today_email = Mmail(u.monitor.imap, 'SINCE "%d-%s-%d"' % (before.day, calendar.month_abbr[before.month], before.year))
            min_msgid = 99999
            for msg in today_email.getDate():
                msgid, t = msg
                date_tuple = email.utils.parsedate_tz(t)
                if date_tuple:
                    local_date = datetime.fromtimestamp(
                        email.utils.mktime_tz(date_tuple))

                    if before < local_date and min_msgid > msgid:
                        min_msgid = msgid

            emails = Mmail(u.monitor.imap, "UID %d:*" % (min_msgid))
            action(emails)
            sch_ontime.enter(interval, 1, onTime_helper, (action, interval,sc,))

        def logout():
            #kill thread
            writeLog("info","Request for logout")
            db.child("running").child(uid).remove()

            u.monitor.login = False
            u.monitor.imap.logout()

        def renew():
            u.monitor = Monitor(inbox[uid]["auth_info"]["username"], inbox[uid]["auth_info"]["password"], 'imap.gmail.com') 
            
            # reexecute code
            writeLog("info", "Reexecute code")
            interpret(uid, inbox[uid]["cmd"], False)

            # re-fork
            threading1 = Thread(target=interpret, args=[uid, "", True])
            threading1.daemon = True
            threading1.start()

        if isMonitor:
            writeLog('info', '... script started', u.monitor.USERNAME)

            try: 
                while True:
                    while True:
                        # <--- Start of IMAP server connection loop
                        
                        while True:
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
                                with stdoutIO() as monitor_s:
                                    u.monitor.imap.idle_done()

                                    # writeLog('info', "MURMUR: a new email has arrived || a user checks an email")
                                    newID = u.monitor.fetchLatestEmailID()

                                    # new mail
                                    if u.monitor.getLatestEmailID() != newID: 
                                        # writeLog('info', 'MURMUR: a new email has arrived', u.monitor.USERNAME)
                                        print ('MURMUR: a new email has arrived', u.monitor.USERNAME)

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


                                        if inbox[uid]["onArrive_func"]:
                                            writeLog ("info", "onArrive triggered")
                                            if not u.monitor.QUEUE.push(newID): # do defined action
                                                inbox[uid]["onArrive_func"]( u.monitor.QUEUE.messages )

                                        if inbox[uid]["onCustom_func"]:
                                            writeLog ("info","onCustom triggered")
                                            if not u.monitor.QUEUE.push(newID): # do defined action
                                                inbox[uid]["onCustom_func"]( u.monitor.QUEUE.messages ) # do defined action

                                        data = {"type": "info", "content": monitor_s.getvalue()}
                                        pushMessage(["messages", uid], data)

                                    else:
                                        writeLog('info', 'MURMUR: user checks email', u.monitor.USERNAME)
                                        result = u.monitor.search('UNSEEN')

                            else:
                                u.monitor.imap.idle_done()
                                u.monitor.imap.noop()
                                writeLog('info', 'no new messages seen', u.monitor.USERNAME)
                            # End of mail monitoring loop --->
                            continue
                        

                        # End of IMAP server connection loop --->
                        continue

                    # End of configuration section --->

                    continue
                writeLog('info', 'script stopped ...', u.monitor.USERNAME)
              
            except Exception as e:
                if not u.monitor.login:
                    inbox[uid]["start"] = False
                    return
                    
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

                # reauthenticate
                writeLog("info", "imap disconnected. Try reauthenticate")
                renew()

            
        else:
            try: # exception handling for user code execution 
                inbox[uid]["cmd"] = cmd
                db.child("running").child(uid).set(cmd)

                d = dict(locals(), **globals())
                exec( cmd, d, d)

                global execution_result
                data = {"type": "info", "content": s.getvalue()}
                pushMessage(["messages", uid], data)
                # db.child().child(uid).push(data)
                
            except Exception as e:
                if not u.monitor.login:
                    inbox[uid]["start"] = False
                    return

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
            
            uid = message["path"][1:].split("/")[0] # uid

            # remove user auth info for the sake of privacy
            print (message["path"])
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

            # create a new monitor only when there is none.
            if not uid in inbox:
                tmp = {"monitor": monitor, "start": False, "auth_info": {"type": "plain", "username": message["data"]["username"], "password": message["data"]["password"]}, "cmd": ""}
                inbox[uid] = tmp

            # ready.wait()
            # send message to user it's ready to play with

        elif message["data"]["type"] == "cmd":
            writeLog ("info", "New command Request", message["data"]["content"])
            
            interpret(message["data"]["uid"], message["data"]["content"], False)

            if not inbox[message["data"]["uid"]]["start"]:
                # start monitoring only when executing code is requested 
                inbox[message["data"]["uid"]]["start"] = True
                threading1 = Thread(target=interpret, args=[message["data"]["uid"], "", True])
                threading1.daemon = True
                threading1.start()


writeLog("info", "Start stream")
my_stream = db.child("users").stream(stream_handler)

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