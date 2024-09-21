import os
import re
import requests
from dotenv import load_dotenv
from flask import jsonify, Blueprint, request
from utils.general import validate_headers, validate_max, validate_resolution

capitalcom_bp = Blueprint("capitalcom_bp", __name__)

load_dotenv()
X_CAP_API_KEY = os.getenv("X_CAP_API_KEY")
REQUIRED_HEADERS = ["X_SECURITY_TOKEN", "CST"]
email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

@capitalcom_bp.route("/capitalcom/historical/prices", methods=["GET"])
def get_symbol_prices():
    """
    Retrieve historical prices for a specific symbol.

    This endpoint queries the Capital.com API to retrieve historical price data
    for a given financial instrument, based on the provided symbol and resolution.

    Args:
        symbol (str): The symbol of the financial instrument (required).
        resolution (str): The time resolution for the price data, such as 'MINUTE', 'HOUR', or 'DAY' (optional, default is 'HOUR').
        max (int): The maximum number of data points to retrieve, between 1 and 1000 (optional).

    Headers:
        X-SECURITY-TOKEN (str): The security token for authentication (required).
        CST (str): The session token for authentication (required).

    Returns:
        JSON: A JSON object containing:
            - data (dict): The historical price data.
            - error (str or None): Error message, if any.
            - success (bool): Indicates if the operation was successful.
        HTTP Status Code

    Raises:
        400 Bad Request: If any provided parameter is invalid.
        401 Unauthorized: If the session or security token is invalid.
        500 Internal Server Error: If there's an unexpected error during execution.
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 400
    try:
        headers = request.headers
        validate_headers(headers, REQUIRED_HEADERS)
        symbol = request.args.get("symbol")

        if not symbol:
            response["error"] = "Missing Symbol param."
            return jsonify(response), status_code

        resolution = validate_resolution(request.args.get("resolution"))
        validate_max(request.args.get("max"))

        url = f"https://api-capital.backend-capital.com/api/v1/prices/{symbol.upper()}?resolution={resolution.upper()}"
        print(url)

        if max_value := request.args.get("max"):
            url += f"&max={max_value}"

        headers = {
            "Accept": "*/*",
            "User-Agent": "news",
            "Content-Type": "application/json",
            "X-SECURITY-TOKEN": headers.get("X_SECURITY_TOKEN"),
            "CST": headers.get("CST"),
        }

        data = requests.get(url, headers=headers)
        data.raise_for_status()
        data = data.json()

        response["data"] = data
        response["success"] = True
        status_code = 200

    except ValueError as ve:
        response["error"] = str(ve)
        return jsonify(response), status_code

    except requests.exceptions.HTTPError as http_e:
        try:
            error_data = http_e.response.json()
            response["error"] = error_data.get("errorCode")
            status_code = 401
        except ValueError:
            response["error"] = f"HTTP error occurred: {str(http_e)}"
            status_code = http_e.response.status_code

    except requests.exceptions.RequestException as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code


@capitalcom_bp.route("/capitalcom-session", methods=["POST"])
def post_capitalcom_session():
    """
    Creates a session with the CapitalCom API.

    This endpoint sends a POST request to the CapitalCom API to create a session using the provided
    email (identifier) and password.

    Request JSON:
        {
            "identifier": str,  # The email address of the user (required)
            "password": str     # The password of the user (required)
        }

    Response JSON:
        {
            "data": dict or None,  # The response data from CapitalCom API if successful
            "error": str or None,  # Error message if the request failed
            "success": bool        # Indicates if the operation was successful
        }

    Returns:
        - 200 OK: If the session is created successfully.
        - 400 Bad Request: If the identifier or password is missing or invalid.
        - 401 Unauthorized: If the credentials are invalid.
        - 500 Internal Server Error: If there's an unexpected error during execution.

    Raises:
        requests.exceptions.RequestException: If there's an issue with the request to the CapitalCom API.
    """

    response = {"data": None, "error": None, "success": False}
    status_code = 400

    if request.json is not None:
        identifier = request.json.get("identifier")
        password = request.json.get("password")

    if identifier is None or identifier == "":
        response["error"] = "Identifier field can't be null"
        return jsonify(response), status_code
    if re.match(email_regex, identifier) is None:
        response["error"] = "Identifier field has to be an email address"
        return jsonify(response), status_code
    if password is None or password == "":
        response["error"] = "Password field can't be null"
        return jsonify(response), status_code

    url = "https://api-capital.backend-capital.com/api/v1/session"

    payload = {
        "identifier": identifier,
        "password": password,
    }

    headers = {
        "Accept": "*/*",
        "User-Agent": "news",
        "Content-Type": "application/json",
        "X-CAP-API-KEY": X_CAP_API_KEY,
    }

    try:
        data = requests.post(url, json=payload, headers=headers)
        data.raise_for_status()
        response_data = data.json()

        response["data"] = response_data
        response["success"] = True
        response["X-SECURITY-TOKEN"] = data.headers.get("X-SECURITY-TOKEN")
        response["CST"] = data.headers.get("CST")
        status_code = 200

    except requests.exceptions.HTTPError as http_e:
        response["error"] = f"HTTP error occurred: {http_e.response.text}"
        status_code = http_e.response.status_code

    except requests.exceptions.RequestException as e:
        if "401" in str(e):
            response["error"] = "Invalid credentials"
            status_code = 401
        else:
            response["error"] = f"An unexpected error occurred: {str(e)}"
            status_code = 500

    return jsonify(response), status_code
