import os
import requests
from flask import Blueprint
from dotenv import load_dotenv
from flask import request, jsonify

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')

telegram_bp = Blueprint(
    'telegram_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

set_telegram_webhook = f'https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://star-oyster-known.ngrok-free.app&drop_pending_updates=True'
get_webhook_info = f'https://api.telegram.org/bot6185446761:AAGXE98znTx0dEKkRdoA-Zxum2VPOXTSHhI/getWebhookInfo'
delete_webhook = f'https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True'
send_message_url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?parse_mode=HTML'
send_photo_url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto?parse_mode=HTML'
send_video_url = f'https://api.telegram.org/bot{TOKEN}/sendVideo'


# Route to received messages from Telegram
@telegram_bp.route('/', methods=['POST']) 
async def webhook():
    update = request.json

    if not update:
        return jsonify({"status": "error", "message": "Invalid update format."}), 400

    if 'message' not in update:
        return jsonify({'status': 'update received'})

    message = update['message']
    if 'text' not in message:
        return jsonify({'status': 'update received'})
    
    if message['chat']['type'] != 'private':
        return jsonify({'status': 'message from a group received'})
   
    chat_id = message['chat']['id']
    user_message = message.get('text', '').strip().lower()

    if user_message == '/start':
        text = "Hello, This is Alpha, an AI Bot that can help you with any question you may have about Cryptocurrencies!"
    else:
        text = "Hello, this is AI Alpha. Please stay tuned for updates as we continue to develop and launch our bot. Thank you for your interest!"
        # text = aialpha(user_message)
  
    text_payload = {'chat_id': chat_id, 'text': text}
    res = requests.post(send_message_url, data=text_payload)
      
    if res.status_code == 200:
        print('Message to Telegram sent successfully')
        return jsonify({"status": "success"}), 200
    else:
        print('Failed to send message to Telegram')
        return jsonify({"status": 500, "message": "Failed to send message to Telegram"}), 500



