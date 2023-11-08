#from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel
from .alert_strategy import send_alert_strategy_to_slack, send_alert_strategy_to_telegram
from flask import request, Blueprint

tradingview_notification_bp = Blueprint(
    'tradingview_notification_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@tradingview_notification_bp.route('/api/alert/tv', methods=['GET', 'POST'])
def receive_data_from_tv():
    try:
        if request.is_json:
            print('request.data AS JSON', request.data)
            # ##send_notification_to_product_alerts_slack_channel(title_message='Message from Tradingview received as JSON',
            #                                                   sub_title='Invalid request format',
            #                                                   message=str(request.data))
            return 'Invalid request format', 400
        else:
            try:
                print('request.data', request.data)
                # data_text = request.data.decode('utf-8')  # Decode the bytes to a string
                # data_lines = data_text.split('\n')  # Split the text into lines
                # data_dict = {} 

                # for line in data_lines:
                #     if ':' in line:
                #         key, value = line.split(':', 1)
                #         data_dict[key.strip()] = value.strip()

                # price_value = data_dict.get('price', '')  
                # alert_name_value = data_dict.get('alert name', '') 
                # meaning_value = data_dict.get('meaning', '')  
                # exchange = data_dict.get('exchange', '')

                # response, status = send_alert_strategy_to_slack(price=price_value, # Delete after send_alert_strategy_to_telegram works
                #                             alert_name=alert_name_value, # Delete after send_alert_strategy_to_telegram works
                #                             meaning=meaning_value) # Delete after send_alert_strategy_to_telegram works
                
                # send_alert_strategy_to_telegram(exchange=exchange,
                #                                 price=price_value,
                #                                 alert_name=alert_name_value,
                #                                 meaning=meaning_value
                #                                 )

                return 'ok', 200
            
            except Exception as e:
                print(f'Error sending message to Slack channel. Reason: {e}')
                # ##send_notification_to_product_alerts_slack_channel(title_message='Message from Tradingview failed',
                #                                               sub_title='Reason',
                #                                               message=str(e))
                return f'Error sending message to Slack channel. Reason: {e}', 500
    except Exception as e:
        print(f'Error main thread. Reason: {e}')
        return 'Error', 500    
        
