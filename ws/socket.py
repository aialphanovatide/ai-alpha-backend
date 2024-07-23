from flask_socketio import SocketIO, emit
from flask import request

socketio = SocketIO()

def init_socketio(app):
    socketio.init_app(app)
    return socketio

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    print(f"Client connected - ID: {client_id}")
    print(f"Connection details:")
    print(f"  Remote address: {request.remote_addr}")
    print(f"  User agent: {request.headers.get('User-Agent')}")
    print(f"  Origin: {request.origin}")
    emit('connection_info', {'client_id': client_id})

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    print(f"Client disconnected - ID: {client_id}")