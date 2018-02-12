# from Log import *

# MONITOR = "monitor-instance"
# UID = "current user-uid"

# def send(to_address, subject, content):
#     writeLog("info","Request for sending email")
#     # u.monitor.send(to_address, subject, content)

# def queue(func, qwe, folders):
#     writeLog("info", "Request for queue")
#     # global queue_action 
#     # queue_action = action
#     u.monitor.queue(func, qwe, folders)
#     # qwe()
#     data = {"type": "info", "content": s.getvalue() + "\nYour queue is successfully launched"}
#     db.child("messages").child(uid).push(data)

# def logout():
#     #kill thread
#     writeLog("info","Request for logout")
#     u.monitor.logout()
#     data = {"type": "info", "content": s.getvalue() + "\nYou're logged out shortly. Bye!"}
#     db.child("messages").child(uid).push(data)
