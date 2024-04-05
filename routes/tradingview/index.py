from sqlalchemy import desc  
from websocket.socket import socketio
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from flask import jsonify, request, Blueprint
from config import session, Category, Alert, CoinBot
from .alert_strategy import send_alert_strategy_to_telegram
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel


tradingview_bp = Blueprint(
    'tradingview_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

new_alert = Alert(alert_name='test',
                        alert_message = 'test',
                        symbol='btc',
                        price=234,
                        coin_bot_id=1
                        )

session.add(new_alert)
session.commit()

# Test route for emitting data through a websocket
@tradingview_bp.route('/emit')
def index():
    data = request.data.decode('utf-8')
    socketio.emit('new_alert', {'message': data})
    return 'message sent', 200

# Gets all alerts of a catgerory
@tradingview_bp.route('/api/tv/alerts', methods=['GET'])  
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

       
        coin_bot = session.query(CoinBot).filter(CoinBot.bot_name == coin.casefold().strip()).first()

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
def receive_data_from_tv():
    try:
        if not request.data:
            return 'No data sent in the request', 400
        elif request.is_json:
            print('Message from Tradingview received as JSON', request.data)
            send_INFO_message_to_slack_channel( channel_id="C06FTS38JRX",
                                                title_message='Message from Tradingview received as JSON',
                                                sub_title='Invalid request format',
                                                message=str(request.data))
            return 'Invalid request format', 400
        else:
            try:
                print('Data from Tradingview', request.data)
                data_text = request.data.decode('utf-8')  # Decode the bytes to a string
                data_lines = data_text.split(',')  # Split the text into lines
                
                # Emits the alert data to the client
                socketio.emit('new_alert', {'message': data_text})
                
                data_dict = {} 

                for line in data_lines:
                     if ':' in line:
                         key, value = line.split(':', 1)
                         data_dict[key.strip()] = value.strip()

                alert_name = data_dict.get('alert_name', '') 
                symbol = data_dict.get('symbol', '') 
                message = data_dict.get('message', '')  
                price = data_dict.get('price', data_dict.get('last_price', ''))
                
                response, status = send_alert_strategy_to_telegram(price=price,
                                                 alert_name=alert_name,
                                                 message=message,
                                                 symbol=symbol,
                                                 )
                
                if status != 200:
                     send_INFO_message_to_slack_channel( channel_id="C06FTS38JRX",
                                                         title_message='Error seding Tradingview Alert',
                                                         sub_title='Reason',
                                                         message=f"{str(response)} - Data: {str(request.data)}")


                return response, status
            
            except Exception as e:
                print(f'Error sending message to Slack channel. Reason: {e}')
                send_INFO_message_to_slack_channel( channel_id="C06FTS38JRX",
                                                    title_message='Error receiving Tradingview message',
                                                    sub_title='Reason',
                                                    message=f"{str(e)} - Data: {str(request.data)}")
                return f'Error sending message to Slack channel. Reason: {e}', 500
            
    except Exception as e:
        print(f'Error receiving Tradingview message: {str(e)}')
        session.rollback()
        return f'Error receiving Tradingview message: {str(e)}', 500    
        
