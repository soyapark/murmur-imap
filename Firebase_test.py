import pyrebase
from Auth import Auth
from threading import Event, Thread
from Monitor import Monitor
import sys
import StringIO
import contextlib

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
        stdout = StringIO.StringIO()
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
    print "new Message"
    print message

    if message["data"] == None or "data" not in message:
        return
    # print message["data"].keys()[0]

    if "type" in message["data"]:
        if message["data"]["type"] == "auth":
            auth = Auth(message["data"]["username"], message["data"]["password"], 'imap.gmail.com')
            server = auth.getServer()

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
            
            
            ready = Event()

            monitor = Monitor(server, ready, message["data"]["username"])
            monitors[uid] = monitor

            threading1 = Thread(target=monitor.monitor)
            threading1.daemon = True
            threading1.start()

            # ready.wait()
            # send message to user it's ready to play with

        elif message["data"]["type"] == "cmd":
            print "New command", message["data"]["content"]
            features.clear()
            
            try:
                # exec( message["data"]["content"])
                with stdoutIO() as s:
                    exec( message["data"]["content"] )
                print "out:", s.getvalue()
                print features

                if 'queue' in features:
                    print "Request for queue"
                    monitors[message["data"]["uid"]].queue( features['queue'][0], features['queue'][1])
                    data = {"type": "info", "content": s.getvalue() + "\nYour queue is successfully launched"}

                elif 'logout' in features:
                    #kill thread
                    print "Request for logout"
                    monitors[message["data"]["uid"]].logout()
                    data = {"type": "info", "content": s.getvalue() + "\nYou're logged out shortly. Bye!"}

                else: 
                    data = {"type": "info", "content": s.getvalue()}

                db.child("messages").child(message["data"]["uid"]).push(data)

                
            except Exception as e:
                print "Execution error ", str(e)
                # Send this error msg to the user
                data = {"type": "error", "content": str(e)}
                db.child("messages").child(message["data"]["uid"]).push(data)


my_stream = db.child("users").stream(stream_handler)