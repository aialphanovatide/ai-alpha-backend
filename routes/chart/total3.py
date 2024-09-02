from http import HTTPStatus
from flask import jsonify
import requests
from sqlalchemy import Interval
import os
import requests
from http import HTTPStatus
from sqlalchemy import Interval
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from tvDatafeed import TvDatafeed, Interval



load_dotenv()

TW_USER = os.getenv('TW_USER')
TW_PASS = os.getenv('TW_PASS')


chart_bp = Blueprint('chart', __name__)

def get_total_3_data():
    username = TW_USER
    password = TW_PASS

    tv = TvDatafeed(username, password)

    symbol = 'CRYPTOCAP:TOTAL3'
    exchange = 'CRYPTOCAP'
    interval = Interval.in_daily
    days = 15

    data = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=days, fut_contract=None, extended_session=False)

    data = data.iloc[::-1]

    results = []

    for i, (index, row) in enumerate(data.iterrows(), start=1):
        package = {
            'date': index.strftime('%Y-%m-%d'),  # Date format YYYY-MM-DD
            'open': round(row['open'], 2),
            'high': round(row['high'], 2),
            'low': round(row['low'], 2),
            'close': round(row['close'], 2)
        }
        results.append(package)
    
    return results


@chart_bp.route('/api/total_3_data', methods=['GET'])
def get_total_3_data():
    """
    Retrieve and calculate total market cap data for the top 3 cryptocurrencies.

    This endpoint fetches market cap data for Bitcoin, Ethereum, and the total market,
    then calculates the market cap for the third largest cryptocurrency by subtracting
    Bitcoin and Ethereum from the total.

    Returns:
        dict: A JSON response containing either the calculated data or an error message.
            Format: {"message": list or None, "error": str or None, "status": int}

    Raises:
        requests.exceptions.RequestException: If there's an error in the API requests.
        SQLAlchemyError: If there's a database-related error.
    """
    response = {
        "message": None,
        "error": None,
        "status": 200
    }

    try:
        total3 = get_total_3_data()
        response["message"] = total3
    except requests.exceptions.RequestException as e:
        response["error"] = f"API request failed: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    except SQLAlchemyError as e:
        response["error"] = "Database error occurred"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify(response), response["status"]



get_total_3_data()