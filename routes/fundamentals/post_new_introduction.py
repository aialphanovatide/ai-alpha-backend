from flask import Blueprint, request
from config import Introduction, Session
from flask import jsonify
from flask import request
from config import Session

post_new_introduction = Blueprint('postNewIntroduction', __name__)

@post_new_introduction.route('/post_introduction', methods=['POST'])
def create_content():
    try:
        # Obtiene los datos del cuerpo de la solicitud
        data = request.get_json()

        # Extrae el ID del Coin Bot y el contenido desde los datos
        coin_bot_id = data.get('id')
        content = data.get('content')

        # Validar que coin_bot_id no sea nulo o esté ausente
        if coin_bot_id is None:
            return jsonify({'error': 'id is required'}), 400

        new_introduction = Introduction(coin_bot_id=coin_bot_id, content=content)
        with Session() as session:
            session.add(new_introduction)
            session.commit()

        return jsonify({'message': 'Content created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
