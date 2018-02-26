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
from queue import * 

from Conf import *
from Auth import *
from EmailQueue import * 
from Cleanup import *

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

inbox = {} # uid: {"monitor": ~, "auth_info": ~, "cmd": ~}

class User():
    def __init__(self, monitor):
        self.monitor = monitor

    def __str__(self):
        return "????"

    def __enter__(self):
        return self

    def __exit__(self,  tp, value, traceback):
        pass

class Timer_(object):
    def __init__(self, time, uid, interval, func_id):
        self.time = time
        self.uid = uid
        self.interval = interval
        self.func_id = func_id

        writeLog("info", 'Timer: new task added ' +  uid + " " + str(interval))

    def __lt__(self, other):
        return self.time < other.time

class Arrival(object):
    def __init__(self, uid, action):
        pass


global execution_result, sch_ontime
execution_result = ""
sch_ontime = sched.scheduler(time.time, time.sleep)

def interpret(uid, cmd, isMonitor):
    with User(inbox[uid]["monitor"]) as u, stdoutIO() as s:
        def catch_exception(e):
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

                     

        def search(search_creteria):
            u.monitor.imap 

        def send(to_address, subject, content):
            writeLog("info","Request for sending email")

            # type checking
            if to_address is None or len(str(to_address)) == 0:
                raise Exception('send(): args to_addr must be provided')

            to_address = str(to_address)
            subject = str(subject)
            content = str(content)

            u.monitor.send(to_address, subject, content)

            writeLog ("info", "Requested email sent")
            print ("Email has been sent")

        def markRead(messages, read):
            if type(messages) is not Mmail:
                raise Exception('markRead(): args messages has to be a Mmail instance')

            messages.mark_read(read, messages.get_IDs())

        def onArrive(action):
            writeLog("info", "Request for onArrive")

            u.monitor.installOnArrive(action)
            inbox[uid]["onArrive_func"] = action

            print ("Your onArrive is successfully launched")

        def onCustom(action, cond):
            writeLog("info", "Request for onCustom")

            u.monitor.installOnCustom(action, cond)
            inbox[uid]["onCustom_func"] = action

            print ("Your onCustom is successfully launched")

        def onTime(doAction, minutes=None, seconds=None, hours=None):
            print("info", "onTime triggered")
            
            # global sch_ontime
            # sch_ontime.enter(interval, 1, onTime_helper, (action, interval, sch_ontime,))
            # sch_ontime.run()

            print ("Your onTime is successfully launched")

        def onTime_helper(action, target_time, interval):
            # TODO: pass a pile of email 

            # get uid of emails within interval
            now = datetime.now()
            start_time = now - timedelta(seconds = interval) 
            today_email = Mmail(u.monitor.imap, 'SINCE "%d-%s-%d"' % (start_time.day, calendar.month_abbr[start_time.month], start_time.year))
            min_msgid = 99999
            for msg in today_email.get_date():
                msgid, t = msg
                date_tuple = email.utils.parsedate_tz(t)
                if date_tuple:
                    local_date = datetime.fromtimestamp(
                        email.utils.mktime_tz(date_tuple))

                    if start_time < local_date and min_msgid > msgid:
                        min_msgid = msgid

            emails = Mmail(u.monitor.imap, "UID %d:*" % (min_msgid))
            action(emails)

        def logout():
            #kill thread
            writeLog("info","Request for logout")
            db.child("running").child(uid).remove()

            u.monitor.login = False
            u.monitor.imap.logout()

        

        def repeat(doAction, minutes=None, seconds=None, hours=None):
            interval = 0
   
            if minutes is not None and isinstance(minutes, (int, float, complex)):
                # convert min to sec
                interval = minutes * 60
            elif seconds is not None and isinstance(seconds, (int, float, complex)): 
                interval = seconds
            elif hours is not None and isinstance(hours, (int, float, complex)):
                interval = hours * 3600
            else:
                raise Exception('repeat(): args minutes|seconds|hours has to be a number')

            if interval < 60:
                raise Exception('repeat(): interval is too short! Please set larger than 1 min')

            now = datetime.now()
            target_time = now + timedelta(seconds = interval)

            inbox[uid]["monitor"].installRepeat(doAction, target_time, interval)

            # global tasks
            # tasks.put( Timer_(target_time, uid, interval, inbox[uid]["monitor"].repeat["id"]) )

            print ("Your repeat() is successfully launched")

        def renew():
            if hasattr(u.monitor, 'OAUTH'):
                u.monitor.authenticate_oauth()
            else:
                u.monitor.authenticate_plain()

            # reexecute code
            # writeLog("info", "Reexecute code")
            # interpret(uid, inbox[uid]["cmd"], False)

            # re-fork
            threading1 = Thread(target=interpret, args=[uid, "", True])
            threading1.daemon = True
            threading1.start()

        if isMonitor:
            writeLog('info', '... script started', u.monitor.USERNAME)

            try: 
                while True:
                    # <--- Start of mail monitoring loop

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
                    writeLog('info', 'MURMUR: IDLE- Start of mail monitoring loop', u.monitor.USERNAME)

                    # TODO: Remove hard-coded IDLE timeout; place in config file
                    result = u.monitor.imap.idle_check(30) # sec
                    if result:
                        with stdoutIO() as monitor_s:
                            u.monitor.imap.idle_done()

                            newID = u.monitor.fetchLatestEmailID()

                            # new mail
                            if u.monitor.getLatestEmailID() < newID: 
                                while u.monitor.getLatestEmailID() < newID:
                                    nextEmail_id = u.monitor.getLatestEmailID() + 1
                                    writeLog('info', 'MURMUR: a new email has arrived ' + str(nextEmail_id), u.monitor.USERNAME)
                                    print ('MURMUR: a new email has arrived')

                                    # Increment newest email ID
                                    u.monitor.setLatestEmailID( nextEmail_id )

                                    # for msgid, data in response.items():
                                    #     print('   ID %d: flags=%s' % (msgid,
                                    #                                             data[b'FLAGS']))
                                    # print ""


                                    if inbox[uid]["monitor"].arrive:
                                        try: 
                                            writeLog ("info", "onArrive triggered")
                                            inbox[uid]["monitor"].arrive["action"]( Mmail(inbox[uid]["monitor"].imap, "UID " + str(nextEmail_id)) ) # do defined action
                                        except Exception as e:
                                            catch_exception(e)
                                        
                                    if inbox[uid]["monitor"].custom:
                                        try:                                        
                                            if not inbox[uid]["monitor"].custom["queue"].push(nextEmail_id): # do defined action
                                                writeLog ("info","onCustom triggered")
                                                inbox[uid]["monitor"].custom["action"]( inbox[uid]["monitor"].custom["queue"].getMmail() ) # do defined action
                                        except Exception as e:
                                            catch_exception(e)


                                data = {"type": "info", "content": monitor_s.getvalue()}
                                pushMessage(["messages", uid], data)

                            else:
                                writeLog('info', 'MURMUR: user checks email', u.monitor.USERNAME)
                                result = u.monitor.search('UNSEEN')

                    else:
                        u.monitor.imap.idle_done()
                        u.monitor.imap.noop()
                        writeLog('info', 'no new messages seen', u.monitor.USERNAME)
                    
                    if inbox[uid]["monitor"].time and inbox[uid]["monitor"].time["target_time"] < datetime.now():
                        writeLog('info', 'onTime triggered')
                        
                        try: 
                            onTime_helper(inbox[uid]["monitor"].time["action"], inbox[uid]["monitor"].time["target_time"], inbox[uid]["monitor"].time["interval"])
                        except Exception as e:
                            catch_exception(e)

                        inbox[uid]["monitor"].time = ''

                    if inbox[uid]["monitor"].repeat and inbox[uid]["monitor"].repeat["target_time"] < datetime.now():
                        writeLog('info', 'repeat triggered')
                        
                        try:
                            onTime_helper(inbox[uid]["monitor"].repeat["action"], inbox[uid]["monitor"].repeat["target_time"], inbox[uid]["monitor"].repeat["interval"])

                            inbox[uid]["monitor"].repeat["target_time"] = datetime.now() + timedelta(seconds=inbox[uid]["monitor"].repeat["interval"])
                        except Exception as e:
                            catch_exception(e)

                    # End of mail monitoring loop --->
                    
                writeLog('info', 'script stopped ...', u.monitor.USERNAME)
              
            except Exception as e:
                catch_exception(e)

                # reauthenticate
                writeLog("info", "disconnect imap . Try reauthenticate \n", u.monitor.USERNAME)
                renew()   

                               
        else: # code execution
            try: 
                if "action" in cmd and hasattr(cmd["action"], '__call__'): #repeat, onTime
                    onTime_helper(cmd["action"], cmd["start_time"])
                    return True

                else:
                    inbox[uid]["cmd"] = cmd
                    db.child("running").child(uid).set(cmd)

                    d = dict(locals(), **globals())
                    exec( cmd, d, d)

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

                return False


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

        if message["data"]["type"] == "auth" or message["data"]["type"] == "oauth":
            writeLog("info", "auth request", message["data"]["username"])
            uid = message["path"][1:].split("/")[0] # uid
            monitor = "" # monitor instance

            if message["data"]["type"] == "auth": 
                monitor = Monitor(message["data"]["username"], message["data"]["password"], 'imap.gmail.com', False)

                # remove user auth info for the sake of privacy
                db.child("users").child(message["path"][1:]).remove()

                # create a new monitor only when there is none.
                if monitor.imap and not uid in inbox:
                    tmp = {"monitor": monitor, "start": False, "auth_info": {"type": "plain", "username": message["data"]["username"], "password": message["data"]["password"]}, "cmd": ""}
                    inbox[uid] = tmp

            else: # oauth
                monitor = Monitor(message["data"]["username"], message["data"]["code"], 'imap.gmail.com', True)

                try:
                    monitor.authenticate_oauth(message["data"]["code"])

                    # create a new monitor only when there is none.
                    if not uid in inbox:
                        tmp = {"monitor": monitor, "start": False, "auth_info": {"type": "plain", "username": message["data"]["username"], "refresh_token": monitor.REFRESH_TOKEN, "cmd": ""}}
                        inbox[uid] = tmp
                except Exception:
                    monitor.imap = False

            if monitor.imap == False:
                # send message to user auth fail
                data = {"code": 403, "auth": "Fail to log in."}
                pushMessage(["messages", uid], data)
                # db.child("messages").child(uid).push(data)
                return

            else:
                # send message to user auth success
                data = {"code": 200, "auth": "Authentication Success."}
                pushMessage(["messages", uid], data)
            
        elif message["data"]["type"] == "cmd":
            writeLog ("info", "New command Request", message["data"]["content"])
            
            interpret(message["data"]["uid"], message["data"]["content"], False)

            if not inbox[message["data"]["uid"]]["start"]:
                # start monitoring only when executing code is requested 
                inbox[message["data"]["uid"]]["start"] = True
                threading1 = Thread(target=interpret, args=[message["data"]["uid"], "", True])
                threading1.daemon = True
                threading1.start()



### START timer listener ###
############################ 

global tasks
tasks = PriorityQueue()

def timer_init():
    while True:
        if not tasks.empty() and tasks.queue[0].time < datetime.now():
            t = tasks.get()

            if t.uid not in inbox:
                continue

            # if this task is repeat func
            if inbox[t.uid]["monitor"].repeat and t.func_id == inbox[t.uid]["monitor"].repeat["id"]:
                # if there is error during executing code, don't add to a queue
                start_time = datetime.now() - timedelta(seconds = t.interval)
                time_obj= {"action": inbox[t.uid]["monitor"].repeat["action"], "start_time":start_time}
                if interpret(t.uid, time_obj, False):    # time, uid, interval, func_id
                    target_time = datetime.now() + timedelta(seconds = t.interval)
                    tasks.put( Timer_(target_time, t.uid, t.interval, t.func_id) )

            elif inbox[t.uid]["monitor"].time and t.func_id == inbox[t.uid]["monitor"].time["id"]:
                start_time = datetime.now() - timedelta(seconds = t.interval)
                time_obj= {"action": inbox[t.uid]["monitor"].time["action"], "start_time":start_time}
                interpret(t.uid, time_obj, False)   

            else: 
                continue

            writeLog("info", "Timer event triggered")            


timer_thread = Thread(target=timer_init, args=[])
timer_thread.daemon = True
timer_thread.start()

### END timer listener ###
############################



### START streaming for user-input ###
############################
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
### END streaming for user-input ###
############################