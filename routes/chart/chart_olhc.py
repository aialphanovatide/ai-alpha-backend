import datetime
from typing import List, Dict, Union, Tuple, Optional
from flask import request, jsonify, Blueprint
from dotenv import load_dotenv
import requests
import os
from datetime import datetime, timedelta

chart_graphs_bp = Blueprint('chart_graphs_bp', __name__)

# Load environment variables
load_dotenv()

COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
COINGECKO_API_URL = os.getenv('COINGECKO_API_URL')
BINANCE_API_URL = os.getenv('BINANCE_API_URL')

# Parse HEADERS from a JSON string to a dictionary
HEADERS = {'X-Cg-Pro-Api-Key': COINGECKO_API_KEY}

def get_ohlc_binance_data(symbol: str, vs_currency: str, interval: str, precision: Optional[int] = None) -> Tuple[Optional[List[List[Union[int, float]]]], int]:
    symbol = symbol
    
    if not symbol:
        return None, 404

    pair = f"{symbol.upper()}{vs_currency.upper()}T"
    endpoint = f"{BINANCE_API_URL}/klines"
    params = {
        'symbol': pair,
        'interval': interval,
        'limit': 30
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
    
def consolidate_ohlc_data(data, interval):
    consolidated = {}
    for entry in data:
        timestamp = datetime.fromtimestamp(entry[0] / 1000)
        if interval == '1d':
            key = timestamp.date()
        elif interval == '1w':
            key = timestamp.date() - timedelta(days=timestamp.weekday())
        else:
            # Para otros intervalos, puedes agregar más lógica aquí
            key = timestamp

        if key not in consolidated:
            consolidated[key] = {
                'open': entry[1],
                'high': entry[2],
                'low': entry[3],
                'close': entry[4]
            }
        else:
            consolidated[key]['high'] = max(consolidated[key]['high'], entry[2])
            consolidated[key]['low'] = min(consolidated[key]['low'], entry[3])
            consolidated[key]['close'] = entry[4]

    return [
        [int(key.timestamp() * 1000) if isinstance(key, datetime) else int(datetime.combine(key, datetime.min.time()).timestamp() * 1000),
         data['open'], data['high'], data['low'], data['close']]
        for key, data in sorted(consolidated.items())
    ]

def get_ohlc_coingecko_data(coin: str, gecko_id: str, vs_currency: str, interval: str, precision: Optional[str] = None) -> Tuple[Union[List[List[Union[int, float]]], Dict[str, str]], int]:
    binance_data, binance_status = get_ohlc_binance_data(coin, vs_currency, interval, precision)
    if binance_data:
        consolidated_data = consolidate_ohlc_data(binance_data, interval)
        return consolidated_data, binance_status

    coingecko_id = gecko_id
    
    if not coingecko_id:
        return {"error": "Coin not found"}, 404

    try:
        endpoint = f"{COINGECKO_API_URL}/coins/{coingecko_id}/ohlc"
        params = {
            'vs_currency': vs_currency,
            'days': '180' if interval == '1w' else '30'
        }
        if precision:
            params['precision'] = precision

        response = requests.get(endpoint, params=params, headers=HEADERS)
        response.raise_for_status()
        
        raw_data = response.json()
        consolidated_data = consolidate_ohlc_data(raw_data, interval)
        return consolidated_data, 200
    except requests.exceptions.HTTPError as http_err:
        return {"error": str(http_err)}, response.status_code
    except requests.exceptions.RequestException as req_err:
        return {"error": str(req_err)}, 500

def get_ohlc_data(coin: str,gecko_id: str, vs_currency: str, interval: str, precision: Optional[str] = None) -> Tuple[Union[List[List[Union[int, float]]], Dict[str, str]], int]:
    # Primero intentamos obtener datos de Binance
    binance_data, binance_status = get_ohlc_binance_data(coin, vs_currency, interval, precision)
    
    if binance_data:
        consolidated_data = consolidate_ohlc_data(binance_data, interval)
        return consolidated_data, binance_status
    
    # Si no hay datos de Binance, consultamos a CoinGecko
    coingecko_id = gecko_id
    if not coingecko_id:
        return {"error": "Coin not found"}, 404

    try:
        endpoint = f"{COINGECKO_API_URL}/coins/{coingecko_id}/ohlc"
        params = {
            'vs_currency': vs_currency,
            'days': '180' if interval == '1w' else '30'
        }
        if precision:
            params['precision'] = precision

        response = requests.get(endpoint, params=params, headers=HEADERS)
        response.raise_for_status()
        raw_data = response.json()
        consolidated_data = consolidate_ohlc_data(raw_data, interval)
        return consolidated_data, 200
    except requests.exceptions.HTTPError as http_err:
        return {"error": str(http_err)}, response.status_code
    except requests.exceptions.RequestException as req_err:
        return {"error": str(req_err)}, 500


@chart_graphs_bp.route('/chart/ohlc', methods=['GET'])
def ohlc() -> Tuple[Union[str, Dict[str, Union[str, List[List[Union[int, float]]]]]], int]:
    gecko_id = request.args.get('gecko_id', '').lower()
    vs_currency = request.args.get('vs_currency', 'usd')
    interval = request.args.get('interval', '1h')
    precision = request.args.get('precision')
    symbol = request.args.get('precision')
    
    if not gecko_id:
        return jsonify({"error": "Missing required parameter: 'gecko_id'"}), 400
    if not symbol:
        return jsonify({"error": "Missing required parameter: 'symbol'"}), 400
    if vs_currency not in ['usd', 'btc', 'eth']:
        return jsonify({"error": "VS currency not supported. Must be 'usd', 'btc', or 'eth'"}), 400
    if interval not in ['1h', '4h', '1d', '1w']:
        return jsonify({"error": "Invalid interval. Must be '1h', '4h', '1d', or '1w'"}), 400
    if precision:
        try:
            precision_int = int(precision)
            if precision_int < 0 or precision_int > 18:
                return jsonify({"error": "Precision must be a non-negative integer not exceeding 18"}), 400
        except ValueError:
            return jsonify({"error": "Precision must be a valid integer"}), 400

    data, status_code = get_ohlc_data(symbol, gecko_id, vs_currency, interval, precision)
    return jsonify(data), status_code












