import os
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_PRODUCT_ALERTS = os.getenv('SLACK_PRODUCT_ALERTS')

def send_notification_to_product_alerts_slack_channel(title_message, sub_title, message):

    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title_message}*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{sub_title}:*\n{message}"
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

        slack_response = requests.post(SLACK_PRODUCT_ALERTS, json=payload) 
        if slack_response.status_code == 200:
            return 'Notification sent to Slack successfully', 200
        else:
            return 'Error while sending slack notification', 500
    except Exception as e:
        return f"An error occurred while sending a slack notification: {e}", 500

