import os
import requests
from http import HTTPStatus
from sqlalchemy import desc
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from cachetools.func import ttl_cache
from config import Chart, session, CoinBot, Session
from flask import jsonify, request, Blueprint, jsonify  
from operator import itemgetter


chart_bp = Blueprint('chart', __name__)


# Load environment variables
load_dotenv()

# Get WordPress API key from environment variables
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')
COINGECKO_API_URL = "https://pro-api.coingecko.com/api/v3"



@chart_bp.route('/api/chart/save_chart', methods=['POST'])
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

        print("data from charts", chart_data)

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


@chart_bp.route('/api/coin-support-resistance', methods=['GET'])
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
                response["error"] = f"CoinBot not found for the coin name: {coin_name}"
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
            # Convert datetime objects to ISO format strings
            chart_values['created_at'] = chart_values['created_at'].isoformat() if chart_values['created_at'] else None
            chart_values['updated_at'] = chart_values['updated_at'].isoformat() if chart_values['updated_at'] else None
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
        total3 = calculate_total_3_data()
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


@ttl_cache(maxsize=1, ttl=3600)  # Cache for 1 hour
def calculate_total_3_data():
    """
    Calculate the market cap data for the third largest cryptocurrency.

    This function fetches data from the CoinGecko API for Bitcoin, Ethereum, and the total market,
    then calculates the difference to determine the market cap of the third largest cryptocurrency.

    Returns:
        list: A list of market cap values for the third largest cryptocurrency over 7 days.

    Raises:
        requests.exceptions.RequestException: If there's an error in the API requests.
    """
    base_url = "https://pro-api.coingecko.com/api/v3"
    endpoints = {
        "btc": f"{base_url}/coins/bitcoin/market_chart?vs_currency=usd&days=7&interval=daily",
        "eth": f"{base_url}/coins/ethereum/market_chart?vs_currency=usd&days=7&interval=daily",
        "total": f"{base_url}/global/market_cap_chart?days=7"
    }
    headers = {"x-cg-pro-api-key": COINGECKO_API_KEY}

    responses = {}
    for coin, url in endpoints.items():
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            responses[coin] = response.json()
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Error fetching {coin} data: {str(e)}")

    btc_market_caps = [entry[1] for entry in responses["btc"]["market_caps"]]
    eth_market_caps = [entry[1] for entry in responses["eth"]["market_caps"]]
    total_market_caps = [entry[1] for entry in responses["total"]["market_cap_chart"]["market_cap"]]

    eth_btc_market_caps = [btc + eth for btc, eth in zip(btc_market_caps, eth_market_caps)]
    total3 = [total - eth_btc for total, eth_btc in zip(total_market_caps, eth_btc_market_caps)]

    return total3


