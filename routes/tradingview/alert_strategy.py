from dotenv import load_dotenv
from ..trendspider.create_chart import generate_alert_chart
import requests
import os


load_dotenv()

# Product-alerts channel webhook url
SLACK_PRODUCT_ALERTS = os.getenv('SLACK_PRODUCT_ALERTS')

# Token of the Telegram Bot
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Group and channel ID
CHANNEL_ID_AI_ALPHA_FOUNDERS = os.getenv('CHANNEL_ID_AI_ALPHA_FOUNDERS')
CALL_TO_TRADE_TOPIC_ID = os.getenv('CALL_TO_TRADE_TOPIC_ID')

telegram_text_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?parse_mode=HTML'
send_photo_url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto?parse_mode=HTML'


# example incoming string: 3M chart - Price cross and close over Resistance 3
def formatted_alert_name(input_string):

    components = input_string.split(' - ')
    
    time_frame = components[0].casefold()
    alert_message = components[1]

    return time_frame, alert_message


def send_alert_strategy_to_slack(price, alert_name, symbol):

    formatted_symbol = str(symbol).upper()
    time_frame, alert_message = formatted_alert_name(alert_name) 
    formatted_price = str(price)

    new_alert_name = formatted_symbol + " - " + time_frame

    payload = {
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Alert from TradingView*"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*{new_alert_name}*\n\n{alert_message}\n*Last Price:* {formatted_price}"
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
    

def send_alert_strategy_to_telegram(price, alert_name, symbol):

    formatted_symbol = str(symbol).upper()
    time_frame, alert_message = formatted_alert_name(alert_name) 
    formatted_price = str(price)

    new_alert_name = formatted_symbol + " - " + time_frame

    # send_alert_strategy_to_slack(price=price,
    #                             alert_name=alert_name,
    #                             symbol=symbol)


    content = f"""<b>{new_alert_name}</b>\n\n<b>{alert_message}</b>\nLast Price: <b>{formatted_price}</b>\n"""

    symbol = "BINANCE:^" + formatted_symbol # result BINANCE:^BTCUSDT -> return symbol from TS, "BINANCE:^" was added to the result from TV to match the one from TS
  
    chart = generate_alert_chart(symbol, formatted_price)

    files = {
    'photo': ('chart.png', chart, 'image/png')
    }

    # photo_payload = {'chat_id': CHANNEL_ID_AI_ALPHA_FOUNDERS,
    #                 'caption': content,
    #                 'message_thread_id': CALL_TO_TRADE_TOPIC_ID}


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
            return f'Error while sending alert to Telegram {str(response.content)}', 500 
    except Exception as e:
        return f'Error sending message to Telegram. Reason: {e}', 500