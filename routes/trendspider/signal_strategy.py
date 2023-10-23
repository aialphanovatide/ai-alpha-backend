import os
import re
import gspread
import requests
from difflib import SequenceMatcher
from routes.trendspider.create_chart import generate_signal_chart
from routes.trendspider.formulas import add_0_25, formulas_long, formulas_short

# Product-alerts channel webhook url
SLACK_PRODUCT_ALERTS = os.getenv('SLACK_PRODUCT_ALERTS')

# Token of the Telegram Bot
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Group ID of AI Alpha Lite
CHANNEL_ID_AI_ALPHA_LITE = os.getenv('CHANNEL_ID_AI_ALPHA_LITE')

# Group and channels IDs of AI Alpha Founders 
CHANNEL_ID_AI_ALPHA_FOUNDERS = os.getenv('CHANNEL_ID_AI_ALPHA_FOUNDERS')
BITCOIN_TOPIC_ID = os.getenv('BITCOIN_TOPIC_ID')
ETHEREUM_TOPIC_ID = os.getenv('ETHEREUM_TOPIC_ID')
CALL_TO_TRADE_TOPIC_ID = os.getenv('CALL_TO_TRADE_TOPIC_ID')

send_message_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?parse_mode=HTML'
send_photo_url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto?parse_mode=HTML'

def send_signal_strategy_to_slack(data, accuracy, position, formatted_entry_range):

    strategy_name = data['bot_name']  
    type = data["type"] 

    formatted_strategy_name = str(strategy_name).upper()
    formatted_type_of_signal = str(type).capitalize()

    if starts_with_test(strategy_name):
        text = 'Signal sent to Test channel on Telegram successfully:'
    else:
        text = 'Signal sent to Telegram successfully:'

    payload = {
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*{text}*"
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
                                    "text": f"*Accuracy:*\n{accuracy}%"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Type:*\n{formatted_type_of_signal}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Position:*\n{position}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Entry Range:*\n{formatted_entry_range}"
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



def send_signal_strategy_to_telegram(data):

    

    strategy_name = data['bot_name']  
    symbol = data['symbol']
    last_price = data["last_price"] 

    entry_range = add_0_25(last_price) # adds a 0.25% to the last_price
    try:
        sa = gspread.service_account('service_account.json')
        main_sheet = sa.open_by_url("https://docs.google.com/spreadsheets/d/10PToRlfsE6BExc8UCba5dxg062YWIYH6ZtZgVDlfciM/edit#gid=884504876")
        wks = main_sheet.worksheet('Summary of Swing Trading strategies')
        all_stretegies = wks.col_values(1) 
    except Exception as e:
        print('An error occured' + str(e))
        return 'An error occured' + str(e)
  
    # First look for the strategy that is equal to the incoming strategy from Trendspider
    best_match_of_all_strategies = max(all_stretegies, key=lambda strategy: SequenceMatcher(None, strategy_name, strategy).ratio())
    if best_match_of_all_strategies == strategy_name:
    
        row_data = None # Store the data of the found strategy
        for row in wks.get_all_values():
            if row[0].startswith(best_match_of_all_strategies):
                row_data = row
                break
        
        accuracy = row_data[15]
        position = row_data[14] # BTC - LONG / BTC - SHORT....

        if int(accuracy) >= 50:

            wks_best_match = main_sheet.worksheet(position)
            porcentages = wks_best_match.col_values(1)
            risk_return_ratios = wks_best_match.col_values(5)

            closest_match = max(porcentages, key=lambda strategy: SequenceMatcher(None, accuracy, strategy).ratio())
            index = porcentages.index(closest_match)
            index_for_r_r_r = index + 1

            all_tp1 = wks_best_match.col_values(6)
            all_tp2 = wks_best_match.col_values(7)
            all_tp3 = wks_best_match.col_values(8)
            all_tp4 = wks_best_match.col_values(9)
            all_sl1 = wks_best_match.col_values(10)
            all_sl2 = wks_best_match.col_values(11)

            r_r_r = risk_return_ratios[index_for_r_r_r]
            tp1 = all_tp1[index]
            tp2 = all_tp2[index]
            tp3 = all_tp3[index]
            tp4 = all_tp4[index]
            sl1 = all_sl1[index]
            sl2 = all_sl2[index]

            symbol = symbol.split(':')[1].replace('^', '').strip()
            symbol_with_usdt = symbol[:3] + '/' + symbol[3:]
            position = position.split('-')[1].strip().upper() # Long or Short

            chart = generate_signal_chart(symbol, last_price)

            files = {
            'photo': ('chart.png', chart, 'image/png')
            }

            if position == 'LONG':
                results = formulas_long(accuracy, entry_range, r_r_r, tp1, tp2, tp3, tp4, sl1, sl2)
                if results:
                    TP_1 = results[0]
                    TP_2 = results[1]
                    TP_3 = results[2]
                    TP_4 = results[3]
                    stop_loss_1 = results[4] 
                    stop_loss_2 = results[5]
                else: 
                    return 'Formula failed', 500

            else:
                
                results = formulas_short(accuracy, entry_range, r_r_r, tp1, tp2, tp3, tp4, sl1, sl2)
                
                if results:
                    TP_1 = results[0]
                    TP_2 = results[1]
                    TP_3 = results[2]
                    TP_4 = results[3]
                    stop_loss_1 = results[4] 
                    stop_loss_2 = results[5]
                else:
                    return 'Formula failed', 500
                
            if starts_with_test(strategy_name):
                topic_id = 108
            elif symbol == 'BTCUSDT':
                topic_id = BITCOIN_TOPIC_ID
            elif symbol == 'ETHUSDT':
                topic_id = ETHEREUM_TOPIC_ID
            else:
                topic_id = CALL_TO_TRADE_TOPIC_ID

           
            if starts_with_test(strategy_name):
                group_id = -1001869959989
            else:
                group_id = CHANNEL_ID_AI_ALPHA_FOUNDERS

            last_price = float(last_price)
            result = last_price * 1.0025
            formatted_entry_range = f'{result:,.2f}'

            strategy_text = f"""<b>Breakout Strategy - {symbol_with_usdt.upper()}</b>\nStrategy: Breakout Entry for {symbol_with_usdt.upper()}\nSignal Accuracy: <b>{accuracy}%</b>\n\nHello! AI Alpha's algorithm has identified a trigger to enter a potential trading position for {symbol_with_usdt.upper()}.\n\nAccording to our <b>breakout</b> strategy, we recommend entering a <b>{position}</b> position for {symbol_with_usdt.upper()} <b>Potential entry point ${formatted_entry_range}.</b>\n\nTake Profit Target 1: ${TP_1} \nTake Profit Target 2: ${TP_2}\nTake Profit Target 3: ${TP_3}\nTake Profit Target 4: ${TP_4}\nRecommended Stop Loss 1: ${stop_loss_1}\nRecommended Stop Loss 2: ${stop_loss_2}\n\nAI Alpha https://aialpha.ai/"""
            photo_payload = {'chat_id': group_id, 'caption': strategy_text, 'message_thread_id': topic_id}

            send_signal_strategy_to_slack(data=data,
                                          accuracy=accuracy,
                                          position=position,
                                          formatted_entry_range=formatted_entry_range,
                                          )
            
            response = requests.post(send_photo_url, data=photo_payload, files=files)

            if response.status_code == 200:
                return 'Signal sent to Telegram successfully', 200
            else:
                return 'Error while sending signal to Telegram', 400
        else: 
            return 'Accuracy too low', 400
    else:
        return 'Strategy not found on the Signals Spreadhsheet', 400
    

def starts_with_test(strategy_name):
    pattern = re.compile(r'^test', re.IGNORECASE)

    if pattern.match(strategy_name):
        return True
    else:
        return False
