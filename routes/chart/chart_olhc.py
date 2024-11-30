import os
import time
import requests
from typing import Optional
from dotenv import load_dotenv
from flask import render_template
from services.chart.candlestick import ChartWidget, ChartSettings
from flask import request, jsonify, Blueprint, current_app
from redis_client.redis_client import cache_with_redis

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
    if current_app.debug:
        print(f"[DEBUG] Binance API - Input parameters:")
        print(f"[DEBUG] Symbol: {symbol}")
        print(f"[DEBUG] VS Currency: {vs_currency}")
        print(f"[DEBUG] Interval: {interval}")
        print(f"[DEBUG] Precision: {precision}")
        print(f"[DEBUG] BINANCE_API_URL: {BINANCE_API_URL}")

    pair = f"{symbol.upper().strip()}{vs_currency.upper().strip()}T"
    endpoint = f"{BINANCE_API_URL}/v3/klines"

    params = {
        'symbol': pair,
        'interval': interval.casefold(),
        'limit': 180
    }

    if current_app.debug:
        print(f"[DEBUG] Binance API - Request details:")
        print(f"[DEBUG] Endpoint: {endpoint}")
        print(f"[DEBUG] Params: {params}")

    try:
        response = requests.get(endpoint, params=params)
        if current_app.debug:
            print(f"[DEBUG] Binance API - Response status: {response.status_code}")
            print(f"[DEBUG] Binance API - Response headers: {dict(response.headers)}")
            print(f"[DEBUG] Binance API - Response content preview: {response.text[:200]}...")

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
            if current_app.debug:
                print(f"[DEBUG] Binance API - Successfully processed {len(ohlc_data)} candles")
            return ohlc_data, 200
        
        if current_app.debug:
            print("[DEBUG] Binance API - No data returned")
        return None, 404

    except requests.exceptions.RequestException as e:
        if current_app.debug:
            print(f"[DEBUG] Binance API - Request failed: {str(e)}")
        return None, 500

def get_ohlc_coingecko_data(gecko_id: str, vs_currency: str, interval: str, precision: Optional[int] = None):
    """
    Fetch OHLC data from CoinGecko for a specific coin using its Gecko ID and specified time interval.
    """
    if current_app.debug:
        print(f"[DEBUG] CoinGecko API - Input parameters:")
        print(f"[DEBUG] Gecko ID: {gecko_id}")
        print(f"[DEBUG] VS Currency: {vs_currency}")
        print(f"[DEBUG] Interval: {interval}")
        print(f"[DEBUG] Precision: {precision}")
        print(f"[DEBUG] COINGECKO_API_URL: {COINGECKO_API_URL}")

    try:
        endpoint = f"{COINGECKO_API_URL}/coins/{gecko_id}/ohlc"
        days = 180 if interval == '1w' else 30
        params = {
            'vs_currency': vs_currency,
            'days': days,
        }
        if precision:
            params['precision'] = int(precision)

        if current_app.debug:
            print(f"[DEBUG] CoinGecko API - Request details:")
            print(f"[DEBUG] Endpoint: {endpoint}")
            print(f"[DEBUG] Params: {params}")
            print(f"[DEBUG] Headers: {HEADERS}")

        response = requests.get(endpoint, params=params, headers=HEADERS)
        
        if current_app.debug:
            print(f"[DEBUG] CoinGecko API - Response status: {response.status_code}")
            print(f"[DEBUG] CoinGecko API - Response headers: {dict(response.headers)}")
            print(f"[DEBUG] CoinGecko API - Response content preview: {response.text[:200]}...")

        response.raise_for_status()
        raw_data = response.json()
        
        if not raw_data:
            if current_app.debug:
                print("[DEBUG] CoinGecko API - No data returned")
            return None, 404
        
        if current_app.debug:
            print(f"[DEBUG] CoinGecko API - Successfully retrieved {len(raw_data)} data points")
        return raw_data, 200

    except requests.exceptions.HTTPError as http_err:
        if current_app.debug:
            print(f"[DEBUG] CoinGecko API - HTTP error: {str(http_err)}")
        return None, response.status_code
    except requests.exceptions.RequestException as req_err:
        if current_app.debug:
            print(f"[DEBUG] CoinGecko API - Request failed: {str(req_err)}")
        return None, 500

@chart_graphs_bp.route('/chart/ohlc', methods=['GET'])
@cache_with_redis(expiration=2)
def ohlc_chart():
    if current_app.debug:
        print("[DEBUG] /chart/ohlc endpoint called")
        print(f"[DEBUG] Request args: {request.args}")
        print(f"[DEBUG] Request headers: {dict(request.headers)}")

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

        if current_app.debug:
            print("[DEBUG] Processed parameters:")
            print(f"[DEBUG] gecko_id: {gecko_id}")
            print(f"[DEBUG] vs_currency: {vs_currency}")
            print(f"[DEBUG] interval: {interval}")
            print(f"[DEBUG] precision: {precision}")
            print(f"[DEBUG] symbol: {symbol}")

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
        
        # Try Binance first
        data, status = get_ohlc_binance_data(symbol, vs_currency, interval, precision)
        if data:
            if current_app.debug:
                print("[DEBUG] Successfully retrieved data from Binance")
            response['data'] = data
            end_time = time.time()
            if current_app.debug:
                print(f"[DEBUG] Total request time: {end_time - start_time:.2f} seconds")
            return jsonify(response), status

        # Fallback to CoinGecko
        if current_app.debug:
            print("[DEBUG] Binance data not available, falling back to CoinGecko")
        
        data, status_code = get_ohlc_coingecko_data(gecko_id, vs_currency, interval, precision)
        end_time = time.time()
        
        if current_app.debug:
            print(f"[DEBUG] Total request time: {end_time - start_time:.2f} seconds")
            print(f"[DEBUG] Final status code: {status_code}")
        
        response['data'] = data
        return jsonify(response), status_code
    
    except Exception as e:
        if current_app.debug:
            print(f"[DEBUG] Unexpected error: {str(e)}")
        response['error'] = str(e)
        return jsonify(response), 500


@chart_graphs_bp.route('/chart/widget', methods=['GET'])
def chart_widget():
    try:
        # Retrieve query parameters
        symbol = request.args.get('symbol', 'BTCUSDT')
        interval = request.args.get('interval', '1h')
        n_bars = request.args.get('n_bars', 50, type=int)

        # Create a ChartWidget instance with the new parameters
        chart_widget = ChartWidget(config=ChartSettings(interval=interval, symbol=symbol, num_candles=n_bars))
        
        # Get the script and div components
        script, div = chart_widget.get_chart_components()
        
        # Render the template with the chart components
        return render_template('chart.html', script=script, div=div)
    except Exception as e:
        return str(e), 500
