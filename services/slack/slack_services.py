from services.slack.client import client
from slack_sdk.errors import SlackApiError

LOGS_CHANNEL = "C06FTS38JRX"

# Send an info message to slack
def send_INFO_message_to_slack_channel(title_message, sub_title, message, channel_id=LOGS_CHANNEL):
    blocks = [
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
        }
    ]

    try:
        result = client.chat_postMessage(
            channel=channel_id,
            text=title_message,
            blocks=blocks
        )
        response = result['ok']
        print('\nTS:', result['ts'])
        if response == True:
            return f'Message sent successfully to Slack channel {channel_id}', 200
        else:
            return f'Unable to send message to slack: {str(response)}'

    except SlackApiError as e:
        print(f"Error posting message: {e}")
        return f'Error sending this message: "{title_message}" to Slack channel, Reason:\n{str(e)}', 500