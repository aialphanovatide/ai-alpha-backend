import os
import requests
from dotenv import load_dotenv
from flask import jsonify, Blueprint, request

revenuecat_bp = Blueprint("revenuecat_bp", __name__)

load_dotenv()
REVENUECAT_API_KEY = os.getenv("REVENUECAT_API_KEY")

@revenuecat_bp.route("/get_subscribers_info", methods=["GET"])
def get_subscribers_info():
    """
    Retrieve user information from RevenueCat.

    This endpoint queries the RevenueCat API to retrieve subscription and purchase
    information for a specific user, identified by their RevenueCat user ID.

    Args:
        revenuecat_user_id (str): The unique identifier of the RevenueCat user (required).

    Headers:
        Authorization (str): Bearer token for authenticating with the RevenueCat API (required).

    Returns:
        JSON: A JSON object containing:
            - data (dict): The user information from RevenueCat.
            - error (str or None): Error message, if any.
            - success (bool): Indicates if the operation was successful.
        HTTP Status Code

    Raises:
        400 Bad Request: If the RevenueCat user ID is missing or invalid.
        401 Unauthorized: If the API token is invalid.
        500 Internal Server Error: If there's an unexpected error during execution.
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 400
    try:
        revenuecat_user_id = request.args.get("revenuecat_user_id")

        if not revenuecat_user_id:
            response["error"] = "Missing RevenueCat user ID"
            return jsonify(response), status_code

        url = f"https://api.revenuecat.com/v1/subscribers/{revenuecat_user_id}"

        headers = {
            "Accept": "*/*",
            "User-Agent": "news",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {REVENUECAT_API_KEY}"
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
            response["error"] = error_data.get("message")
            status_code = 401
        except ValueError:
            response["error"] = f"HTTP error occurred: {str(http_e)}"
            status_code = http_e.response.status_code

    except requests.exceptions.RequestException as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code