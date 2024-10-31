import re
from sqlalchemy import desc  
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


@tradingview_bp.route('/alerts/categories', methods=['POST'])  
def get_alerts_by_categories():
    """
    Retrieve alerts for multiple categories with pagination support.

    This endpoint allows fetching alerts for one or more categories. The alerts are returned
    in descending order by creation date (newest first) with optional pagination.

    Request Body:
    {
        "categories": ["category1", "category2"],  # Required: List of category names
        "page": 1,                                # Optional: Page number (default: 1)
        "per_page": 10                           # Optional: Items per page (default: 10)
    }

    Error Responses:
        400: Bad Request
            - Categories are required
            - Categories must be a list of strings
            - Categories list cannot be empty
            - Page and per_page must be positive integers
            - Page and per_page must be valid integers
        500: Internal Server Error
            - An error occurred: {error_message}

    Notes:
        - Non-existent categories will return empty data with an error message
        - Pagination is applied per category
        - Results are ordered by created_at in descending order
        - All timestamps are in UTC
    """
    try:
        # Validate request data
        data = request.json
        if not data or 'categories' not in data:
            return jsonify({'error': 'Categories are required'}), 400

        categories = data.get('categories')
        # Convert page and per_page to integers safely
        try:
            page = int(data.get('page', 1))
            per_page = int(data.get('per_page', 10))
        except ValueError:
            return jsonify({'error': 'Page and per_page must be valid integers'}), 400
        
        # Validate input parameters
        if not isinstance(categories, list):
            return jsonify({'error': 'Categories must be a list of strings'}), 400
        
        if not categories:
            return jsonify({'error': 'Categories list cannot be empty'}), 400
            
        # Validate pagination parameters
        if page < 1 or per_page < 1:
            return jsonify({'error': 'Page and per_page must be positive integers'}), 400

        response = {
            'categories': {},
            'total_alerts': 0
        }

        for category_name in categories:
            category_obj = session.query(Category).filter(Category.name == category_name.strip().casefold()).first()

            if not category_obj:
                response['categories'][category_name] = {
                    'error': f"Category {category_name} doesn't exist",
                    'data': [],
                    'total': 0
                }
                continue

            # Build base query for this category
            alerts_query = (session.query(Alert)
                          .join(CoinBot)
                          .filter(CoinBot.category_id == category_obj.category_id)
                          .order_by(desc(Alert.created_at)))

            # Get total count for this category
            total_category_alerts = alerts_query.count()
            response['total_alerts'] += total_category_alerts

            # Calculate pagination values
            total_pages = (total_category_alerts + per_page - 1) // per_page
            offset = (page - 1) * per_page

            # Apply pagination
            alerts = alerts_query.offset(offset).limit(per_page).all()
            alerts_list = [alert.as_dict() for alert in alerts]

            # Prepare category response
            category_response = {
                'data': alerts_list,
                'total': total_category_alerts,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
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
    Retrieve alerts for multiple coins with date filtering and pagination support.

    This endpoint allows fetching alerts for one or more coins with optional date filtering.
    The alerts are returned in descending order by creation date (newest first) with optional pagination.

    Request Body:
    {
        "coins": ["btc", "eth"],               # Required: List of coin symbols
        "date": "today",                       # Optional: Date filter (today, this week, last week)
        "page": 1,                             # Optional: Page number (default: 1)
        "per_page": 10                         # Optional: Items per page (default: 10)
    }

    Date Filter Options:
        - "today": Alerts from start of current day until now
        - "this week": Alerts from start of week until start of today
        - "last week": Alerts from start of last week until start of this week

    Error Responses:
        400: Bad Request
            - Coins array is required
            - Coins must be a non-empty array
            - Invalid date parameter
            - Page and per_page must be positive integers
        500: Internal Server Error
            - An error occurred: {error_message}

    Notes:
        - Non-existent coins will return empty data with an error message
        - Date ranges are calculated in server's timezone
        - Pagination is applied per coin
        - Results are ordered by created_at in descending order
        - All timestamps are in UTC
        - If no date filter is provided, all alerts are returned
        - Week starts on Monday (0) and ends on Sunday (6)
    """

    try:
        # Validate request data
        data = request.json
        if not data or 'coins' not in data:
            return jsonify({'error': 'Coins array is required'}), 400

        coins = data.get('coins')
        date_filter = data.get('date')
        page = data.get('page')
        per_page = data.get('per_page')

        # Validate coins parameter
        if not isinstance(coins, list) or not coins:
            return jsonify({'error': 'Coins must be a non-empty array'}), 400

        # Validate date parameter
        valid_date_filters = ["today", "this week", "last week"]
        if date_filter and date_filter not in valid_date_filters:
            return jsonify({'error': f'Invalid date parameter. Must be one of: {", ".join(valid_date_filters)}'}), 400

        # Validate pagination parameters if provided
        if (page is not None and page < 1) or (per_page is not None and per_page < 1):
            return jsonify({'error': 'Page and per_page must be positive integers'}), 400

        # Calculate date ranges
        now = datetime.now()
        start_date = None
        end_date = None

        if date_filter:
            if date_filter == "today":
                # Start of current day to now
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now

            elif date_filter == "this week":
                # Start of week to start of today (excluding today)
                week_start = now - timedelta(days=now.weekday())
                start_date = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

            elif date_filter == "last week":
                # Start of last week to start of this week
                this_week_start = now - timedelta(days=now.weekday())
                start_date = (this_week_start - timedelta(weeks=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        response = {
            'coins': {},
            'total_alerts': 0,
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None,
                'filter': date_filter
            }
        }

        for coin_name in coins:
            coin_bot = session.query(CoinBot).filter(CoinBot.name == coin_name.casefold().strip()).first()

            if not coin_bot:
                response['coins'][coin_name] = {
                    'error': f'Coin {coin_name} not found',
                    'data': [],
                    'total': 0
                }
                continue

            # Build base query for this coin
            alerts_query = session.query(Alert).filter(Alert.coin_bot_id == coin_bot.bot_id)
            
            # Apply date filters if provided
            if start_date and end_date:
                if date_filter == "today":
                    alerts_query = alerts_query.filter(Alert.created_at >= start_date)
                else:
                    alerts_query = alerts_query.filter(
                        Alert.created_at >= start_date,
                        Alert.created_at < end_date
                    )
            
            # Order by created_at descending
            alerts_query = alerts_query.order_by(desc(Alert.created_at))

            # Get total count for this coin
            total_coin_alerts = alerts_query.count()
            response['total_alerts'] += total_coin_alerts

            # Apply pagination if requested
            if page is not None and per_page is not None:
                alerts_query = alerts_query.offset((page - 1) * per_page).limit(per_page)

            # Get alerts and convert to dict using as_dict method
            alerts = alerts_query.all()
            alerts_list = [alert.as_dict() for alert in alerts]

            # Prepare coin response
            coin_response = {
                'data': alerts_list,
                'total': total_coin_alerts
            }

            # Add pagination info if pagination was used
            if page is not None and per_page is not None:
                total_pages = (total_coin_alerts + per_page - 1) // per_page
                coin_response['pagination'] = {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
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
        
