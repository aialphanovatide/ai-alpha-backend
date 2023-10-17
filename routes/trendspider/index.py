from dotenv import load_dotenv
from flask import request, Blueprint
from routes.trendspider.alert_startegy import send_alert_strategy_message_to_telegram
from routes.trendspider.signal_strategy import send_signal_strategy_to_telegram
from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel

load_dotenv()

trendspider_notification_bp = Blueprint(
    'trendspider_notification_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


def get_data_from_trendspider_to_telegram(data):
    type = data["type"]

    if type == "signal":
        response, status = send_signal_strategy_to_telegram(data)
        return response, status
    else:
        response, status = send_alert_strategy_message_to_telegram(data)
        return response, status

@trendspider_notification_bp.route('/webhook', methods=['GET', 'POST'])
def receive_data():
        data_length = len(request.data)
        print('request.data of Trenspider >', request.data)
        if data_length > 0:
            if request.is_json:
                try:
                    json_data = request.get_json()
                    
                    result, status = get_data_from_trendspider_to_telegram(json_data)
            
                    if status == 200:
                        return result, 200
                    else:
                        send_notification_to_product_alerts_slack_channel(title_message='Message from Trendspider failed', sub_title='Reason', message=str(result))
                        return result, 500

                    
                except Exception as e:
                    send_notification_to_product_alerts_slack_channel(title_message='Message from Trendspider failed', sub_title='Reason', message=str(e))
                    return 'Signal from Trendspider failed: ' + str(e), 400

            else:
                send_notification_to_product_alerts_slack_channel(title_message='Message from Trendspider failed', sub_title='Reason', message='Malformed body message, please check last notifcation on Trendspider')
                return "Data received as text/plain", 400
        else:
            send_notification_to_product_alerts_slack_channel(title_message='Message from Trendspider', sub_title='Info', message='Notification from Trendpider empty')
            return "Notification from Trendpider empty", 400


        
