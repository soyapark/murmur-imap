import pyrebase
from Auth import Auth
from threading import Event, Thread
from Monitor import *
import sys
try:
    from StringIO import StringIO
except ImportError:
    import io
import contextlib
from Log import *

config = {
  "apiKey": "###",
  "authDomain": "murmur-183618.firebaseapp.com",
  "databaseURL": "https://murmur-183618.firebaseio.com",
  "storageBucket": "murmur-183618.appspot.com",
  "serviceAccount": "cert/murmur-firebase.json"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


features = {}

def queue(func, folders):
    features['queue'] = [func, folders]

def logout():
    features['logout'] = []

monitors = {} # uid: monitor_instance

def stream_handler(message):
    # print(message["event"]) # put
    # print(message["path"]) # /-K7yGTTEp7O549EzTYtI
    print ("new Message")
    print (message)

    if message["data"] == None or "data" not in message:
        return
    # print message["data"].keys()[0]

    if "type" in message["data"]:
        # print ("hello")
        if message["data"]["type"] == "auth":
            writeLog("info", "write request", message["data"]["username"])
            monitor = Monitor(message["data"]["username"], message["data"]["password"], 'imap.gmail.com')
            server = monitor.imap

            uid = message["path"][1:] # uid
            db.child("users").child(message["path"][1:]).remove()

            if server == False:
                # send message to user auth fail
                data = {"code": 403, "auth": "Authentication Fail. Is it correct username/password?"}
                db.child("messages").child(uid).push(data)
                return

            else:
                # send message to user auth success
                data = {"code": 200, "auth": "Authentication Success."}
                db.child("messages").child(uid).push(data)

            monitors[uid] = monitor

            threading1 = Thread(target=monitor.monitor)
            threading1.daemon = True
            threading1.start()

            # ready.wait()
            # send message to user it's ready to play with

        elif message["data"]["type"] == "cmd":
            print ("New command", message["data"]["content"])
            features.clear()
            
            try:
                # exec( message["data"]["content"])
                with stdoutIO() as s:
                    exec( message["data"]["content"] )
                # print "out:", s.getvalue()
                # print features

                if 'logout' in features:
                    #kill thread
                    writeLog("info","Request for logout")
                    monitors[message["data"]["uid"]].logout()
                    data = {"type": "info", "content": s.getvalue() + "\nYou're logged out shortly. Bye!"}

                elif 'queue' in features:
                    writeLog("info", "Request for queue")
                    monitors[message["data"]["uid"]].queue( features['queue'][0], features['queue'][1])
                    data = {"type": "info", "content": s.getvalue() + "\nYour queue is successfully launched"}

                else: 
                    data = {"type": "info", "content": s.getvalue()}

                db.child("messages").child(message["data"]["uid"]).push(data)

                
            except Exception as e:
                writeLog( "critical", "Execution error %s" % (str(e)) )
                # Send this error msg to the user
                data = {"type": "error", "content": str(e)}
                db.child("messages").child(message["data"]["uid"]).push(data)


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