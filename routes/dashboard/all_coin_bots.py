from config import CoinBot
from flask import jsonify
from config import Session as DBSession 
from flask import Blueprint


coin_bots = Blueprint('allCoinBots', __name__)

@coin_bots.route('/get_all_coin_bots', methods=['GET'])
def get_all_coin_bots():
    try:
        with DBSession() as db_session:
            coin_bots = db_session.query(CoinBot.bot_id, CoinBot.bot_name).all()

        # Transformar la lista de tuplas a una lista de diccionarios
        coin_bots_data = [{'id': bot_id, 'name': bot_name} for bot_id, bot_name in coin_bots]

        return jsonify({'success': True, 'coin_bots': coin_bots_data})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

