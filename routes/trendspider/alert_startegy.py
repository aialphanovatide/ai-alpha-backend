import os
import requests
from dotenv import load_dotenv
from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel

load_dotenv()

# Product-alerts channel webhook url
SLACK_PRODUCT_ALERTS = os.getenv('SLACK_PRODUCT_ALERTS')

# Token of the Telegram Bot
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Group and channel ID
CHANNEL_ID_AI_ALPHA_FOUNDERS = os.getenv('CHANNEL_ID_AI_ALPHA_FOUNDERS')
CALL_TO_TRADE_TOPIC_ID = os.getenv('CALL_TO_TRADE_TOPIC_ID')

telegram_text_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?parse_mode=HTML'

def send_alert_strategy_message_to_slack(data):

    strategy_name = data['bot_name']  
    symbol = data['symbol']
    last_price = data["last_price"] 
    type = data["type"] 
    status = data["status"] 

    formatted_strategy_name = str(strategy_name).upper()
    formatted_symbol = str(symbol).upper()
    formatted_last_price = str(last_price)
    formatted_status = str(status).capitalize()
    formatted_type_of_alert = str(type).capitalize()

    payload = { 
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Alert strategy*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Strategy:*\n{formatted_strategy_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Symbol:*\n{formatted_symbol}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Type:*\n{formatted_type_of_alert}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:*\n{formatted_status}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Last Price:*\n${formatted_last_price}"
                        }
                    ]
                },
                {
                "type": "divider"
                },
                {
                "type": "divider"
                }
            ]
        }
    
    try:
        response = requests.post(SLACK_PRODUCT_ALERTS, json=payload)
        if response.status_code == 200:
            print('Alert message sent to Slack successfully')
            return 'Alert message sent to Slack successfully', 200
        else:
            print(f'Error while sending alert message to Slack {response.content}')
            return 'Error while sending alert message to Slack', 500 
    except Exception as e:
        print(f'Error sending message to Slack channel. Reason: {e}')
        return f'Error sending message to Slack channel. Reason: {e}', 500
    

def send_alert_strategy_to_telegram(data):

    send_alert_strategy_message_to_slack(data=data)

    strategy_name = data['bot_name']  
    symbol = data['symbol']
    last_price = data["last_price"] 
    status = data["status"] 

    formatted_strategy_name = str(strategy_name).upper()
    formatted_symbol = str(symbol).upper()
    formatted_last_price = str(last_price)
    formatted_status = str(status).capitalize()

    content = f"""<b>Alert Strategy - {formatted_symbol}</b>\n\nStrategy: {formatted_strategy_name}\nStatus: <b>{formatted_status}</b>\nLast Price: <b>${formatted_last_price}</b>\n\n"""

    text_payload = {
            'text': content,
            'chat_id': CHANNEL_ID_AI_ALPHA_FOUNDERS,
            'message_thread_id': CALL_TO_TRADE_TOPIC_ID,
            'protect_content': False,
            }
    try:
        response = requests.post(telegram_text_url, data=text_payload)

        if response.status_code == 200:
            return 'Alert message sent to Telegram successfully', 200
        else:
            send_notification_to_product_alerts_slack_channel(title_message='Error while sending Alert to Telegram', sub_title='Reason', message=f'{str(response.content)}')
            return 'Error while sending alert to Telegram', 500 
    except Exception as e:
        send_notification_to_product_alerts_slack_channel(title_message='Error while sending Alert to Telegram', sub_title='Reason', message=f'{str(e)}')
        return f'Error sending message to Telegram. Reason: {e}', 500