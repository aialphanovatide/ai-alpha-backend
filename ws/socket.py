from flask_socketio import SocketIO, emit
from flask import request
from typing import Any
from utils.logging import setup_logger
from typing import Any, Optional, Union, List

logger = setup_logger(__name__)

socketio = SocketIO(async_mode='threading', ping_timeout=60)

def init_socketio(app):
    print('---- Initializing SocketIO ----')
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     async_mode='threading',
                     ping_timeout=60,
                     ping_interval=25)
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
    

def emit_notification(
    event_name: str,
    data: Any,
    target: Optional[Union[str, List[str]]] = None,
) -> bool:
    """
    Emit a notification to specific targets or broadcast to all clients.
    """
    try:
        logger.info(f"Emitting {event_name} to {target if target else 'all'}")
        
        if target:
            targets = [target] if isinstance(target, str) else target
            for room_id in targets:
                socketio.emit(event_name, data, room=room_id)
                logger.debug(f"Emitted to room: {room_id}")
        else:
            # Use socketio.emit instead of emit
            socketio.emit(event_name, data)
            logger.debug("Broadcast emission complete")
            
        return True
        
    except Exception as e:
        logger.error(f"Emission failed: {str(e)}")
        return False

