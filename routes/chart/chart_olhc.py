from typing import List, Dict, Union, Tuple, Optional
from flask import request, jsonify, Blueprint
from ws.socket import socketio, emit
from typing import Dict, Any, Tuple 
from dotenv import load_dotenv
import requests
import logging
import os

chart_graphs_bp = Blueprint('chart_graphs_bp', __name__)

# Load environment variables
load_dotenv()

COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
COINGECKO_API_URL = "https://pro-api.coingecko.com/api/v3"
BINANCE_API_URL = "https://api3.binance.com/api/v3"
headers = {'X-Cg-Pro-Api-Key': COINGECKO_API_KEY}


# List of cryptocurrencies we have available
# Replace this using THE DATABASE
crypto_data = [
    {"symbol": "btc", "name": "Bitcoin", "coingecko_id": "bitcoin"},
    {"symbol": "eth", "name": "Ethereum", "coingecko_id": "ethereum"},
    {"symbol": "hacks", "name": "Hacks", "coingecko_id": "hacks"},
    {"symbol": "ldo", "name": "Lido", "coingecko_id": "lido-dao"},
    {"symbol": "rpl", "name": "Rocket Pool", "coingecko_id": "rocket-pool"},
    {"symbol": "fxs", "name": "Frax Share", "coingecko_id": "frax-share"},
    {"symbol": "atom", "name": "Cosmos", "coingecko_id": "cosmos"},
    {"symbol": "dot", "name": "Polkadot", "coingecko_id": "polkadot"},
    {"symbol": "qnt", "name": "Quant", "coingecko_id": "quant"},
    {"symbol": "ada", "name": "Cardano", "coingecko_id": "cardano"},
    {"symbol": "sol", "name": "Solana", "coingecko_id": "solana"},
    {"symbol": "avax", "name": "Avalanche", "coingecko_id": "avalanche-2"},
    {"symbol": "near", "name": "Near Protocol", "coingecko_id": "near"},
    {"symbol": "ftm", "name": "Fantom", "coingecko_id": "fantom"},
    {"symbol": "kas", "name": "Kaspa", "coingecko_id": "kaspa"},
    {"symbol": "matic", "name": "Polygon", "coingecko_id": "matic-network"},
    {"symbol": "arb", "name": "Arbitrum", "coingecko_id": "arbitrum"},
    {"symbol": "op", "name": "Optimism", "coingecko_id": "optimism"},
    {"symbol": "link", "name": "Chainlink", "coingecko_id": "chainlink"},
    {"symbol": "api3", "name": "API3", "coingecko_id": "api3"},
    {"symbol": "band", "name": "Band Protocol", "coingecko_id": "band-protocol"},
    {"symbol": "xlm", "name": "Stellar", "coingecko_id": "stellar"},
    {"symbol": "algo", "name": "Algorand", "coingecko_id": "algorand"},
    {"symbol": "xrp", "name": "Ripple", "coingecko_id": "ripple"},
    {"symbol": "dydx", "name": "dYdX", "coingecko_id": "dydx"},
    {"symbol": "velo", "name": "Velodrome", "coingecko_id": "velodrome-finance"},
    {"symbol": "gmx", "name": "GMX", "coingecko_id": "gmx"},
    {"symbol": "uni", "name": "Uniswap", "coingecko_id": "uniswap"},
    {"symbol": "sushi", "name": "SushiSwap", "coingecko_id": "sushi"},
    {"symbol": "cake", "name": "PancakeSwap", "coingecko_id": "pancakeswap-token"},
    {"symbol": "aave", "name": "Aave", "coingecko_id": "aave"},
    {"symbol": "pendle", "name": "Pendle", "coingecko_id": "pendle"},
    {"symbol": "1inch", "name": "1inch", "coingecko_id": "1inch"},
    {"symbol": "ocean", "name": "Ocean Protocol", "coingecko_id": "ocean-protocol"},
    {"symbol": "fet", "name": "Fetch.ai", "coingecko_id": "fetch-ai"},
    {"symbol": "rndr", "name": "Render", "coingecko_id": "render-token"},
]


def get_ohlc_binance_data(coin: str, vs_currency: str, interval: str, precision: Optional[int] = None) -> Tuple[Optional[List[List[Union[int, float]]]], int]:
    symbol = next((crypto['symbol'] for crypto in crypto_data if crypto['symbol'].lower() == coin.lower() or crypto['name'].lower() == coin.lower()), None)
    
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


def get_ohlc_coingecko_data(coin: str, vs_currency: str, interval: str, precision: Optional[str] = None) -> Tuple[Union[List[List[Union[int, float]]], Dict[str, str]], int]:
    binance_data, binance_status = get_ohlc_binance_data(coin, vs_currency, interval, precision)
    if binance_data:
        return binance_data, binance_status

    coingecko_id = next((crypto['coingecko_id'] for crypto in crypto_data if crypto['symbol'].lower() == coin.lower() or crypto['name'].lower() == coin.lower()), None)
    
    if not coingecko_id:
        return {"error": "Coin not found"}, 404

    try:
        endpoint = f"{COINGECKO_API_URL}/coins/{coingecko_id}/ohlc"
        params = {
            'vs_currency': vs_currency,
            'days': '30'
        }
        if precision:
            params['precision'] = precision

        response = requests.get(endpoint, params=params, headers=headers)
        response.raise_for_status()
        return response.json(), 200
    except requests.exceptions.HTTPError as http_err:
        return {"error": str(http_err)}, response.status_code
    except requests.exceptions.RequestException as req_err:
        return {"error": str(req_err)}, 500

@chart_graphs_bp.route('/api/chart/ohlc', methods=['GET'])
def ohlc() -> Tuple[Union[str, Dict[str, Union[str, List[List[Union[int, float]]]]]], int]:
    """
    Retrieves OHLC (Open, High, Low, Close) data for a specified cryptocurrency.

    Query Parameters:
        coin (str): The cryptocurrency identifier (e.g., 'bitcoin').
        vs_currency (str): The currency to compare against. Must be 'usd', 'btc', or 'eth'. Defaults to 'usd'.
        interval (str): The time interval for the data. Must be '1h', '4h', '1d', or '1w'. Defaults to '1h'.
        precision (str): The number of decimal places for the returned data. Must be a non-negative integer not exceeding 18.

    Returns:
        Tuple[Union[str, Dict[str, Union[str, List[List[Union[int, float]]]]]], int]: 
            A JSON response containing the OHLC data if the parameters are valid, along with an HTTP status code.

    Responses:
        200: Success - The OHLC data is returned.
        400: Bad Request - One or more parameters are invalid or missing.
    """
        
    coin = request.args.get('coin', '').lower()
    vs_currency = request.args.get('vs_currency', 'usd')
    interval = request.args.get('interval', '1h')
    precision = request.args.get('precision')

    if not coin:
        return jsonify({"error": "Missing required parameter: 'coin'"}), 400

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

    data, status_code = get_ohlc_coingecko_data(coin, vs_currency, interval, precision)
    return jsonify(data), status_code


def get_top_movers_data(vs_currency: str = 'usd', order: str = 'market_cap_desc', precision: Optional[int] = None) -> Tuple[Optional[Dict[str, Union[bool, Dict[str, List[Dict[str, Any]]], str]]], int, Optional[str]]:
    """
    Fetch and process top cryptocurrency movers data from CoinGecko API.

    This function retrieves cryptocurrency market data, sorts it based on the specified order,
    and returns the top 10 gainers and top 10 losers.

    Args:
        vs_currency (str): The target currency for market data (default: 'usd').
        order (str): The ordering criteria for the data (default: 'market_cap_desc').
            Valid options: 'market_cap_desc', 'market_cap_asc', 'volume_desc', 'volume_asc',
            'price_change_desc', 'price_change_asc'.
        precision (Optional[int]): The number of decimal places for price values (default: None).

    Returns:
        Tuple:
            - A dictionary containing the processed data if successful, None otherwise.
            - HTTP status code.
            - Error message if an error occurred, None otherwise.
    """
    valid_orders: List[str] = ['market_cap_desc', 'market_cap_asc', 'volume_desc', 'volume_asc', 'price_change_desc', 'price_change_asc']
    if order not in valid_orders:
        return None, 400, "Invalid order parameter"

    ids: List[str] = [crypto["coingecko_id"] for crypto in crypto_data]
    ids_string: str = ",".join(ids)

    url: str = f'{COINGECKO_API_URL}/coins/markets'
    params = {
        'vs_currency': vs_currency,
        'ids': ids_string,
        'order': 'market_cap_desc',  # Default order for initial fetch
        'per_page': 250,
        'page': 1,
        'sparkline': False,
        'price_change_percentage': '24h'
    }

    if precision is not None:
        params['precision'] = precision

    try:
        response: requests.Response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data: List[Dict[str, Any]] = response.json()
            
            # Sort based on the order parameter
            if order.startswith('market_cap'):
                sorted_data = sorted(data, key=lambda x: x['market_cap'] or 0, reverse=(order == 'market_cap_desc'))
            elif order.startswith('volume'):
                sorted_data = sorted(data, key=lambda x: x['total_volume'] or 0, reverse=(order == 'volume_desc'))
            elif order.startswith('price_change'):
                sorted_data = sorted(data, key=lambda x: x['price_change_percentage_24h'] or 0, reverse=(order == 'price_change_desc'))
            
            # Get top 10 and bottom 10
            top_10 = sorted_data[:10]
            bottom_10 = sorted_data[-10:][::-1]

            result = {
                "success": True,
                "data": {
                    "top_10_gainers": top_10,
                    "top_10_losers": bottom_10
                },
                "order": order
            }
            return result, 200, None
        else:
            return None, response.status_code, "Failed to fetch data from CoinGecko"
    except requests.RequestException as e:
        return None, 500, str(e)
    

# @chart_graphs_bp.route('/api/top-movers', methods=['GET'])
# def get_crypto_markets():
#     """
#     Retrieve top cryptocurrency movers based on specified criteria.

#     This endpoint fetches cryptocurrency market data from CoinGecko and returns the top 10 gainers and top 10 losers
#     based on the specified ordering criteria.

#     Query Parameters:
#     - vs_currency (str, optional): The target currency for market data (default: 'usd').
#     - order (str, optional): The ordering criteria for the data. Valid options are:
#       'market_cap_desc', 'market_cap_asc', 'volume_desc', 'volume_asc', 'price_change_desc', 'price_change_asc'
#       (default: 'market_cap_desc').
#     - precision (int, optional): The number of decimal places for price values.

#     Returns:
#     JSON object with the following structure:
#     {
#         "success": bool,
#         "data": {
#             "top_10_gainers": list,
#             "top_10_losers": list
#         },
#         "order": str
#     }

#     On error, returns a JSON object with error details and an appropriate HTTP status code.

#     Note: This function uses predefined cryptocurrency data (crypto_data) for fetching market information.
#     """
        
#     vs_currency = request.args.get('vs_currency', 'usd')
#     order = request.args.get('order', 'market_cap_desc')
#     precision = request.args.get('precision')
    
#     valid_orders = ['market_cap_desc', 'market_cap_asc', 'volume_desc', 'volume_asc', 'price_change_desc', 'price_change_asc']
#     if order not in valid_orders:
#         return jsonify({"success": False, "error": {"code": 400, "message": "Invalid order parameter"}}), 400

#     ids = [crypto["coingecko_id"] for crypto in crypto_data]
#     ids_string = ",".join(ids)

#     url = f'{COINGECKO_API_URL}/coins/markets'
#     params = {
#         'vs_currency': vs_currency,
#         'ids': ids_string,
#         'order': 'market_cap_desc',  # Default order for initial fetch
#         'per_page': 250,
#         'page': 1,
#         'sparkline': False,
#         'price_change_percentage': '24h'
#     }

#     if precision:
#         params['precision'] = precision

#     try:
#         response = requests.get(url, params=params, headers=headers)
#         if response.status_code == 200:
#             data = response.json()
            
#             # Sort based on the order parameter
#             if order.startswith('market_cap'):
#                 sorted_data = sorted(data, key=lambda x: x['market_cap'] or 0, reverse=(order == 'market_cap_desc'))
#             elif order.startswith('volume'):
#                 sorted_data = sorted(data, key=lambda x: x['total_volume'] or 0, reverse=(order == 'volume_desc'))
#             elif order.startswith('price_change'):
#                 sorted_data = sorted(data, key=lambda x: x['price_change_percentage_24h'] or 0, reverse=(order == 'price_change_desc'))
            
#             # Get top 10 and bottom 10
#             top_10 = sorted_data[:10]
#             bottom_10 = sorted_data[-10:][::-1]

#             result = {
#                 "success": True,
#                 "data": {
#                     "top_10_gainers": top_10,
#                     "top_10_losers": bottom_10
#                 },
#                 "order": order
#             }
#             return jsonify(result), 200
#         else:
#             return jsonify({
#                 "success": False,
#                 "error": {
#                     "code": response.status_code,
#                     "message": "Failed to fetch data from CoinGecko"
#                 }
#             }), response.status_code
#     except requests.RequestException as e:
#         return jsonify({
#             "success": False,
#             "error": {
#                 "code": 500,
#                 "message": str(e)
#             }
#         }), 500
    
@chart_graphs_bp.route('/api/top-movers', methods=['GET'])
def get_crypto_markets():
    vs_currency = request.args.get('vs_currency', 'usd')
    order = request.args.get('order', 'market_cap_desc')
    precision = request.args.get('precision')
    
    result, status_code, error_message = get_top_movers_data(vs_currency, order, precision)
    
    if result:
        return jsonify(result), status_code
    else:
        return jsonify({
            "success": False,
            "error": {
                "code": status_code,
                "message": error_message
            }
        }), status_code
    

# _________________________________ WEBSOCKET ________________________________

@socketio.on('subscribe_to_ohlc_data')
def handle_subscribe_to_ohlc_data(data):
    # New OHLC data subscription logic
    coin = data.get('coin')
    vs_currency = data.get('vs_currency', 'usd')
    interval = data.get('interval', '1h')
    precision = data.get('precision')
    
    ohlc_data, status_code = get_ohlc_coingecko_data(coin, vs_currency, interval, precision)
    if status_code == 200:
        emit('ohlc_data', ohlc_data)
    else:
        emit('error', {'message': 'Failed to fetch OHLC data'})



@socketio.on('subscribe_to_top_movers')
def handle_subscribe_to_top_movers(data):
    vs_currency = data.get('vs_currency', 'usd')
    order = data.get('order', 'market_cap_desc')
    precision = data.get('precision')
    
    result, status_code, error_message = get_top_movers_data(vs_currency, order, precision)
    
    if result:
        emit('top_movers_data', result)
    else:
        emit('top_movers_error', {
            "success": False,
            "error": {
                "code": status_code,
                "message": error_message
            }
        })


