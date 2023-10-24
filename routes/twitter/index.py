from tweepy.errors import TweepyException, TooManyRequests
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

# print(auth.get_me())

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

    input_string = input_string.replace(f"**{title}**", bold_title)
    input_string = input_string.replace(f"*{title}*", bold_title)
   
    result = []

    chunks = input_string.split("- ")
    current_string = chunks[0].replace('\n',' ')
    
    for part in chunks[1:]:
        part = part.strip()
        endswith_period = part.endswith('.')

        if endswith_period:
            part = part[:-1]

        if len(current_string + part) < 280:
            current_string += "• " + part + '\n'
        else:
            result.append(current_string)
            current_string = "• " + part + '\n'

    result.append(current_string)
    return result

def send_tweets_to_twitter(content: str, title: str) -> list:

    if len(content) == 0:
        return 'There is no content to send to Twitter', 404

    paragraphs = split_string(content)

    if len(paragraphs) == 1:
        try:
            print('paragraphs[0] > ', paragraphs[0])
            # response = auth.create_tweet(text=paragraphs[0])
            return 'Summary sent to Twitter successfully', 200
        except TweepyException as e:
            print('An error occurred:' + str(e))
            return 'An error occurred:' + str(e), 500
    else:
        id = None 
        try:
            for i, paragraph in enumerate(paragraphs):
                print('paragraph > ', paragraph)
                # response = auth.create_tweet(text=paragraph, in_reply_to_tweet_id=None if i == 0 else id)
                # id = response[0].get("id")

            return f'Summary of *{title}* sent to Twitter successfully', 200

        except TweepyException as e:
            print('An error occurred: ' + str(e))
            return 'An error occurred: ' + str(e), 500


content = """
*Bitcoin Liquidations Reach $400 Million as Short Positions Overwhelm Longs*

- Largest single Bitcoin liquidation order valued at $9.98 million
- 94,168 traders faced liquidation across the crypto market
- Bitcoin shorts experienced liquidations totaling $177.15 million
- Ethereum shorts had approximately $42.23 million worth of positions liquidated
- Majority of liquidated positions were short positions
- Crypto market's upward momentum caught traders off guard, leading to surge in liquidations
- $400 million worth of liquidations for leveraged traders in the past 24 hours
- Short liquidations exceeded longs, indicating a pessimistic outlook among traders
- Bitcoin price surged due to anticipation of increased demand from ETFs
- Approval of US spot Bitcoin ETFs expected in the upcoming weeks
- BlackRock Inc. and Fidelity Investments competing to provide ETFs
- Speculative fervor surrounding Bitcoin due to potential ETF approval
"""
send_tweets_to_twitter(content, "Bitcoin Liquidations Reach $400 Million as Short Positions Overwhelm Longs")