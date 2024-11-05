from flask import Blueprint, request, jsonify
from services.coingecko.coingecko import get_tokenomics_data

ask_ai_bp = Blueprint('ask_ai', __name__)

@ask_ai_bp.route('/ask-ai', methods=['GET'])
def ask_ai():
    """
    Endpoint to retrieve detailed information about a cryptocurrency.

    Query Parameter:
        coin_name (str): The name of the cryptocurrency.

    Returns:
        JSON: Detailed information or an error message.
    """
    coin_name = request.args.get('coin_name')
    if not coin_name:
        return jsonify({'error': 'The parameter coin_name is required'}), 400

    tokenomics_data = get_tokenomics_data(coin_name)
    if 'error' in tokenomics_data:
        return jsonify({'error': tokenomics_data['error']}), 404

    return jsonify(tokenomics_data), 200