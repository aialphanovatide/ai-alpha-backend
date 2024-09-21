import os
import requests
from dotenv import load_dotenv
from flask import jsonify, Blueprint, request
from utils.general import validate_date, validate_int_list

coindar_bp = Blueprint("coindar_bp", __name__)

load_dotenv()

COINDAR_API_KEY = os.getenv("COINDAR_API_KEY")

@coindar_bp.route("/crypto-events", methods=["GET"])
def get_crypto_events():
    """
    Retrieve cryptocurrency events based on specified filters.

    This endpoint queries the Coindar API to retrieve events related to cryptocurrencies,
    filtered by date range, coin IDs, tags, and sorting options.

    Args:
        today_date (str): The lower limit of the event start date in the format yyyy-mm-dd (optional)
        end_date (str): The upper date limit of the event start date in the format yyyy-mm-dd (optional)
        filter_coins (str): Comma-separated list of cryptocurrency IDs related to the requested events (optional)
        sort_by (str): Parameter defining events sorting; possible values are 'date_start', 'date_added', or 'views' (optional)
        filter_tags (str): Comma-separated list of tag IDs (optional)
        order_by (str): Sorting order; possible values are '0' (ascending) or '1' (descending) (optional)

    Returns:
        JSON: A JSON object containing:
            - data (list): List of event objects
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        400 Bad Request: If any provided parameter is invalid
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {"data": None, "error": None, "success": False}
    status_code = 400

    today_date = request.args.get("today_date")
    end_date = request.args.get("end_date")
    filter_coins = request.args.get("filter_coins")
    sort_by = request.args.get("sort_by")
    filter_tags = request.args.get("filter_tags")
    order_by = request.args.get("order_by")

    if today_date and not validate_date(today_date):
        response["error"] = "Invalid today_date format. Expected yyyy-mm-dd."
        return jsonify(response), status_code

    if end_date and not validate_date(end_date):
        response["error"] = "Invalid end_date format. Expected yyyy-mm-dd."
        return jsonify(response), status_code

    if filter_coins and not validate_int_list(filter_coins):
        response["error"] = (
            "Invalid filter_coins format. Expected comma-separated integers."
        )
        return jsonify(response), status_code

    if sort_by and sort_by not in ["date_start", "date_added", "views"]:
        response["error"] = (
            "Invalid sort_by value. Expected 'date_start', 'date_added', or 'views'."
        )
        return jsonify(response), status_code

    if filter_tags and not validate_int_list(filter_tags):
        response["error"] = (
            "Invalid filter_tags format. Expected comma-separated integers."
        )
        return jsonify(response), status_code

    if order_by and order_by not in ["0", "1"]:
        response["error"] = "Invalid order_by value. Expected '0' or '1'."
        return jsonify(response), status_code

    url = f"https://coindar.org/api/v2/events?access_token={COINDAR_API_KEY}&page=1&page_size=100"

    if today_date is not None:
        url += f"&filter_date_start={today_date}"
    if end_date is not None:
        url += f"&filter_date_end={end_date}"
    if filter_coins is not None:
        url += f"&filter_coins={filter_coins}"
    if sort_by is not None:
        url += f"&sort_by={sort_by}"
    if filter_tags is not None:
        url += f"&filter_tags={filter_tags}"
    if order_by is not None:
        url += f"&order_by={order_by}"

    try:
        data = requests.get(url)
        data.raise_for_status()
        data = data.json()

        response["data"] = data
        response["success"] = True
        status_code = 200

    except requests.exceptions.RequestException as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code
