from routes.trendspider.create_chart import generate_alert_chart
from config import session, CoinBot, Alert 
from dotenv import load_dotenv
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


def send_alert_strategy_to_slack(price, alert_name, message):


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
                                    "text": f"*{alert_name}*\n\n{message}\n*Last Price:* ${price}"
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
            print('Alert message from Tradingview sent to Slack successfully')
            return 'Alert message from Tradingview sent to Slack successfully', 200
        else:
            print(f'Error while sending alert message from Tradingview to Slack {response.content}')
            return 'Error while sending alert message from Tradingview to Slack', 500 
    except Exception as e:
        print(f'Error sending message from Tradingview to Slack channel. Reason: {e}')
        return f'Error sending message from Tradingview to Slack channel. Reason: {e}', 500
    

def send_alert_strategy_to_telegram(price, alert_name, message, symbol):

    alert_message = str(message).capitalize()
    formatted_symbol = str(symbol).upper()
    alert_Name = str(alert_name).upper()
    formatted_price = str(price)
  
    # send_alert_strategy_to_slack(price=formatted_price,
    #                             alert_name=alert_Name,
    #                             message=alert_message)



    content = f"""<b>{alert_Name}</b>\n\n{alert_message}\nLast Price: ${formatted_price}\n"""
   

    text_payload = {
            'text': content,
            'chat_id': CHANNEL_ID_AI_ALPHA_FOUNDERS,
            'message_thread_id': CALL_TO_TRADE_TOPIC_ID,
            'protect_content': False,
            }
    
    try:
       
        response = requests.post(telegram_text_url, data=text_payload)

        if response.status_code == 200:
            # with session:
            #     scrapping_data_object = session.query(CoinBot).filter(CoinBot.bot_name == formatted_symbol.casefold()).first()
            #     new_alert = Alert(alert_name=alert_Name,
            #                 alert_message = alert_message,
            #                 symbol=formatted_symbol,
            #                 price=formatted_price
            #                 )

            #     session.add(new_alert)
            #     session.commit()
        
            return 'Alert message sent from Tradingview to Telegram successfully', 200
        else:
            return f'Error while sending message from Tradingview to Telegram {str(response.content)}', 500 
    except Exception as e:
        return f'Error sending message from Tradingview to Telegram. Reason: {e}', 500
    
