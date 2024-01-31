from config import Keyword 
from flask import jsonify
from config import Session as DBSession 
from flask import Blueprint

all_keywords = Blueprint('getAllKeywords', __name__)

@all_keywords.route('/get_keywords_for_coin_bot/<int:coin_bot_id>', methods=['GET'])
def get_keywords_for_coin_bot(coin_bot_id):
    print(coin_bot_id)
    try:
        with DBSession() as db_session:
            # Obtener las palabras clave para el coinBot específico
            keywords = db_session.query(Keyword).filter_by(coin_bot_id=coin_bot_id).all()
            keywords_data = [{'id': keyword.keyword_id, 'word': keyword.word} for keyword in keywords]
            return jsonify({'success': True, 'keywords': keywords_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})