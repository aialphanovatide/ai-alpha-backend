# socketio_events.py
from flask_socketio import SocketIO, emit

socketio = SocketIO(cors_allowed_origins="*")

# @socketio.on('update_topstory', namespace='/topstory')
# def handle_update_topstory():
#     print("Received update_topstory event")
#     emit('update_topstory_response', {'data': 'Update received'}, broadcast=True)
