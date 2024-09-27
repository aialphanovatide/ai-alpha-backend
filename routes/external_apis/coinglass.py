import os
from dotenv import load_dotenv
import requests
from flask import Flask, jsonify, Blueprint

# Load environment variables from .env file
load_dotenv()

coinglass_bp = Blueprint('coinglass', __name__)

@coinglass_bp.route("/coinglass/bitcoin-etfs", methods=["GET"])
def get_bitcoin_etfs():
    """
    Retrieve Bitcoin ETF data from CoinGlass API.

    This endpoint queries the CoinGlass API to retrieve data about Bitcoin ETFs.

    Returns:
        JSON: A JSON object containing:
            - data (dict): The Bitcoin ETF data.
            - error (str or None): Error message, if any.
            - success (bool): Indicates if the operation was successful.
        HTTP Status Code

    Raises:
        500 Internal Server Error: If there's an unexpected error during execution.
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 500

    try:
        # Get the API key from environment variables
        api_key = os.getenv("COINGLASS_API_KEY")

        if not api_key:
            response["error"] = "API key not found in environment variables."
            return jsonify(response), status_code

        url = "https://open-api.coinglass.com/public/v2/bitcoin_etf_all"
        
        headers = {
            "accept": "application/json",
            "coinglassSecret": api_key
        }

        data = requests.get(url, headers=headers)
        data.raise_for_status()
        data = data.json()

        response["data"] = data
        response["success"] = True
        status_code = 200

    except requests.exceptions.HTTPError as http_e:
        try:
            error_data = http_e.response.json()
            response["error"] = error_data.get("message", str(http_e))
            status_code = http_e.response.status_code
        except ValueError:
            response["error"] = f"HTTP error occurred: {str(http_e)}"

    except requests.exceptions.RequestException as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"

    return jsonify(response), status_code

# Create Flask app and register blueprint
app = Flask(__name__)
app.register_blueprint(coinglass_bp)

if __name__ == '__main__':
    app.run(debug=True)