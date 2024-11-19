from flask_socketio import SocketIO, emit
from flask import request

socketio = SocketIO()

def init_socketio(app):
    print('---- Initializing SocketIO ----')
    socketio.init_app(app, 
                      cors_allowed_origins="*",
                      reconnection=True)
    return socketio

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    print(f"Client connected - ID: {client_id}")
    print(f"Origin: {request.origin}")

    # Emit the client ID back to the connected client
    emit('client_connected', {'client_id': client_id}, room=client_id)

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    print(f"Client disconnected - ID: {client_id}")