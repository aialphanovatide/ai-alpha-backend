import os
import requests
from dotenv import load_dotenv
from config import session, CoinBot, Alert 


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


    try:

        alert_message = str(message).capitalize()
        formatted_symbol = str(symbol).casefold()
        alert_Name = str(alert_name).upper()
        formatted_price = str(price)

        # Remove any dot or point at the end of the price
        if formatted_price.endswith('.') or formatted_price.endswith(','):
            formatted_price = formatted_price[:-1]


        parts = formatted_symbol.split("usdt")
        bot_name = parts[0]
    
        send_alert_strategy_to_slack(price=formatted_price,
                                    alert_name=alert_Name,
                                    message=alert_message)


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
             
                coinBot = session.query(CoinBot).filter(CoinBot.bot_name == bot_name).first()
                coin_bot_id = coinBot.bot_id
                
                new_alert = Alert(alert_name=alert_Name,
                                alert_message = alert_message,
                                symbol=formatted_symbol,
                                price=formatted_price,
                                coin_bot_id=coin_bot_id
                                )

                session.add(new_alert)
                session.commit()
            
                return 'Alert message sent from Tradingview to Telegram successfully', 200
            else:
                return f'Error while sending message from Tradingview to Telegram {str(response.content)}', 500 
        except Exception as e:
            return f'Error sending message from Tradingview to Telegram. Reason: {str(e)}', 500
    except Exception as e:
        return f'An error occured in send_alert_strategy_to_telegram: {str(e)}', 500
    
