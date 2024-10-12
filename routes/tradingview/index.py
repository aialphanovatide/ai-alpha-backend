import re
from sqlalchemy import desc  
from datetime import datetime, timedelta
from flask import jsonify, request, Blueprint
from config import session, Category, Alert, CoinBot, Session
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel
from routes.tradingview.alert_strategy import send_alert_strategy_to_telegram, send_alert_strategy_to_slack
from services.firebase.firebase import send_notification
from redis_client.redis_client import cache_with_redis, update_cache_with_redis
from services.notification.index import Notification

tradingview_bp = Blueprint(
    'tradingview_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

LOGS_SLACK_CHANNEL_ID = 'C06FTS38JRX'
notification_service = Notification(session=Session())

@tradingview_bp.route('/api/tv/alerts', methods=['GET'])  
@cache_with_redis()
def get_all_alerts():
    try:
        category = request.args.get('category')
        limit = request.args.get('limit')

        if not category:
            return 'Category is required', 400
        
        if limit is not None and (not isinstance(int(limit), int) or int(limit) < 0):
            return 'Limit must be a non-negative integer', 400
        
        category_obj = session.query(Category).filter(Category.category == category).first()

        if not category_obj:
            return f"Category {category} doesn't exist", 404

        alerts_list = []

        if category_obj:
            # Get all coin_bot related to this category
            coin_bots = category_obj.coin_bot

            for coin_bot in coin_bots:

                # Order alerts by created_at in descending order
                alerts = session.query(Alert).filter(Alert.coin_bot == coin_bot).order_by(desc(Alert.created_at)).all()
                if limit:
                    alerts = session.query(Alert).filter(Alert.coin_bot == coin_bot).order_by(desc(Alert.created_at)).limit(limit).all()

                for alert in alerts:
                    alert_dict = {
                        'alert_id': alert.alert_id,
                        'alert_name': alert.alert_name,
                        'alert_message': alert.alert_message,
                        'symbol': alert.symbol,
                        'price': alert.price,
                        'coin_bot_id': alert.coin_bot_id,
                        'created_at': alert.created_at.isoformat()  # Convert to ISO format
                    }

                    alerts_list.append(alert_dict)

        return alerts_list, 200
    except Exception as e:
        return f'Error in getting all alerts: {str(e)}', 500
    

# Get alerts from more than one category.
@tradingview_bp.route('/api/tv/multiple_alert', methods=['POST'])  
@cache_with_redis()
def get_alerts_by_categories():
    try:
        data = request.json
        if not data or 'categories' not in data:
            return jsonify({'error': 'Categories are required'}), 400
        
        categories = data.get('categories')
        limit = data.get('limit')

        if not isinstance(categories, list):
            return jsonify({'error': 'Categories must be a list of strings'}), 400

        if limit is not None and (not isinstance(limit, int) or limit < 0):
            return jsonify({'error': 'Limit must be a non-negative integer'}), 400

        result = {}

        for category_name in categories:
            category_obj = session.query(Category).filter(Category.category == category_name).first()

            if not category_obj:
                result[category_name] = f"Category {category_name} doesn't exist"
                continue

            alerts_list = []

            coin_bots = category_obj.coin_bot

            for coin_bot in coin_bots:
                alerts = session.query(Alert).filter(Alert.coin_bot == coin_bot).order_by(desc(Alert.created_at)).all()
                if limit:
                    alerts = session.query(Alert).filter(Alert.coin_bot == coin_bot).order_by(desc(Alert.created_at)).limit(limit).all()
              
                for alert in alerts:
                    alert_dict = {
                        'alert_id': alert.alert_id,
                        'alert_name': alert.alert_name,
                        'alert_message': alert.alert_message,
                        'symbol': alert.symbol,
                        'price': alert.price,
                        'coin_bot_id': alert.coin_bot_id,
                        'created_at': alert.created_at.isoformat()  # Convert to ISO format
                    }

                    alerts_list.append(alert_dict)

            result[category_name] = alerts_list

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# Get alerts of a token (coin) 
@tradingview_bp.route('/api/filter/alerts', methods=['GET', 'POST'])
@cache_with_redis()
def get_filtered_alerts(): 
    try:
        coin = request.args.get('coin')
        date = request.args.get('date')
        limit = request.args.get('limit')

        if not coin or not coin.strip():
            return jsonify({'error': 'Invalid or missing coin parameter'}), 400
        
        if date and date not in ["today", "this week", "last week", "4h", "1h", "1w", "1d", "24h"]:
            return jsonify({'error': 'Invalid date parameter'}), 400
        
        if limit:
            try:
                limit = int(limit)
                if limit <= 0:
                    return jsonify({'error': 'Invalid limit parameter'}), 400
            except ValueError:
                return jsonify({'error': 'Limit parameter must be an integer'}), 400

       
        coin_bot = session.query(CoinBot).filter(CoinBot.name == coin.casefold().strip()).first()

        if not coin_bot:
            return {'message': f'{coin} not found'}, 404
        else:
            coin_bot_id = coin_bot.bot_id
        
            start_date = None
            if date == 'today' or date == '1d':
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            elif date == 'this week' or date == '1w':  
                today = datetime.now()
                start_date = today - timedelta(days=today.weekday())
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date == 'last week':
                today = datetime.now()
                start_date = today - timedelta(days=(today.weekday() + 7))
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date == '4h':
                start_date = datetime.now() - timedelta(hours=4)
            elif date == '1h':
                start_date = datetime.now() - timedelta(hours=1)
            elif date == '24h':
                start_date = datetime.now() - timedelta(hours=24)
            else:
                start_date =  datetime.now()

            alerts = session.query(Alert).filter(Alert.coin_bot_id == coin_bot_id, Alert.created_at >= start_date).order_by(desc(Alert.created_at)).limit(limit).all()
           
            if alerts:
                # Convert alerts to a list of dictionaries
                alerts_list = []

                for alert in alerts:
                    alert_dict = {
                        'alert_id': alert.alert_id,
                        'alert_name': alert.alert_name,
                        'alert_message': alert.alert_message,
                        'symbol': alert.symbol,
                        'price': alert.price,
                        'coin_bot_id': alert.coin_bot_id,
                        'created_at': alert.created_at.isoformat()  # Convert to ISO format
                    }

                    alerts_list.append(alert_dict)

                return {'alerts': alerts_list}, 200
            else:
                return {'message': f'No alerts found for {coin} on {date}'}, 204

    except Exception as e:
        return {'message': f'An error occurred: {str(e)}'}, 500



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
                notification_service.push_notification(coin=coin.name, 
                                                    title=alert_name, 
                                                    body=message.capitalize(), 
                                                    type='alert', 
                                                    timeframe=normalized_timeframe)
 
                
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
        
