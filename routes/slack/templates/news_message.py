from routes.slack.index import client
from slack_sdk.errors import SlackApiError

def send_NEWS_message_to_slack(channel_id, title, date_time, url, summary, images_list):
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Title: {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Date:*\n{date_time}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*URL:*\n{url}"
                    }
                ]
            },
            {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"*Summary*\n{summary}"
			},
			"accessory": {
				"type": "image",
				"image_url": f"{images_list[0] if images_list else 'No Image'}",
				"alt_text": "alt text for image"
			}
            },
            {
                "type": "divider"
            }
        ]
    
        try:
            result = client.chat_postMessage(
                channel=channel_id,
                text='New Notification from News Bot', 
                blocks=blocks
            )
            response = result['ok']
            if response == True:
                return f'Message sent successfully to Slack channel {channel_id}', 200

        except SlackApiError as e:
            print(f"Error posting message: {e}")
            return f'Error sending message to Slack channel {channel_id}', 500