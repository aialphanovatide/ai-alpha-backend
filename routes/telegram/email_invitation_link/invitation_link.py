import os
import time
import smtplib
import requests
from pathlib import Path
from flask import jsonify
from email.mime.text import MIMEText
from flask import request, Blueprint
from email.mime.multipart import MIMEMultipart

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID_AI_ALPHA_LITE = os.getenv('CHANNEL_ID_AI_ALPHA_LITE')
CHANNEL_ID_AI_ALPHA_FOUNDERS = os.getenv('CHANNEL_ID_AI_ALPHA_FOUNDERS')

send_email_bp = Blueprint(
    'send_email_bp', __name__,
    template_folder='templates',
    static_folder='static'
)

ROOT_DIRECTORY = Path(__file__).parent.resolve()


async def send_email_to_client(link_to_chat, client_email):
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'info@aialpha.ai'
    sender_password = EMAIL_PASSWORD
    recipient_email = client_email
    subject = 'AI Alpha Invitation Link'
    with open(f'{ROOT_DIRECTORY}/email_body.html', 'r') as file:
        html_content = file.read()
        html_content = html_content.replace('{{ link }}', link_to_chat)


    message = MIMEMultipart() 
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    message.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)

        server.send_message(message)
        print(f"Invitation link sent successfully to {client_email}")
        return f"Invitation link sent successfully to {client_email}"

    except smtplib.SMTPAuthenticationError:
        print("SMTP authentication error. Please check your email credentials.")
        return "SMTP authentication error. Please check your email credentials."

    except smtplib.SMTPException as e:
        print("SMTP exception:", str(e))
        return "SMTP exception:", str(e)

    except Exception as e:
        print("Error occurred:", str(e))
        return "Error occurred:", str(e)

    finally:
        server.quit()



createChatInviteLink = f'https://api.telegram.org/bot{TOKEN}/createChatInviteLink'

@send_email_bp.route('/verification', methods=['GET', 'POST'])
async def send_email(): 
    data = request.get_json()

    customer_data = data.get("customer")
    email = customer_data['email']

    items = data.get("line_items")
    product = items[0]['name']
    
    unix_timestamp = int(time.time())
    unix_timestamp_60_seconds_ago = unix_timestamp + 300 # To add expiration date
   
    if product == 'Alpha Lite':
        payload = {
            "chat_id": CHANNEL_ID_AI_ALPHA_LITE,
            "member_limit": 1,
        }

    else:
         payload = {
            "chat_id": CHANNEL_ID_AI_ALPHA_FOUNDERS,
            "member_limit": 1,
        }
         

    if email:
        response = requests.post(createChatInviteLink, data=payload) 
        print('Telegram response for invitaion link:', response.content)
        if response.status_code == 200:
            response_data = response.json()
        
            invite_link = response_data.get("result", {}).get("invite_link", None)
            if invite_link:
                res = await send_email_to_client(invite_link, email)
                if res:
                    return jsonify({"status": 200, "content": res }), 200
                else:
                    return jsonify({"status": "Error while sending email"}), 500
            else:
                return jsonify({"status": "Error while creating the link"}), 500
        else:
            print('Error while creating invitation link:', response.headers)
            return jsonify({"status": "Error while creating the link"}), 500
    else:
        return jsonify({"status": "Client not registered yet"}), 404
