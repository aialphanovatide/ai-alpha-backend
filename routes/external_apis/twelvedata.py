import os
import datetime
import requests
from dotenv import load_dotenv
from flask import jsonify, Blueprint, request

twelvedata_bp = Blueprint("twelvedata_bp", __name__)

load_dotenv()

TUELVEDATA_API_KEY = os.getenv("TUELVEDATA_API_KEY")
INTERVAL_VALUES = [
    "1min",
    "5min",
    "15min",
    "30min",
    "45min",
    "1h",
    "2h",
    "4h",
    "1day",
    "1week",
    "1month",
]

@twelvedata_bp.route("/get_symbol_time_series", methods=["GET"])
def get_symbol_time_series():
    """
    Retrieve historical time series data for a specified symbol.

    This endpoint queries the TwelveData API to retrieve historical time series data
    for a given financial symbol, based on the provided interval and output size.

    Args:
        symbol (str): The symbol of the financial instrument (optional, default is 'VIX').
        interval (str): The time interval for the data points, such as '1min', '1h', or '1day' (optional, default is '1h').
        outputsize (int): The maximum number of data points to retrieve (optional, default is 10).

    Returns:
        JSON: A JSON object containing:
            - data (dict): The historical time series data.
            - error (str or None): Error message, if any.
            - success (bool): Indicates if the operation was successful.
        HTTP Status Code

    Raises:
        400 Bad Request: If any provided parameter is invalid.
        404 Not Found: If the symbol is not found.
        500 Internal Server Error: If there's an unexpected error during execution.
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 400

    symbol = request.args.get("symbol", "VIX")
    outputsize = request.args.get("outputsize", 10)
    interval = request.args.get("interval", "1h")

    if interval.lower() not in INTERVAL_VALUES:
        response["error"] = f"Invalid interval format. Permitted values: {INTERVAL_VALUES}"
        return jsonify(response), status_code

    try:
        outputsize = int(outputsize)
        if outputsize < 1:
            raise ValueError
    except ValueError:
        response["error"] = "Invalid outputsize. Must be a positive integer."
        return jsonify(response), status_code

    url = f"https://api.twelvedata.com/time_series?apikey={TUELVEDATA_API_KEY}&symbol={symbol.upper()}&interval={interval.lower()}&outputsize={outputsize}"

    try:
        data = requests.get(url)
        data.raise_for_status()
        data = data.json()

        if "code" in data:
            response["error"] = data.get("message", "Error occurred")
            return jsonify(response), data.get("code", 500)

        response["data"] = data
        response["success"] = True
        status_code = 200

    except requests.exceptions.HTTPError as http_e:
        try:
            error_data = http_e.response.json()
            response["error"] = error_data.get("errorCode", "HTTP error occurred")
            status_code = 401
        except ValueError:
            response["error"] = f"HTTP error occurred: {str(http_e)}"
            status_code = http_e.response.status_code

    except requests.exceptions.RequestException as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code
