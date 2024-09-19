from http import HTTPStatus
from sqlalchemy import desc
import requests
import os
from dotenv import load_dotenv
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from config import Chart, CoinBot, Session
from routes.chart.total3 import get_total_3_data
from flask import jsonify, request, Blueprint, jsonify  
from routes.chart.total3 import get_total_3_data


load_dotenv()

TW_USER = os.getenv('TW_USER')
TW_PASS = os.getenv('TW_PASS')

chart_bp = Blueprint('chart', __name__)

# Load environment variables from the .env file
load_dotenv()

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_API_URL = 'https://pro-api.coingecko.com/api/v3'

HEADERS = {
            "Content-Type": "application/json",
            "x-cg-pro-api-key": COINGECKO_API_KEY,
        }


@chart_bp.route('/chart', methods=['POST'])
def save_chart():
    """
    Adds a new support and resistance lines record for a coin.

    This endpoint creates a new chart entry for a specified coin, pair, and temporality,
    regardless of whether a previous entry exists.

    Args (JSON):
        coin_bot_id (int): The ID of the coin bot.
        pair (str): The trading pair.
        temporality (str): The time frame of the chart.
        token (str): The token symbol.
        support_1, support_2, support_3, support_4 (float): Support levels.
        resistance_1, resistance_2, resistance_3, resistance_4 (float): Resistance levels.

    Returns:
        dict: A JSON response indicating success or failure.
            Format: {"message": str or None, "error": str or None, "status": int}

    Raises:
        SQLAlchemyError: If there's a database-related error.
    """
    response = {
        "message": None,
        "error": None,
        "status": HTTPStatus.OK
    }

    session = Session()

    try:
        data = request.json
        required_fields = ['coin_bot_id', 'pair', 'temporality', 'token']
        
        if not all(field in data for field in required_fields):
            response["error"] = "One or more required fields are missing"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]

        coin_bot_id = data['coin_bot_id']
        pair = data['pair'].casefold()
        temporality = data['temporality'].casefold()
        token = data['token'].casefold()

        print("data", data)

        if token == 'btc' and pair == 'btc':
            response["error"] = "Invalid coin/pair combination"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]
        
       

        chart_data = {
            'support_1': float(data.get('support_1')),
            'support_2': float(data.get('support_2')),
            'support_3': float(data.get('support_3')),
            'support_4': float(data.get('support_4')),
            'resistance_1': float(data.get('resistance_1')),
            'resistance_2': float(data.get('resistance_2')),
            'resistance_3': float(data.get('resistance_3')),
            'resistance_4': float(data.get('resistance_4')),
            'token': token,
            'pair': pair,
            'temporality': temporality,
            'coin_bot_id': coin_bot_id
        }

        

        new_chart = Chart(**chart_data)
        session.add(new_chart)
        session.commit()

        response["message"] = "New chart record created successfully"
        response["status"] = HTTPStatus.CREATED

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

    return jsonify(response), response["status"]


@chart_bp.route('/chart', methods=['GET'])
def get_chart_values():
    """
    Get the most recent support and resistance lines of a requested coin.

    This endpoint retrieves the most recent chart values including support and resistance levels
    for a specified coin (by name or ID), temporality, and trading pair.

    Args:
        coin_name (str, optional): The name of the coin.
        coin_id (int, optional): The ID of the coin.
        temporality (str): The time frame of the chart.
        pair (str): The trading pair.

    Returns:
        dict: A JSON response containing either the chart values or an error message.
            Format: {"message": dict or None, "error": str or None, "status": int}

    Raises:
        SQLAlchemyError: If there's a database-related error.
    """
    response = {
        "message": None,
        "error": None,
        "status": HTTPStatus.OK
    }

    session = Session()

    try:
        coin_name = request.args.get('coin_name')
        coin_id = request.args.get('coin_id')
        temporality = request.args.get('temporality')
        pair = request.args.get('pair')
        
        if not (coin_name or coin_id) or not temporality or not pair:
            response["error"] = "Missing required parameters"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]

        if coin_name:
            coinbot = session.query(CoinBot).filter(CoinBot.bot_name == coin_name).first()
            if not coinbot:
                response["error"] = f"Coin not found with name: {coin_name}"
                response["status"] = HTTPStatus.NOT_FOUND
                return jsonify(response), response["status"]
            coin_id = coinbot.bot_id

        # Query for the most recent chart entry based on updated_at
        chart = session.query(Chart).filter_by(
            coin_bot_id=coin_id, 
            temporality=temporality.casefold(), 
            pair=pair.casefold()
        ).order_by(desc(Chart.updated_at)).first()

        if chart:
            chart_values = chart.as_dict()
            response["message"] = chart_values
        else:
            response["error"] = "No chart found for the given parameters"
            response["status"] = HTTPStatus.NOT_FOUND

    except SQLAlchemyError as e:
        session.rollback()
        response["error"] = f"Database error: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        session.rollback()
        response["error"] = f"An unexpected error occurred: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        session.close()

    return jsonify(response), response["status"]


@chart_bp.route('/chart/total3', methods=['GET'])
def get_total_3_data_route():
    """
    Retrieve and calculate total market cap data for the top 3 cryptocurrencies.

    This endpoint fetches market cap data for the top 3 cryptocurrencies.

    Query Parameters:
        days (int): Number of days of data to fetch. Defaults to 15.

    Returns:
        dict: A JSON response containing either the calculated data or an error message.
            Format: {"message": list or None, "error": str or None, "status": int}
    """
    response = {
        "message": None,
        "error": None,
        "status": HTTPStatus.OK
    }

    try:
        days = int(request.args.get('days', 15))
        total3 = get_total_3_data(days)
        response["message"] = total3
    except ValueError:
        response["error"] = "Invalid 'days' parameter. It must be an integer."
        response["status"] = HTTPStatus.BAD_REQUEST
    except RuntimeError as e:
        response["error"] = str(e)
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        response["error"] = f"An unexpected error occurred: {str(e)}"
        response["status"] = HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify(response), response["status"]


@chart_bp.route('/chart/top-movers', methods=['GET'])
def get_top_movers():
    vs_currency = request.args.get('vs_currency', 'usd')
    order = request.args.get('order', 'market_cap_desc')
    precision = request.args.get('precision', type=int)

    valid_orders = ['market_cap_desc', 'market_cap_asc', 'volume_desc', 'volume_asc', 'price_change_desc', 'price_change_asc']
    if order not in valid_orders:
        return jsonify({"success": False, "error": {"code": 400, "message": "Invalid order parameter"}}), 400

    try:
        crypto_data = []
        # Fetch data from CoinGecko API
        ids = ",".join(crypto["coingecko_id"] for crypto in crypto_data)
        params = {
            'vs_currency': vs_currency,
            'ids': ids,
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h'
        }
        if precision is not None:
            params['precision'] = precision

        response = requests.get(f'{COINGECKO_API_URL}/coins/markets', params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Sort data based on the order parameter
        if order.startswith('market_cap'):
            key = lambda x: x['market_cap'] or 0
        elif order.startswith('volume'):
            key = lambda x: x['total_volume'] or 0
        elif order.startswith('price_change'):
            key = lambda x: x['price_change_percentage_24h'] or 0
        else:
            raise ValueError(f"Unsupported order: {order}")

        sorted_data = sorted(data, key=key, reverse=order.endswith('desc'))

        # Get top 10 and bottom 10
        top_10 = sorted_data[:10]
        bottom_10 = sorted_data[-10:][::-1]

        result = {
            "success": True,
            "data": {
                "top_10_gainers": top_10,
                "top_10_losers": bottom_10
            },
            "order": order
        }
        return jsonify(result), 200

    except requests.RequestException as e:
        return jsonify({"success": False, "error": {"code": 500, "message": f"API request failed: {str(e)}"}}), 500
    except ValueError as e:
        return jsonify({"success": False, "error": {"code": 400, "message": str(e)}}), 400
    except Exception as e:
        return jsonify({"success": False, "error": {"code": 500, "message": f"An unexpected error occurred: {str(e)}"}}), 500