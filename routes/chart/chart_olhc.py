import os
import time
import requests
from typing import Optional
from dotenv import load_dotenv
from flask import request, jsonify, Blueprint

chart_graphs_bp = Blueprint('chart_graphs_bp', __name__)

# Load environment variables
load_dotenv()

COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
COINGECKO_API_URL = os.getenv('COINGECKO_API_URL')
BINANCE_API_URL = os.getenv('BINANCE_API_URL')
HEADERS = {'X-Cg-Pro-Api-Key': COINGECKO_API_KEY}

def get_ohlc_binance_data(symbol: str, vs_currency: str, interval: str, precision: Optional[int] = None):
    """
    Fetch OHLC data from Binance for a specified trading pair and time interval.
    """
    pair = f"{symbol.upper().strip()}{vs_currency.upper().strip()}T"
    endpoint = f"{BINANCE_API_URL}/v3/klines"

    params = {
        'symbol': pair,
        'interval': interval.casefold(),
        'limit': 180
    }

    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        if data:
            precision_int = int(precision) if precision is not None else None
            ohlc_data = [
                [
                    int(candle[0]),
                    round(float(candle[1]), precision_int) if precision_int is not None else float(candle[1]),
                    round(float(candle[2]), precision_int) if precision_int is not None else float(candle[2]),
                    round(float(candle[3]), precision_int) if precision_int is not None else float(candle[3]),
                    round(float(candle[4]), precision_int) if precision_int is not None else float(candle[4])
                ] for candle in data
            ]
            return ohlc_data, 200
        return None, 404
    except requests.exceptions.RequestException as e:
        return None, 500

def get_ohlc_coingecko_data(gecko_id: str, vs_currency: str, interval: str, precision: Optional[int] = None):
    """
    Fetch OHLC data from CoinGecko for a specific coin using its Gecko ID and specified time interval.
    """
    try:
        endpoint = f"{COINGECKO_API_URL}/coins/{gecko_id}/ohlc"
        days = 180 if interval == '1w' else 30
        params = {
            'vs_currency': vs_currency,
            'days': days,
        }
        if precision:
            params['precision'] = int(precision)

        response = requests.get(endpoint, params=params, headers=HEADERS)
        response.raise_for_status()
        raw_data = response.json()
        
        if not raw_data:  # Check if no data is returned
            return None, 404
        
        return raw_data, 200
    except requests.exceptions.HTTPError as http_err:
        return None, response.status_code  
    except requests.exceptions.RequestException as req_err:
        return None, 500  
    

@chart_graphs_bp.route('/chart/ohlc', methods=['GET'])
def ohlc_chart():
    response = {
        'data': None,
        'error': None,
    }
    
    try:
        # Retrieve query parameters
        gecko_id = request.args.get('gecko_id', '').lower()
        vs_currency = request.args.get('vs_currency', 'usd')
        interval = request.args.get('interval', '1h')
        precision = request.args.get('precision')
        symbol = request.args.get('symbol')

        # Validate required parameters
        if not gecko_id:
            response['error'] = "Missing required parameter: 'gecko_id'"
            return jsonify(response), 400
        if not symbol:
            response['error'] = "Missing required parameter: 'symbol'"
            return jsonify(response), 400
        if vs_currency not in ['usd', 'btc', 'eth']:
            response['error'] = "VS currency not supported. Must be 'usd', 'btc', or 'eth'"
            return jsonify(response), 400
        if interval not in ['1h', '4h', '1d', '1w']:
            response['error'] = "Invalid interval. Must be '1h', '4h', '1d', or '1w'"
            return jsonify(response), 400
        
        # Validate precision if provided
        if precision:
            try:
                precision_int = int(precision)
                if precision_int < 0 or precision_int > 18:
                    response['error'] = "Precision must be a non-negative integer not exceeding 18"
                    return jsonify(response), 400
            except ValueError:
                response['error'] = "Precision must be a valid integer"
                return jsonify(response), 400

        # Fetch OHLC data
        start_time = time.time()
        data, status = get_ohlc_binance_data(symbol, vs_currency, interval, precision)
        if data:
            print("--- Data coming from Binance ---")
            response['data'] = data
            end_time = time.time()
            print(f"Total request time: {end_time - start_time:.2f} seconds")
            return jsonify(response), status


        data, status_code = get_ohlc_coingecko_data(gecko_id, vs_currency, interval, precision)

        end_time = time.time()
        print(f"Total request time: {end_time - start_time:.2f} seconds")
        
        response['data'] = data
        return jsonify(response), status_code
    
    except Exception as e:
        response['error'] = str(e)
        return jsonify(response), 500


