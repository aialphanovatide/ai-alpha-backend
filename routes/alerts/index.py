import re
from sqlalchemy import desc  
from datetime import datetime, timedelta
from flask import jsonify, request, Blueprint
from services.notification.index import Notification
from config import session, Category, Alert, CoinBot, Session
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel
from redis_client.redis_client import cache_with_redis, update_cache_with_redis

tradingview_bp = Blueprint(
    'tradingview_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

LOGS_SLACK_CHANNEL_ID = 'C06FTS38JRX'
notification_service = Notification(session=Session())


@tradingview_bp.route('/alerts/categories', methods=['POST'])  
@cache_with_redis()
def get_alerts_by_categories():
    try:
        # Validate request data
        data = request.json
        if not data or 'categories' not in data:
            return jsonify({'error': 'Categories are required'}), 400
        
        print('data', data)
        
        categories = data.get('categories')
        page = data.get('page')
        per_page = data.get('per_page')
        
        # Validate input parameters
        if not isinstance(categories, list):
            return jsonify({'error': 'Categories must be a list of strings'}), 400
        
        if not categories:
            return jsonify({'error': 'Categories list cannot be empty'}), 400
            
        # Validate pagination parameters if provided
        if (page is not None and page < 1) or (per_page is not None and per_page < 1):
            return jsonify({'error': 'Page and per_page must be positive integers'}), 400

        response = {
            'categories': {},
            'total_alerts': 0
        }

        for category_name in categories:
            category_obj = session.query(Category).filter(Category.name == category_name).first()

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

            # Apply pagination if requested
            if page is not None and per_page is not None:
                alerts_query = alerts_query.offset((page - 1) * per_page).limit(per_page)

            # Get alerts and convert to dict using as_dict method
            alerts = alerts_query.all()
            alerts_list = [alert.as_dict() for alert in alerts]

            # Prepare category response
            category_response = {
                'data': alerts_list,
                'total': total_category_alerts
            }

            # Add pagination info if pagination was used
            if page is not None and per_page is not None:
                total_pages = (total_category_alerts + per_page - 1) // per_page
                category_response['pagination'] = {
                    'current_page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }

            response['categories'][category_name] = category_response

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@tradingview_bp.route('/alerts/coins', methods=['POST'])
@cache_with_redis()
def get_filtered_alerts():
    try:
        # Get and validate request data
        data = request.json
        if not data or 'coins' not in data:
            return jsonify({'error': 'Coins array is required'}), 400

        coins = data.get('coins')
        date = data.get('date')
        page = data.get('page')
        per_page = data.get('per_page')

        # Validate coins parameter
        if not isinstance(coins, list) or not coins:
            return jsonify({'error': 'Coins must be a non-empty array'}), 400

        # Validate date parameter
        valid_date_filters = ["today", "this week", "last week", "4h", "1h", "1w", "1d", "24h"]
        if date and date not in valid_date_filters:
            return jsonify({'error': f'Invalid date parameter. Must be one of: {", ".join(valid_date_filters)}'}), 400

        # Validate pagination parameters if provided
        if (page is not None and page < 1) or (per_page is not None and per_page < 1):
            return jsonify({'error': 'Page and per_page must be positive integers'}), 400

        response = {
            'coins': {},
            'total_alerts': 0
        }

        # Calculate start_date based on date parameter
        start_date = None
        if date:
            now = datetime.now()
            if date in ['today', '1d']:
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date in ['this week', '1w']:
                start_date = now - timedelta(days=now.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date == 'last week':
                start_date = now - timedelta(days=(now.weekday() + 7))
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date == '4h':
                start_date = now - timedelta(hours=4)
            elif date == '1h':
                start_date = now - timedelta(hours=1)
            elif date == '24h':
                start_date = now - timedelta(hours=24)

        for coin_name in coins:
            # Get coin_bot for the current coin
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
            
            # Apply date filter if provided
            if start_date:
                alerts_query = alerts_query.filter(Alert.created_at >= start_date)
            
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
@update_cache_with_redis(related_get_endpoints=['get_filtered_alerts', 'get_alerts_by_categories', 'get_all_alerts'])
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
                print('Data from Tradingview', request.data)
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


                print('timeframe_match', timeframe_match)
                print('timeframe', timeframe)
                print('normalized_timeframe', normalized_timeframe)

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
                # notification_service.push_notification(coin=coin.name, 
                #                                     title=alert_name, 
                #                                     body=message.capitalize(), 
                #                                     type='alert', 
                #                                     timeframe=normalized_timeframe)
 
                
                # send_alert_strategy_to_slack(price=price,
                #                     alert_name=alert_name,
                #                     message=message.capitalize())
                

                return "OK", 200
            
            except Exception as e:
                print('Error receiving Tradingview message', e)
                # send_INFO_message_to_slack_channel(channel_id=LOGS_SLACK_CHANNEL_ID,
                #                                     title_message='Error receiving Tradingview message',
                #                                     sub_title='Reason',
                #                                     message=f"{str(e)} - Data: {str(request.data)}")
                return f'Error receiving Tradingview message', 500
            
    except Exception as e:
        print('Error receiving Tradingview message', e)
        # send_INFO_message_to_slack_channel( channel_id=LOGS_SLACK_CHANNEL_ID,
        #                                     title_message='Error receiving Tradingview message',
        #                                     sub_title='Reason',
        #                                     message=str(e))
        return f'Error receiving Tradingview message: {str(e)}', 500    
        
