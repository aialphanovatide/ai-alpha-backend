from routes.slack.index import client
from slack_sdk.errors import SlackApiError

# Sends an article to Slack


def send_NEWS_message_to_slack(channel_id, title, date_time, url, summary, image, category_name, extra_info):
    print('matched keywords:', extra_info)
    blocks = [
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
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Matched Keywords:*\n{extra_info}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary*\n{summary}"
            },
            "accessory": {
                "type": "image",
                "image_url": f"{image}",
                "alt_text": f"{title}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Send to AI Alpha App - {category_name}*"
                    },
            "accessory": {
                        "type": "button",
                        "text": {
                                "type": "plain_text",
                            "text": "SEND",
                                    "emoji": True
                        },
                        "value": f"linkToArticle: {url}",
                        "action_id": "button-action"
                    }
        },
        {
            "type": "divider"
        },
        {
            "type": "divider"
        }
    ]

    try:
        result = client.chat_postMessage(
            channel=channel_id,
            text=f'New Notification from {str(category_name).capitalize()}',
            blocks=blocks
        )

        response = result['ok']
        print('Slack Response: ', response)
        if response == True:
            print(
                f'Article {title} sent successfully to Slack channel {category_name}')
            return f'Article {title} sent successfully to Slack channel {category_name}', 200
        else:
            print(f'Article {title} was not sent: {response}')

    except SlackApiError as e:
        print(f"Error posting message: {e}")
        return f'Error sending message to Slack channel {category_name}', 500


# Send an info message to slack
def send_INFO_message_to_slack_channel(title_message, sub_title, message, channel_id="C06FTS38JRX"):
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


# Deletes a message in slack by TS - timestamp
def delete_messages_in_channel(messages_list, channel_id="C06FTS38JRX"):
    try:
        for message in messages_list:
            response = client.chat_delete(
                channel=channel_id,
                ts=message
            )
            print('response: ', response)
            print(f"Deleted message with timestamp {message}")
        return 'All messages deleted in Slack', 200
    except Exception as e:
        return f'Error while deleting messages in Slack: {str(e)}', 500


# # Test delete slack message
# messages_to_delete = ["1706204718.731639"]
# delete_messages_in_channel(messages_to_delete)


# Test send news
# send_NEWS_message_to_slack(channel_id="C06FTS38JRX",
#                             title="Testing sending top story to AI Alpha",
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
#                             category_name='Bitcoin',
#                             url="https://cointelegraph.com/news/btc-price-41k-bitcoin-us-macro-data-fed-fomc-day",
#                             image="https://oaidalleapiprodscus.blob.core.windows.net/private/org-V3grKfdUrUQTVzr4Y6MaGKAA/user-4aQgDraRZsqDNNzTjEvtdLJD/img-ylKRuEbd9e9xWc1o6RwVOw9C.png?st=2024-01-25T16%3A08%3A37Z&se=2024-01-25T18%3A08%3A37Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2024-01-24T22%3A02%3A06Z&ske=2024-01-25T22%3A02%3A06Z&sks=b&skv=2021-08-06&sig=naEtkOnSFIzRNoUwLfBSj2pMR3SbBIlSSjq6MwX%2BMDw%3D"
#                             )
