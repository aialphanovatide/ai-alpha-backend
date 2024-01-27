from flask import Blueprint, request, jsonify
from config import Tokenomics, Session
from sqlalchemy.orm import joinedload

get_coin_bot_tokenomics = Blueprint('getCoinBotTokenomics', __name__)

@get_coin_bot_tokenomics.route('/get_coin_bot_tokenomics/<int:coin_bot_id>', methods=['GET'])
def get_tokenomics(coin_bot_id):
    try:
        with Session() as session:
            # Realizar una consulta para obtener los tokenomics del Coin Bot específico
            tokenomics = (
                session.query(Tokenomics)
                .filter_by(coin_bot_id=coin_bot_id)
                .options(joinedload(Tokenomics.coin_bot))
                .first()
            )

            if tokenomics:
                # Devolver la información de los tokenomics en formato JSON
                return jsonify({
                    'coinBotInfo': {
                        'totalSupply': tokenomics.total_supply,
                        'circulatingSupply': tokenomics.circulating_supply,
                        'percentCirculatingSupply': tokenomics.percent_circulating_supply,
                        'maxSupply': tokenomics.max_supply,
                        'supplyModel': tokenomics.supply_model,
                    }
                })
            else:
                return jsonify({'error': 'Tokenomics not found for the specified Coin Bot'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
