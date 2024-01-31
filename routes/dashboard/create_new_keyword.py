from config import Keyword
from flask import jsonify
from flask import request
from config import Session as DBSession 
from flask import Blueprint

new_keyword = Blueprint('new_kw', __name__)

@new_keyword.route('/save_keyword', methods=['POST'])
def save_keyword():
    try:
        # Obtener datos del cuerpo de la solicitud (POST request)
        data = request.json

        # Crear una nueva instancia de la clase Keyword con los datos proporcionados
        new_keyword = Keyword(
            word=data.get('keyword'),  # Cambiado de 'keyword' a 'word'
            coin_bot_id=data.get('coin_bot_id')
            # Puedes agregar más campos según sea necesario
        )

        # Guardar el nuevo objeto Keyword en la base de datos
        with DBSession() as db_session:
            db_session.add(new_keyword)
            db_session.commit()

        return jsonify({'success': True, 'message': 'Keyword saved successfully'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})