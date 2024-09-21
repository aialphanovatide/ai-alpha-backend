import os
import requests
from dotenv import load_dotenv
from flask import jsonify, Blueprint, request
from utils.external_apis_values import COINALYZE_SYMBOL_VALUES

coinalyze_bp = Blueprint("coinalyze_bp", __name__)

load_dotenv()

COINALYZE_API_KEY = os.getenv("COINALYZE_API_KEY")

@coinalyze_bp.route("/funding-rates", methods=["GET"])
def get_funding_rates():
    """
    Retrieve funding rates for specified symbols.

    This endpoint queries the Coinalyze API to retrieve the funding rates for specified financial symbols.
    The user can provide a list of symbols to retrieve their corresponding funding rates.

    Args:
        symbols (str): Comma-separated list of symbols for which to retrieve funding rates (required).
                      Valid values include 'BTCUSD_PERP.3', 'BTCUSD_PERP.A', 'BTCUSD.6', etc.

    Returns:
        JSON: A JSON object containing:
            - data (dict): The funding rates data.
            - error (str or None): Error message, if any.
            - success (bool): Indicates if the operation was successful.
        HTTP Status Code

    Raises:
        400 Bad Request: If the symbols parameter is missing or contains invalid values.
        404 Not Found: If the provided symbols are not found.
        500 Internal Server Error: If there's an unexpected error during execution.
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 400

    symbols = request.args.get("symbols")

    if symbols is None:
        response["error"] = "At least one symbol ID is required."
        return jsonify(response), status_code

    symbols_list = symbols.split(",")
    for symbol in symbols_list:
        if symbol.upper() not in COINALYZE_SYMBOL_VALUES:
            response["error"] = f"One or more symbols are invalid. Permitted values: {COINALYZE_SYMBOL_VALUES}"
            status_code = 404
            return jsonify(response), status_code

    url = f"https://api.coinalyze.net/v1/funding-rate?api_key={COINALYZE_API_KEY}&symbols={symbols.upper()}"

    try:
        data = requests.get(url)
        data.raise_for_status()
        data = data.json()

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
