import os
import requests
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from typing import Dict, Any
from http import HTTPStatus

# Load environment variables
load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')
NGROK_URL = os.getenv('NGROK_URL')

telegram_bp = Blueprint(
    'telegram_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

# Telegram API URLs
SET_WEBHOOK_URL = f'https://api.telegram.org/bot{TOKEN}/setWebhook?url={NGROK_URL}&drop_pending_updates=True'
GET_WEBHOOK_INFO_URL = f'https://api.telegram.org/bot{TOKEN}/getWebhookInfo'
DELETE_WEBHOOK_URL = f'https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=True'
SEND_MESSAGE_URL = f'https://api.telegram.org/bot{TOKEN}/sendMessage?parse_mode=HTML'
SEND_PHOTO_URL = f'https://api.telegram.org/bot{TOKEN}/sendPhoto?parse_mode=HTML'
SEND_VIDEO_URL = f'https://api.telegram.org/bot{TOKEN}/sendVideo'

def send_telegram_message(chat_id: int, text: str) -> Dict[str, Any]:
    """
    Send a message to a Telegram chat.

    Args:
        chat_id (int): The ID of the chat to send the message to.
        text (str): The text of the message to send.

    Returns:
        Dict[str, Any]: A dictionary containing the response status and message.
    """
    payload = {'chat_id': chat_id, 'text': text}
    response = requests.post(SEND_MESSAGE_URL, data=payload)
    
    if response.status_code == HTTPStatus.OK:
        print('Message to Telegram sent successfully')
        return {"status": "success", "message": "Message sent successfully"}
    else:
        print(f'Failed to send message to Telegram: {response.text}')
        return {"status": "error", "message": "Failed to send message to Telegram"}



@telegram_bp.route('/chat', methods=['POST'])
async def webhook():
    """
    Handle incoming updates from Telegram.

    Returns:
        flask.Response: A Flask response object with JSON data.
    """
    response_dict = {
        "status": "error",
        "message": "An unexpected error occurred",
        "data": None
    }
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    try:
        update: Dict[str, Any] = request.json

        if not update:
            response_dict["message"] = "Invalid update format."
            status_code = HTTPStatus.BAD_REQUEST
            return jsonify(response_dict), status_code

        if 'message' not in update:
            response_dict["status"] = "success"
            response_dict["message"] = "Update received"
            status_code = HTTPStatus.OK
            return jsonify(response_dict), status_code

        message = update['message']
        if 'text' not in message:
            response_dict["status"] = "success"
            response_dict["message"] = "Non-text message received"
            status_code = HTTPStatus.OK
            return jsonify(response_dict), status_code
        
        if message['chat']['type'] != 'private':
            response_dict["status"] = "success"
            response_dict["message"] = "Message from a group received"
            status_code = HTTPStatus.OK
            return jsonify(response_dict), status_code
    
        chat_id = message['chat']['id']
        user_message = message.get('text', '').strip().lower()

        if user_message == '/start':
            text = "Hello, This is Alpha, an AI Bot that can help you with any question you may have about Cryptocurrencies!"
        else:
            text = "Hello, this is AI Alpha. Please stay tuned for updates as we continue to develop and launch our bot. Thank you for your interest!"
            # Uncomment the following line when aialpha function is implemented
            # text = aialpha(user_message)
    
        result = send_telegram_message(chat_id, text)
        response_dict["status"] = result["status"]
        response_dict["message"] = result["message"]
        status_code = HTTPStatus.OK if result['status'] == 'success' else HTTPStatus.INTERNAL_SERVER_ERROR

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        response_dict["message"] = "An internal server error occurred"

    return jsonify(response_dict), status_code