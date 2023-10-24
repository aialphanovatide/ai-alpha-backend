from tweepy.errors import TweepyException
# from tweet_counter import count_tweet
from dotenv import load_dotenv
import tweepy
import re
import os

load_dotenv()

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_KEY_SECRET = os.getenv("TWITTER_KEY_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

auth = tweepy.Client(
    TWITTER_BEARER_TOKEN,
    TWITTER_API_KEY,
    TWITTER_KEY_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET
)

def find_title_between_asterisks(text):
    match = re.search(r'\*{1,2}(.*?)\*{1,2}', text)
    if match:
        title = match.group(1)
        return title
    else:
        return None


def bold(title):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold_chars = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"

    output = ""

    for character in title:
        if character in chars:
            output += bold_chars[chars.index(character)]
        else:
            output += character
    return output

def split_string(input_string: str) -> str:

    title = find_title_between_asterisks(input_string)
    bold_title = bold(title)
    input_string = input_string.replace(f"*{title}*", bold_title)

    result = []

    chunks = input_string.split("- ")
    current_string = chunks[0]
    
    for part in chunks[1:]:
        if len(current_string + part) < 280:
            current_string += "- " + part
        else:
            result.append(current_string)
            current_string = "- " + part

    result.append(current_string)
    return result

def send_tweets_to_twitter(content: str) -> list:

    if len(content) == 0:
        return 'There is no content to send to Twitter', 404

    paragraphs = split_string(content)

    if len(paragraphs) == 1:
        try:
            print('paragraphs[0] > ', paragraphs[0])
            # response = auth.create_tweet(text=paragraphs[0])
            # print('response > ',  response.content)
            return 'Summary sent to Twitter successfully', 200
        except TweepyException as e:
            print('An error occurred:' + str(e))
            return 'An error occurred:' + str(e), 500
    else:
        id = None
        try:
            for i, paragraph in enumerate(paragraphs):
                print('paragraph > ', paragraph)
                # response = auth.create_tweet(text=paragraph,
                #                             in_reply_to_tweet_id=None if i==0 else id)
                # print('response > ', response[0])
                # id = response[0].get("id")

            return 'Summary sent to Twitter successfully', 200
        
        except TweepyException as e:
            print('An error occurred:' + str(e))
            return 'An error occurred:' + str(e), 500


content = """
*Cryptocurrency traders face $150 million in liquidations as prices surge*
- Over $150 million of liquidations in cryptocurrency derivatives trading in the past 24 hours
- Majority of liquidations were leveraged shorts, worth $110 million
- Bitcoin traders saw $55 million in liquidations, followed by ether traders with $29 million
- Chainlink speculators suffered over $9 million in liquidations
- Liquidations occurred as bitcoin rallied and altcoins also saw significant gains
- Liquidations happen when traders fail to meet margin requirements or have enough funds to keep positions open.
"""
send_tweets_to_twitter(content)