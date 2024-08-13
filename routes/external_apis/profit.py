import os
import requests
from dotenv import load_dotenv
from flask import jsonify, Blueprint, request
from utils.general import validate_date
from utils.external_apis_values import PROFIT_ISO_CURRENCIES

profit_bp = Blueprint("profit_bp", __name__)

load_dotenv()

PROFIT_COM_API_KEY = os.getenv("PROFIT_COM_API_KEY")

@profit_bp.route("/get_economic_events", methods=["GET"])
def get_economic_events():
    """
    Retrieve economic events based on specified filters.

    This endpoint queries the Profit API to retrieve economic events related to
    forex, filtered by date range, country ISO, currency, and impact.

    Args:
        country_iso (str): The country ISO code ('US', 'GB' or 'CN') (optional)
        impact (str): Comma-separated list of impact levels ('high', 'medium', 'low') (optional)
        date (str): The lower limit of the event start date in the format yyyy-mm-dd (optional)
        end_date (str): The upper limit of the event end date in the format yyyy-mm-dd (optional)

    Returns:
        JSON: A JSON object containing:
            - url (str): The URL of the API request
            - data (list): List of event objects
            - error (str or None): Error message, if any
            - success (bool): Indicates if the operation was successful
        HTTP Status Code

    Raises:
        400 Bad Request: If any provided parameter is invalid
        500 Internal Server Error: If there's an unexpected error during execution
    """
    response = {"url": None, "data": None, "error": None, "success": False}
    status_code = 400

    country_iso = request.args.get("country_iso")
    impact = request.args.get("impact")
    date = request.args.get("date")
    end_date = request.args.get("end_date")

    # Validations
    if date and not validate_date(date):
        response["error"] = "Invalid date format. Expected yyyy-mm-dd."
        return jsonify(response), status_code

    if end_date and not validate_date(end_date):
        response["error"] = "Invalid end_date format. Expected yyyy-mm-dd."
        return jsonify(response), status_code

    if country_iso:
        country_iso = country_iso.upper()
        if country_iso not in PROFIT_ISO_CURRENCIES:
            response["error"] = ("Invalid country_iso value. Expected 'US', 'GB' or 'CN'.")
            return jsonify(response), status_code

    if impact:
        impact_list = [item.strip() for item in impact.split(",")]
        valid_impacts = {"high", "medium", "low"}
        if not all(i in valid_impacts for i in impact_list):
            response["error"] = ("Invalid impact values. Expected 'high', 'medium', 'low'.")
            return jsonify(response), status_code

    url = f"https://api.profit.com/data-api/economic_calendar/forex?token={PROFIT_COM_API_KEY}"

    if country_iso:
        url += f"&country_iso={country_iso}"
    if date:
        url += f"&start_date={date}"
    if end_date:
        url += f"&end_date={end_date}"
    if impact:
        for i in impact_list:
            url += f"&impact={i}"

    try:
        data = requests.get(url)
        data.raise_for_status()
        response_data = data.json()

        response["data"] = response_data
        response["success"] = True
        response["url"] = url
        status_code = 200

    except requests.exceptions.HTTPError as http_e:
        response["error"] = f"HTTP error occurred: {http_e.response.text}"
        status_code = http_e.response.status_code

    except requests.exceptions.RequestException as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        status_code = 500

    return jsonify(response), status_code
