import socketio
import eventlet
import eventlet.wsgi
from flask import Flask, render_template

sio = socketio.Server(cors_allowed_origins='*')
app = Flask(__name__)
sid_list = []

#* Function to handle send message event
def sendMessage(message, event):
    for _sid in sid_list:
        sio.emit(event, message, _sid['sid'])

#* Function to handle when new user join
#* to the chatroom
def addUserConnection(sid, data):
    joinedSid = sid
    username = str(data)

    if len(sid_list) > 0:
        for _sid in sid_list:
            if username not in _sid['username']:
                sid_list.append({
                    "sid": joinedSid,
                    "username": username
                })
                break
    else:
        sid_list.append({
            "sid": joinedSid,
            "username": username
        })
    
    #* Broadcast send message
    print("{} joining the room".format(username))
    sendMessage("{} joining the room|{}".format(username, str(len(sid_list))), "join")

#* Function to handle when the user leaving
#* the room
def removeUserConnection(sid):
    for x in range(0, len(sid_list)):
        if sid_list[x]['sid'] == sid:
            #* Broadcast send message
            sendMessage("{} leaving the room|{}".format(sid_list[x]['username'], str(len(sid_list)-1)), "leaving")
            del sid_list[x]
    
#* Function to check if the username
#* already exists in chatroom
def checkUserExists(sid, data):
    username = data
    available = False
    if len(sid_list) > 0:
        for _sid in sid_list:
            if username not in _sid['username']:
                available = True
    else:
        available = True

    #* Send response to mobile
    sio.emit("checkuser", "available" if available == True else "not available", sid)

@sio.on('connect', namespace='/')
def connect(sid, environ):
    print("Connected SID: ", sid)

@sio.on('join', namespace='/')
def join(sid, data):
    #* Add sid and username
    addUserConnection(sid, data)

@sio.on('leaving', namespace='/')
def leaving(sid, data):
    #* Remove from sid list
    removeUserConnection(sid)

@sio.on('checkuser', namespace='/')
def checkuser(sid, data):
    checkUserExists(sid, data)

@sio.on('typing', namespace='/')
def typing(sid, data):
    #* Broadcast to all users
    sendMessage(data, "typing")

@sio.on('message', namespace='/')
def message(sid, data):
    print(data)

    #* Send message
    sendMessage(data, "message")

@sio.on('disconnect', namespace='/')
def disconnect(sid):
    print('disconnect ', sid)

    #* Remove from sid list
    removeUserConnection(sid)

if __name__ == '__main__':
    # wrap Flask application with engineio's middleware
    app = socketio.Middleware(sio, app)

    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('192.168.200.16', 8004)), app)