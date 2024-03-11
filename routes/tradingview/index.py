from sqlalchemy import desc  
from flask import jsonify, request, Blueprint
from datetime import datetime, timedelta
from config import session, Category, Alert, CoinBot
from .alert_strategy import send_alert_strategy_to_telegram
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel


tradingview_bp = Blueprint(
    'tradingview_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

# Gets all alerts of a catgerory - desc
@tradingview_bp.route('/api/tv/alerts', methods=['GET'])  
def get_all_alerts():
    try:
        category = request.args.get('category')

        if not category:
            return 'Category is required', 400
        
        category_obj = session.query(Category).filter(Category.category == category).first()

        alerts_list = []

        if not category_obj:
            return f"Category {category} doesn't exist", 404

        if category_obj:
            # gets all coin_bot related to this category
            coin_bots = category_obj.coin_bot

            for coin_bot in coin_bots:
                # Order alerts by created_at in descending order
                alerts = session.query(Alert).filter(Alert.coin_bot == coin_bot).order_by(desc(Alert.created_at)).all()
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
    
#get alerts from more than one category especified by categories.
@tradingview_bp.route('/api/tv/multiple_alerts', methods=['POST'])  
def get_alerts_by_categories():
    try:
        data = request.json
        if not data or 'categories' not in data:
            return jsonify({'error': 'Categories are required in JSON format'}), 400
        
        categories = data['categories']

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

# Get alerts by coin - desc
@tradingview_bp.route('/api/filter/alerts', methods=['GET', 'POST'])
def get_filtered_alerts(): 
    try:
        coin = request.args.get('coin')
        date = request.args.get('date')

        if not coin or not date:
            return {'message': "Coin and date are required"}, 400

        if date not in ["today", "this week", "last week"]: 
            return {'message': "Date not valid"}, 400
        else:
            coin_bot = session.query(CoinBot).filter(CoinBot.bot_name == coin.casefold().strip()).first()

            if not coin_bot:
                return {'message': f'{coin} not found'}, 404
            else:
                coin_bot_id = coin_bot.bot_id

                # Determine the date range based on the provided option
                if date == 'today':
                    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                elif date == 'this week':
                    today = datetime.now()
                    start_date = today - timedelta(days=today.weekday())
                    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                elif date == 'last week':
                    today = datetime.now()
                    start_date = today - timedelta(days=(today.weekday() + 7))
                    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    start_date = None

                # Filter alerts based on date range
                if start_date:
                    alerts = session.query(Alert).filter(Alert.coin_bot_id == coin_bot_id, Alert.created_at >= start_date).order_by(desc(Alert.created_at)).all()
                else:
                    alerts = session.query(Alert).filter(Alert.coin_bot_id == coin_bot_id).order_by(desc(Alert.created_at)).all()

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
        
