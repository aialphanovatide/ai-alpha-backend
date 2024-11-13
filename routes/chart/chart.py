import os
import requests
from sqlalchemy import desc
from http import HTTPStatus
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from config import Chart, CoinBot, Session
from routes.chart.total3 import get_total_3_data
from flask import jsonify, request, Blueprint, jsonify  
from redis_client.redis_client import cache_with_redis
from decorators.measure_time import measure_execution_time
from services.notification.index import Notification

notification_service = Notification(session=Session())


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
        coin_id (int): The ID of the coin.
        pair (str): The trading pair.
        temporality (str): The time frame of the chart.
        coin_name (str): The name of the coin.
        support_1, support_2, support_3, support_4 (float): Support levels.
        resistance_1, resistance_2, resistance_3, resistance_4 (float): Resistance levels.
        is_essential (bool): Flag to determine if notification should be sent.

    Returns:
        dict: A JSON response indicating success or failure.
            Format: {"message": str or None, "error": str or None, "status": int, "data": dict or None}

    Raises:
        SQLAlchemyError: If there's a database-related error.
    """
    response = {
        "message": None,
        "error": None,
        "status": HTTPStatus.OK,
        "data": None
    }

    session = Session()

    try:
        data = request.json
        required_fields = [
            'coin_id', 'pair', 'temporality', 'coin_name',
            'support_1', 'support_2', 'support_3', 'support_4',
            'resistance_1', 'resistance_2', 'resistance_3', 'resistance_4', 'is_essential'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            response["error"] = f"One or more required fields are missing: {', '.join(missing_fields)}"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]

        coin_id = data['coin_id']
        pair = data['pair'].casefold()
        temporality = data['temporality'].casefold()
        coin_name = data['coin_name'].casefold()
        is_essential = data['is_essential']

        if coin_name == 'btc' and pair == 'btc':
            response["error"] = "Invalid coin/pair combination"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]
        
        if coin_name == 'eth' and pair == 'eth':
            response["error"] = "Invalid coin/pair combination"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]
    
        chart_data = {
            'support_1': float(data['support_1']),
            'support_2': float(data['support_2']),
            'support_3': float(data['support_3']),
            'support_4': float(data['support_4']),
            'resistance_1': float(data['resistance_1']),
            'resistance_2': float(data['resistance_2']),
            'resistance_3': float(data['resistance_3']),
            'resistance_4': float(data['resistance_4']),
            'token': coin_name,
            'pair': pair,
            'temporality': temporality,
            'coin_bot_id': coin_id
        }

        new_chart = Chart(**chart_data)
        session.add(new_chart)
        session.commit()
        
        # Query the database to get the coin_bot name
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_id == coin_id).first()
        if not coin_bot:
            raise ValueError(f"No CoinBot found with id {coin_id}")
        session.commit()
        
        coin_symbol = coin_bot.name
        
        # Send notification only if is_essential is True
        if is_essential:
            notification_service.push_notification(
                coin=coin_symbol,
                title=f"{coin_symbol} Support/Resistance Update",  
                body="Check the New Levels!",
                type="s_and_r",
                timeframe=""  
            )
        
        response["message"] = "New chart record created successfully"
        response["status"] = HTTPStatus.CREATED
        response["data"] = new_chart.as_dict()

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

@chart_bp.route('/chart-data', methods=['POST'])
def receive_and_save_chart_data():
    """
    Receives support and resistance data from TradingView, parses it,
    saves it to the database, and sends notifications if required.

    Args:
        The request body should contain a symbol (e.g., BTCUSDT), support and resistance levels,
        timeframe, and a flag indicating if a notification should be sent.

    Returns:
        dict: A JSON response indicating success or failure.
            Format: {"message": str or None, "error": str or None, "status": int, "data": dict or None}
    """
    response = {
        "message": None,
        "error": None,
        "status": HTTPStatus.OK,
        "data": None
    }

    session = Session()

    try:
        # Parse incoming data from TradingView webhook
        data = request.data.decode('utf-8').split('\n')
        
        if len(data) != 11:
            return jsonify({"error": "Incorrect data format"}), HTTPStatus.BAD_REQUEST
        
        # Extract symbol (e.g., BTCUSDT) and clean it
        symbol = data[0].split(': ')[1]
        
        # List of known pairs (you can add more as needed)
        known_pairs = ['USDT', 'USD', 'ETH', 'BTC']
        
        # Determine pair by checking if the symbol ends with any known pair
        pair = next((p for p in known_pairs if symbol.endswith(p)), None)
        if not pair:
            return jsonify({"error": "Invalid trading pair"}), HTTPStatus.BAD_REQUEST
        
        # Extract token by removing the pair from the end of the symbol
        token = symbol[:-len(pair)].lower()  # Everything before the pair is the token
        # Extract timeframe (e.g., '1D', '4H')
        timeframe = data[1].split(': ')[1]  # Extracting 'Timeframe' from second line
        values = {}
        for line in data[2:-1]:  # Skip last line since it's 'Is Essential'
            key, value = line.split(': ')
            values[key] = float(value)

        supports = [values['S1'], values['S2'], values['S3'], values['S4']]
        resistances = [values['R1'], values['R2'], values['R3'], values['R4']]
        # Extract 'Is Essential' flag from last line
        is_essential_str = data[-1].split(': ')[1]
        # Convert 'Is Essential' string to boolean value ('true' -> True, 'false' -> False)
        is_essential = True if is_essential_str.lower() == 'true' else False
        # Query CoinBot to find coin_id using either name or alias
        coin_bot = session.query(CoinBot).filter(
            (CoinBot.name == token) | (CoinBot.alias == token)
        ).first()
        if not coin_bot:
            return jsonify({"error": f"No CoinBot found with name or alias '{token}'"}), HTTPStatus.NOT_FOUND
        coin_id = coin_bot.bot_id
        
        # Delete any existing chart records with this coin_bot_id and matching temporality
        session.query(Chart).filter(Chart.coin_bot_id == coin_id, Chart.temporality == timeframe).delete()
        
        # Prepare chart data for saving to database...

        new_chart_data = {
            'support_1': supports[0],
            'support_2': supports[1],
            'support_3': supports[2],
            'support_4': supports[3],
            'resistance_1': resistances[0],
            'resistance_2': resistances[1],
            'resistance_3': resistances[2],
            'resistance_4': resistances[3],
            'token': token,
            'pair': pair,
            'temporality': timeframe,
            'coin_bot_id': coin_id,
            'is_essential': is_essential   # Store is_essential flag in DB if needed.
        }
        
        new_chart = Chart(**new_chart_data)
        session.add(new_chart)
        
        # Commit changes to the database.
        session.commit()
            
        # Send notification only if is_essential is True.
        if is_essential:
            notification_service.push_notification(
                coin=symbol,
                title=f"{symbol} Support/Resistance Update",
                body="Check the New Levels!",
                type="s_and_r",
                timeframe=timeframe  
            )
        
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

        if not (coin_name or coin_id):
            response["error"] = "Missing required parameter: either coin_name or coin_id must be provided"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]

        if not temporality or not pair:
            response["error"] = "Missing required parameters: temporality and pair must be provided"
            response["status"] = HTTPStatus.BAD_REQUEST
            return jsonify(response), response["status"]

        if coin_name:
            coinbot = session.query(CoinBot).filter(CoinBot.name == coin_name).first()
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
@cache_with_redis(expiration=5)
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
        "status": HTTPStatus.OK,
        "data": None
    }

    try:
        days = int(request.args.get('days', 15))
        total3 = get_total_3_data(days)
        response["data"] = total3
        response["message"] = "Data retrieved sucessfully"
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
@cache_with_redis()
def get_top_movers():
    """
    Retrieve the top movers (gainers and losers) for cryptocurrencies.

    This endpoint fetches cryptocurrency data from the CoinGecko API and returns
    the top 10 gainers and top 10 losers based on the specified ordering criteria.

    Query Parameters:
    - vs_currency (str, optional): The target currency for market data (default: 'usd').
    - order (str, optional): The ordering criteria for the results (default: 'market_cap_desc').
      Valid options: 'market_cap_desc', 'market_cap_asc', 'volume_desc', 'volume_asc',
      'price_change_desc', 'price_change_asc'.
    - precision (int, optional): The number of decimal places for currency values.

    Returns:
    JSON object with the following structure:
    {
        "success": bool,
        "data": {
            "top_10_gainers": list,
            "top_10_losers": list
        },
        "order": str
    }

    On error, returns a JSON object with "success": false and an error message.

    Raises:
    - 400 Bad Request: If an invalid order parameter is provided.
    - 500 Internal Server Error: If there's an issue with the CoinGecko API request
      or any other unexpected error occurs.
    """
    vs_currency = request.args.get('vs_currency', 'usd')
    order = request.args.get('order', 'market_cap_desc')
    precision = request.args.get('precision', type=int)

    valid_orders = ['market_cap_desc', 'market_cap_asc', 'volume_desc', 'volume_asc', 'price_change_desc', 'price_change_asc']
    if order not in valid_orders:
        return jsonify({"success": False, "error": {"code": 400, "message": "Invalid order parameter"}}), 400
    
    with Session() as session:
        try:
            coins_ids = session.query(CoinBot.gecko_id).all()
            ids = ','.join([coin[0] for coin in coins_ids if coin[0]])

            if not ids:
                return jsonify({"success": True, "data": {"top_10_gainers": [], "top_10_losers": []}, "order": order}), 200

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

            # Highlight
            def filter_properties(coin):
                return {
                    "name": coin["name"],
                    "image": coin["image"],
                    "symbol": coin["symbol"],
                    "price_change_percentage_24h": coin["price_change_percentage_24h"],
                    "id": coin["id"],
                    "current_price": coin["current_price"],
                    "last_updated": coin["last_updated"]
                }

            sort_key = {
                'market_cap': lambda x: x.get('market_cap') or 0,
                'volume': lambda x: x.get('total_volume') or 0,
                'price_change': lambda x: x.get('price_change_percentage_24h') or 0
            }.get(order.split('_')[0], lambda x: x.get('market_cap') or 0)

            sorted_data = sorted(data, key=sort_key, reverse=order.endswith('desc'))

            # Highlight
            result = {
                "success": True,
                "data": {
                    "top_10_gainers": [filter_properties(coin) for coin in sorted_data[:10]],
                    "top_10_losers": [filter_properties(coin) for coin in sorted_data[-10:][::-1]]
                },
                "order": order
            }
            return jsonify(result), 200

        except requests.RequestException as e:
            return jsonify({"success": False, "error": {"code": 500, "message": f"API request failed: {str(e)}"}}), 500
        except Exception as e:
            return jsonify({"success": False, "error": {"code": 500, "message": f"An unexpected error occurred: {str(e)}"}}), 500