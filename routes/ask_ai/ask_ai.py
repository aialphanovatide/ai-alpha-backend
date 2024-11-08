from flask import Blueprint, request, jsonify
from services.coingecko.coingecko import get_tokenomics_data, get_list_of_coins
from redis_client.redis_client import cache_with_redis

ask_ai_bp = Blueprint('ask_ai', __name__)

@ask_ai_bp.route('/ask-ai/coins', methods=['GET'])
@cache_with_redis(expiration=86400)
def list_coins():
    """
    Get a list of all available cryptocurrencies or filter by names/symbols.

    Query Parameters:
        names (str, optional): Comma-separated list of coin names
        symbols (str, optional): Comma-separated list of coin symbols

    Returns:
        dict: A dictionary containing:
            - coins: List of coin information
            - length: Number of coins returned
            - success: Operation status
    """
    try:        
        result = get_list_of_coins()
        return jsonify({
            'coins': result['coins'],
            'length': result['length'],
            'success': True,
            'error': None
        }), 200
        
    except Exception as e:
        return jsonify({
            'coins': [],
            'length': 0,
            'error': str(e),
            'success': False
        }), 500


@ask_ai_bp.route('/ask-ai', methods=['GET'])
def ask_ai():
    """
    Endpoint to retrieve detailed information about a cryptocurrency.

    Query Parameter:
        coin_name (str): The name of the cryptocurrency.

    Returns:
        JSON: Detailed information or an error message.
    """
    coin_id = request.args.get('coin_id')
    if not coin_id:
        return jsonify({'error': 'The parameter coin_id is required'}), 400

    tokenomics_data = get_tokenomics_data(coin_id)
    if 'error' in tokenomics_data:
        return jsonify({'error': tokenomics_data['error'],
                        'success': False,
                        'data': None}), 404

    return jsonify({'data': tokenomics_data, 
                    'success': True, 
                    'error': None}), 200