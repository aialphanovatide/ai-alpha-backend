from routes.slack.index import client
from slack_sdk.errors import SlackApiError


def send_NEWS_message_to_slack(channel_id, title, date_time, url, summary, images_list, main_keyword):

        
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{title}",
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
				"image_url": f"{images_list[1] if images_list else 'No Image'}",
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
                text=f'New Notification from {str(main_keyword).capitalize()} News Bot', 
                blocks=blocks
            )
            response = result['ok']
            if response == True:
                return f'Message sent successfully to Slack channel {channel_id}', 200

        except SlackApiError as e:
            print(f"Error posting message: {e}")
            return f'Error sending message to Slack channel {channel_id}', 500
        
# send_NEWS_message_to_slack(channel_id="C05RK7CCDEK",
#                             title="Just how bullish is the Bitcoin halving for BTC price? Experts debate",
#                             date_time="2023-10-18",
#                             summary="""
#                             *Experts debate the impact of Bitcoin halving*

#                             - Panel at Swan Pacific Bitcoin Festival discusses whether Bitcoin halving is a bullish event or just a narrative for novice investors.
#                             - Some believe halving is a bullish phenomenon that leads to upside in BTC price.
#                             - Others argue that halving has no direct impact on price and it's the market flow that drives it.
#                             - Speculation plays a significant role in Bitcoin investment.
#                             - Role of derivatives in Bitcoin price discovery is questioned.
#                             - Bitcoin often trades sideways or in a downtrend, making it challenging to hodl.
#                             - Liquidity is seen as the future price catalyst for Bitcoin.
#                             - Signs indicate a potential return to quantitative easing by the Federal Reserve.
#                             """,
#                             url="https://cointelegraph.com/news/how-bullish-is-bitcoin-halving-for-btc-price",
#                             images_list=['width=960/https://s3.cointelegraph.com/uploads/2023-10/0ea71b33-960f-4f8a-8c07-d6220712f9c8.jpg', 'https://s3.cointelegraph.com/uploads/2023-10/e3827d5a-4314-4b0e-8623-115f77e93c6b.png', 'https://s3.cointelegraph.com/storage/uploads/view/ac4d2a4d9ba9a9aa006aa37b33355665.png', 'https://s3.cointelegraph.com/storage/uploads/view/8e7b3440d419145826674bf2b2f93b0f.png', 'https://s3.cointelegraph.com/storage/uploads/view/e2016155533b827e6ad467da1c82bb1c.png', 'https://s3.cointelegraph.com/storage/uploads/view/08f722b45add8b11cfdeba3cee7060c6.svg', 'https://s3.cointelegraph.com/storage/uploads/view/b89166f724b3e5aec098ebf13cab6531.png', 'https://s3.cointelegraph.com/storage/uploads/view/a5fbd88645e2124aaf525b2a56a6cc4d.png', 'https://s3.cointelegraph.com/storage/uploads/view/c3bc0490407720f59d1c058d0a2788ce.png', 'https://s3.cointelegraph.com/storage/uploads/view/639362c27648354dc8b0a2e252b741eb.png', 'https://s3.cointelegraph.com/storage/uploads/view/b24d0875e4ad164da08a655f1deea30b.png', 'https://s3.cointelegraph.com/storage/uploads/view/3ff6797c69a564da563746ed0253bc76.png', 'https://s3.cointelegraph.com/storage/uploads/view/1d52c58c28980f7d1b5ae59007b66b6d.png', 'https://s3.cointelegraph.com/storage/uploads/view/e4445a81770a9da4f177e000eb71ff11.png', 'https://s3.cointelegraph.com/storage/uploads/view/43688dd5428f7fa573e42458351d152f.png', 'https://s3.cointelegraph.com/storage/uploads/view/41d8e0dda58a5047a7f53db98a2edb3c.png', 'https://s3.cointelegraph.com/storage/uploads/view/172fab437bae754ebe42e7a23b48232a.png', 'https://s3.cointelegraph.com/storage/uploads/view/5886af490e0311fa1838e13f042f28e5.png', 'https://zoa.cointelegraph.com/pixel?postId=118445&regionId=1']
#                             )

def send_INFO_message_to_slack_channel(channel_id, title_message, sub_title, message):
        blocks=[
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
            if response == True:
                return f'Message sent successfully to Slack channel {channel_id}', 200

        except SlackApiError as e:
            print(f"Error posting message: {e}")
            return f'Error sending this message: "{title_message}" to Slack channel, Reason:\n{str(e)}', 500

