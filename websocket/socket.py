# socketio_events.py
from flask import request
from flask_socketio import SocketIO, emit

socketio = SocketIO(cors_allowed_origins="*",
                    ping_timeout=60, 
                    ping_interval=20, 
                    websocket_timeout=60) 


# ---------------------------- LOGS --------------------------------------- #

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    print(f'A client with ID {client_id} has connected')
    emit('new_alert', f'Hello, you are connected. Your ID is {client_id}')


@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    print(f'A client with ID {client_id} has disconnected')


@socketio.on('error')
def handle_error(error):
    client_id = request.sid
    print(f'An error occurred for client with ID {client_id}: {error}')
