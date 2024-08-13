import os
import requests
from flask import jsonify, Blueprint, request
from utils.external_apis_values import BINANCE_INTERVAL_VALUES, BINANCE_SYMBOL_VALUES
from utils.general import parse_timestamp

binance_bp = Blueprint("binance_bp", __name__)

def parse_response(klines_list):
    parsed_response = []
    for kline in klines_list:
        parsed_kline = {
            "kline_open_time": parse_timestamp(kline[0]),
            "open_price": kline[1],
            "high_price": kline[2],
            "low_price": kline[3],
            "close_price": kline[4],
            "volume": kline[5],
            "kline_close_time": parse_timestamp(kline[6]),
            "quote_asset_volume": kline[7],
            "number_of_trades": kline[8],
            "taker_buy_base_asset_volume": kline[9],
            "taker_buy_quote_asset_volume": kline[10],
        }

        parsed_response.append(parsed_kline)
    return parsed_response
        
@binance_bp.route("/get_symbol_klines", methods=["GET"])
def get_symbol_klines():
    """
    Retrieve Kline/Candlestick Data for a Specified Symbol.

    This endpoint allows users to fetch Kline/Candlestick data for a given trading pair symbol from Binance API.
    The user must provide a valid symbol (e.g., 'BTCUSDT') and can optionally specify a time interval.

    Args:
        symbol (str): The trading pair symbol (required).
        interval (str): The time interval for the Klines, default is '1h' (optional).

    Returns:
        JSON: A JSON response containing Kline data, or an error message if the request fails.

    Responses:
        200: Successfully retrieved Kline data.
        400: Invalid symbol or missing required parameters.
        500: Internal server error.
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 400

    symbol = request.args.get("symbol")
    interval = request.args.get("interval", "1h")

    if symbol is None:
        response["error"] = "Symbol param is required."
        return jsonify(response), status_code

    if symbol.upper() not in BINANCE_SYMBOL_VALUES:
        response["error"] = "Invalid symbol."
        return jsonify(response), status_code

    if interval.lower() not in BINANCE_INTERVAL_VALUES:
        response["error"] = f"Invalid interval. Permitted values are: {BINANCE_INTERVAL_VALUES}"
        return jsonify(response), status_code

    url = f"https://api3.binance.com/api/v3/klines?interval={interval.lower()}&symbol={symbol.upper()}"

    try:
        data = requests.get(url)
        data.raise_for_status()
        data = data.json()
        data = parse_response(data)

        response["data"] = data
        response["success"] = True
        status_code = 200

    except requests.exceptions.HTTPError as http_e:
        try:
            error_data = http_e.response.json()
            response["error"] = error_data.get("errorCode", "Internal Server Error")
            status_code = 500
        except ValueError:
            response["error"] = f"HTTP error occurred: {str(http_e)}"
            status_code = http_e.response.status_code

    except requests.exceptions.RequestException as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code
