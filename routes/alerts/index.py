import re
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from flask import jsonify, request, Blueprint
from services.notification.index import Notification
from config import session, Category, Alert, CoinBot, Session
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel
from redis_client.redis_client import cache_with_redis, update_cache_with_redis
from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel

tradingview_bp = Blueprint(
    'tradingview_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

LOGS_SLACK_CHANNEL_ID = 'C06FTS38JRX'
notification_service = Notification(session=Session())


def extract_timeframe(alert_name):
    """
    Extract standardized timeframe from alert name.
    Example: 'BTCUSDT 4H Chart - Bearish' -> '4h'
    
    Returns:
        str: Normalized timeframe ('1h', '4h', '1d', '1w') or None if not found
    """
    timeframe_mapping = {
        '1H': '1h', '4H': '4h', '1D': '1d', '1W': '1w',
        '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w'
    }
    
    if not alert_name:
        return None
        
    match = re.search(r'(\d+[HhDdWw])\s*[Cc]hart', alert_name)
    if match:
        timeframe = match.group(1).upper()
        return timeframe_mapping.get(timeframe)
    return None

@tradingview_bp.route('/alerts/categories', methods=['POST'])  
def get_alerts_by_categories():
    """
    Retrieve alerts for multiple categories with timeframe filtering and pagination support.

    Request Body:
    {
        "categories": ["category1", "category2"],  # Required: List of category names
        "timeframe": "4h",                        # Optional: Timeframe filter (1h, 4h, 1d, 1w)
        "page": 1,                                # Optional: Page number (default: 1)
        "per_page": 10                           # Optional: Items per page (default: 10)
    }

    Returns:
    {
        "categories": {
            "category1": {
                "data": [
                    {
                        "alert_id": int,
                        "alert_name": str,
                        "alert_message": str,
                        "symbol": str,
                        "price": float,
                        "coin_bot_id": int,
                        "created_at": datetime,
                        "updated_at": datetime,
                        "timeframe": str
                    }
                ],
                "total": int,
                "pagination": {
                    "current_page": int,
                    "per_page": int,
                    "total_pages": int,
                    "has_next": bool,
                    "has_prev": bool
                }
            }
        },
        "total_alerts": int
    }

    Error Responses:
        400: Bad Request
            - Categories are required
            - Invalid timeframe parameter
            - Pagination errors
        500: Internal Server Error
    """
    try:

        data = request.json
        if not data or 'categories' not in data:
            return jsonify({'error': 'Categories are required'}), 400

        categories = data.get('categories')
        timeframe = data.get('timeframe')
        
        # Validate timeframe if provided
        valid_timeframes = ['1h', '4h', '1d', '1w']
        if timeframe and timeframe.lower() not in valid_timeframes:
            return jsonify({'error': f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}), 400

        # Pagination validation
        try:
            page = int(data.get('page', 1))
            per_page = int(data.get('per_page', 10))
        except ValueError:
            return jsonify({'error': 'Invalid pagination parameters'}), 400

        if page < 1 or per_page < 1:
            return jsonify({'error': 'Invalid pagination parameters'}), 400

        response = {
            'categories': {},
            'total_alerts': 0
        }

        for category_name in categories:
            print(f"[DEBUG] /alerts/categories - Processing category: {category_name}")
            category_obj = session.query(Category).filter(Category.name == category_name.strip().casefold()).first()

            if not category_obj:
                response['categories'][category_name] = {
                    'error': f"Category {category_name} doesn't exist",
                    'data': [],
                    'total': 0
                }
                continue

            # Build base query
            alerts_query = (session.query(Alert)
                          .join(CoinBot)
                          .filter(CoinBot.category_id == category_obj.category_id))
            
            print(f"[DEBUG] /alerts/categories - Alerts query: {alerts_query}")

            # Apply timeframe filter if provided
            if timeframe:
                alerts_query = alerts_query.filter(
                    func.lower(func.regexp_replace(Alert.alert_name, r'.*(\d+[HhDdWw])\s*[Cc]hart.*', r'\1')) == 
                    timeframe.lower()
                )

            # Order by created_at descending
            alerts_query = alerts_query.order_by(desc(Alert.created_at))

            # Get total count and apply pagination
            total_category_alerts = alerts_query.count()
            response['total_alerts'] += total_category_alerts

            alerts = alerts_query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Convert to dict and add timeframe
            alerts_list = []
            for alert in alerts:
                alert_dict = alert.as_dict()
                alert_dict['timeframe'] = extract_timeframe(alert_dict['alert_name'])
                alerts_list.append(alert_dict)

            category_response = {
                'data': alerts_list,
                'total': total_category_alerts,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': (total_category_alerts + per_page - 1) // per_page,
                    'has_next': page < ((total_category_alerts + per_page - 1) // per_page),
                    'has_prev': page > 1
                }
            }

            response['categories'][category_name] = category_response

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@tradingview_bp.route('/alerts/coins', methods=['POST'])
def get_filtered_alerts():
    """
    Retrieve alerts for multiple coins with timeframe filtering and pagination support.

    Request Body:
    {
        "coins": ["btc", "eth"],               # Required: List of coin symbols
        "timeframe": "4h",                     # Optional: Timeframe filter (1h, 4h, 1d, 1w)
        "page": 1,                             # Optional: Page number (default: 1)
        "per_page": 10                         # Optional: Items per page (default: 10)
    }

    Returns:
    {
        "coins": {
            "btc": {
                "data": [
                    {
                        "alert_id": int,
                        "alert_name": str,
                        "alert_message": str,
                        "symbol": str,
                        "price": float,
                        "coin_bot_id": int,
                        "created_at": datetime,
                        "updated_at": datetime,
                        "timeframe": str
                    }
                ],
                "total": int,
                "pagination": {
                    "current_page": int,
                    "per_page": int,
                    "total_pages": int,
                    "has_next": bool,
                    "has_prev": bool
                }
            }
        },
        "total_alerts": int
    }

    Error Responses:
        400: Bad Request
            - Coins array is required
            - Invalid timeframe parameter
            - Pagination errors
        500: Internal Server Error
    """
    try:
        data = request.json
        if not data or 'coins' not in data:
            return jsonify({'error': 'Coins array is required'}), 400

        coins = data.get('coins')
        timeframe = data.get('timeframe')
        
        # Validate timeframe if provided
        valid_timeframes = ['1h', '4h', '1d', '1w']
        if timeframe and timeframe.lower() not in valid_timeframes:
            return jsonify({'error': f'Invalid timeframe. Must be one of: {", ".join(valid_timeframes)}'}), 400

        # Pagination validation
        try:
            page = int(data.get('page', 1))
            per_page = int(data.get('per_page', 10))
        except ValueError:
            return jsonify({'error': 'Invalid pagination parameters'}), 400

        if page < 1 or per_page < 1:
            return jsonify({'error': 'Invalid pagination parameters'}), 400

        response = {
            'coins': {},
            'total_alerts': 0
        }

        for coin_name in coins:
            print(f"[DEBUG] /alerts/coins - Processing coin: {coin_name}")
            coin_bot = session.query(CoinBot).filter(CoinBot.name == coin_name.casefold().strip()).first()

            if not coin_bot:
                response['coins'][coin_name] = {
                    'error': f'Coin {coin_name} not found',
                    'data': [],
                    'total': 0
                }
                continue

            # Build base query
            alerts_query = session.query(Alert).filter(Alert.coin_bot_id == coin_bot.bot_id)

            # Apply timeframe filter if provided
            if timeframe:
                alerts_query = alerts_query.filter(
                    func.lower(func.regexp_replace(Alert.alert_name, r'.*(\d+[HhDdWw])\s*[Cc]hart.*', r'\1')) == 
                    timeframe.lower()
                )

            # Order by created_at descending
            alerts_query = alerts_query.order_by(desc(Alert.created_at))

            # Get total count and apply pagination
            total_coin_alerts = alerts_query.count()
            response['total_alerts'] += total_coin_alerts

            alerts = alerts_query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Convert to dict and add timeframe
            alerts_list = []
            for alert in alerts:
                alert_dict = alert.as_dict()
                alert_dict['timeframe'] = extract_timeframe(alert_dict['alert_name'])
                alerts_list.append(alert_dict)

            coin_response = {
                'data': alerts_list,
                'total': total_coin_alerts,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': (total_coin_alerts + per_page - 1) // per_page,
                    'has_next': page < ((total_coin_alerts + per_page - 1) // per_page),
                    'has_prev': page > 1
                }
            }

            response['coins'][coin_name] = coin_response

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500








# RESERVED ROUTE - DO NOT USE
# Receives all alert from Tradingview and does three things: Send data to Slack, 
# Store the data in the DB and send the data to Telegram 
@tradingview_bp.route('/api/alert/tv', methods=['GET', 'POST'])
def receive_data_from_tv():
    try:
        if not request.data:
            return 'No data sent in the request', 400
        elif request.is_json:
            send_INFO_message_to_slack_channel( channel_id=LOGS_SLACK_CHANNEL_ID    ,
                                                title_message='Message from Tradingview received as JSON',
                                                sub_title='Invalid request format',
                                                message=str(request.data))
            return 'Invalid request format', 400
        else:
            try:
                data_text = request.data.decode('utf-8')  # Decode the bytes to a string
                data_lines = data_text.split(',')  # Split the text into lines
                
                data_dict = {} 

                for line in data_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        data_dict[key.strip()] = value.strip()

                symbol = data_dict.get('symbol', '').casefold()
                formatted_symbol = ''.join(char for char in symbol if char.isalpha())
                if formatted_symbol.endswith('usdt'):
                    formatted_symbol = formatted_symbol[:-4]
                
                timeframe_match = re.search(r'(\d+[HMD])\s*chart', data_text, re.IGNORECASE)
                normalized_timeframe = None
                if timeframe_match:
                    timeframe = timeframe_match.group(1).upper()
                    timeframe_mapping = {
                    '1M': '1m', '5M': '5m', '15M': '15m', '30M': '30m',
                    '1H': '1h', '2H': '2h', '4H': '4h', '1D': '1d'
                    }
                    normalized_timeframe = timeframe_mapping.get(timeframe, timeframe.lower())

                alert_name = data_dict.get('alert_name', '')  
                message = data_dict.get('message', '')  
                price = data_dict.get('price', data_dict.get('last_price', ''))

                # Get coin_id from coin_name and saves it to the database
                coin = session.query(CoinBot).filter(CoinBot.name == formatted_symbol).first()
                coin_id = coin.bot_id

                # Remove any dot or point at the end of the price
                if price.endswith('.') or price.endswith(','):
                    price = price[:-1]

                new_alert = Alert(alert_name=alert_name,
                                alert_message = message.capitalize(),
                                symbol=formatted_symbol,
                                price=price,
                                coin_bot_id=coin_id
                                )

                session.add(new_alert)
                session.commit()

                # Send to notification to App
                notification_service.push_notification(coin=coin.name, 
                                                    title=alert_name, 
                                                    body=message.capitalize(), 
                                                    type='alert', 
                                                    timeframe=normalized_timeframe)
 
                
                send_notification_to_product_alerts_slack_channel(title_message=alert_name,
                                    sub_title="Alert",
                                    message=f"{message.capitalize()}")
                

                return "OK", 200
            
            except Exception as e:
                print('Error receiving Tradingview message', e)
                send_INFO_message_to_slack_channel(channAlertel_id=LOGS_SLACK_CHANNEL_ID,
                                                    title_message='Error receiving Tradingview message',
                                                    sub_title='Reason',
                                                    message=f"{str(e)} - Data: {str(request.data)}")
                return f'Error receiving Tradingview message', 500
            
    except Exception as e:
        print('Error receiving Tradingview message', e)
        send_INFO_message_to_slack_channel( channel_id=LOGS_SLACK_CHANNEL_ID,
                                            title_message='Error receiving Tradingview message',
                                            sub_title='Reason',
                                            message=str(e))
        return f'Error receiving Tradingview message: {str(e)}', 500    
        

@tradingview_bp.route('/alert', methods=['POST'])
def data_tv():
    """
    Receives alerts from TradingView webhooks in either JSON or plain text format.
    
    TradingView sends webhooks with either:
    - application/json content-type for valid JSON messages
    - text/plain content-type for plain text messages
    
    Expected formats:
    JSON: {
        "symbol": "BTCUSDT",
        "alert_name": "BTCUSDT 4h Chart - Bullish",
        "message": "Price Touch Resistance 4.",
        "price": "45762.77"
    }
    
    Plain text: "symbol: BTCUSDT, alert_name: BTCUSDT 4h Chart - Bullish, message: Price Touch Resistance 4., price: 45762.77"
    """
    try:
        if not request.data:
            return jsonify({'error': 'No data sent in the request'}), 400

        # Initialize data dictionary
        data_dict = {}
        
        # Handle JSON format
        if request.is_json:
            try:
                data_dict = request.get_json()
                log_message = 'Message from Tradingview received as JSON'
            except Exception as e:
                return jsonify({'error': 'Invalid JSON format'}), 400
        # Handle plain text format
        else:
            try:
                data_text = request.data.decode('utf-8')
                # Split by comma and then by colon
                pairs = [pair.strip() for pair in data_text.split(',')]
                for pair in pairs:
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        data_dict[key.strip()] = value.strip()
                log_message = 'Message from Tradingview received as plain text'
            except Exception as e:
                return jsonify({'error': 'Invalid text format'}), 400

        # Log received data
        send_INFO_message_to_slack_channel(
            channel_id=LOGS_SLACK_CHANNEL_ID,
            title_message=log_message,
            sub_title='Data received',
            message=str(data_dict)
        )

        # Extract and validate required fields
        required_fields = ['symbol', 'alert_name', 'message']
        if not all(field in data_dict for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        # Process symbol
        symbol = data_dict.get('symbol', '').casefold()
        formatted_symbol = ''.join(char for char in symbol if char.isalpha())
        if formatted_symbol.endswith('usdt'):
            formatted_symbol = formatted_symbol[:-4]

        # Extract timeframe from alert name
        timeframe_match = re.search(r'(\d+[HMD])\s*chart', data_dict.get('alert_name', ''), re.IGNORECASE)
        normalized_timeframe = None
        if timeframe_match:
            timeframe = timeframe_match.group(1).upper()
            timeframe_mapping = {
                '1M': '1m', '5M': '5m', '15M': '15m', '30M': '30m',
                '1H': '1h', '2H': '2h', '4H': '4h', '1D': '1d'
            }
            normalized_timeframe = timeframe_mapping.get(timeframe, timeframe.lower())

        # Get other fields
        alert_name = data_dict.get('alert_name', '').strip()
        message = data_dict.get('message', '').strip()
        price = data_dict.get('price', data_dict.get('last_price', '')).strip()

        # Clean price
        if isinstance(price, str):
            price = price.rstrip('.,')

        # Validate coin exists
        coin = session.query(CoinBot).filter(CoinBot.name == formatted_symbol).first()
        if not coin:
            return jsonify({'error': f'Coin not found: {formatted_symbol}'}), 404

        # Create new alert
        try:
            new_alert = Alert(
                alert_name=alert_name,
                alert_message=message.capitalize(),
                symbol=formatted_symbol,
                price=float(price),
                coin_bot_id=coin.bot_id
            )
            session.add(new_alert)
            session.commit()
        except Exception as e:
            session.rollback()
            raise Exception(f"Database error: {str(e)}")

        # Send notifications
        try:
            # Send to App
            notification_service.push_notification(
                coin=coin.name,
                title=alert_name,
                body=message.capitalize(),
                type='alert',
                timeframe=normalized_timeframe
            )

            # Send to Slack
            send_notification_to_product_alerts_slack_channel(
                title_message=alert_name,
                sub_title="Alert",
                message=f"{message.capitalize()}"
            )
        except Exception as e:
            # Log notification error but don't fail the request
            send_INFO_message_to_slack_channel(
                channel_id=LOGS_SLACK_CHANNEL_ID,
                title_message='Notification error',
                sub_title='Error',
                message=str(e)
            )

        return jsonify({'message': 'Alert processed successfully'}), 200

    except Exception as e:
        session.rollback()
        error_message = f'Error processing Tradingview alert: {str(e)}'
        print(error_message)
        send_INFO_message_to_slack_channel(
            channel_id=LOGS_SLACK_CHANNEL_ID,
            title_message='Error receiving Tradingview message',
            sub_title='Reason',
            message=f"{error_message} - Data: {str(request.data)}"
        )
        return jsonify({'error': error_message}), 500