import os
from flask import Blueprint, jsonify
import requests
from dotenv import load_dotenv
from utils.session_management import create_response

load_dotenv()

COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')

coingecko_bp = Blueprint('coingecko_bp', __name__)


@coingecko_bp.route('/coingecko/usage', methods=['GET'])
def coingecko_usage():
    """
    Retrieve CoinGecko API usage information.
    """
    url = 'https://pro-api.coingecko.com/api/v3/key'
    headers = {'X-Cg-Pro-Api-Key': COINGECKO_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(create_response(success=True, data=response.json())), 200
    except requests.RequestException as e:
        error_message = f"Error fetching CoinGecko API usage: {str(e)}"
        if e.response:
            error_message += f" Response: {e.response.text}"
        return jsonify(create_response(success=False, error=error_message)), 500