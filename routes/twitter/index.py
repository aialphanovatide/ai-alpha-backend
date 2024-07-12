from tweepy.errors import TweepyException
from dotenv import load_dotenv
import tweepy
import re
import os
from typing import List, Tuple, Optional

# Load environment variables
load_dotenv()

# Twitter API credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_KEY_SECRET = os.getenv("TWITTER_KEY_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Initialize Twitter client
auth = tweepy.Client(
    TWITTER_BEARER_TOKEN,
    TWITTER_API_KEY,
    TWITTER_KEY_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET
)

def find_title_between_asterisks(text: str) -> Optional[str]:
    """
    Find and return the text between single or double asterisks.

    Args:
        text (str): The input text to search.

    Returns:
        Optional[str]: The text between asterisks if found, None otherwise.
    """
    match = re.search(r'\*{1,2}(.*?)\*{1,2}', text)
    return match.group(1) if match else None

def bold(title: str) -> str:
    """
    Convert regular text to bold Unicode characters.

    Args:
        title (str): The input text to convert.

    Returns:
        str: The input text converted to bold Unicode characters.
    """
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold_chars = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return ''.join(bold_chars[chars.index(c)] if c in chars else c for c in title)

def split_string(input_string: str) -> List[str]:
    """
    Split the input string into Twitter-friendly chunks.

    Args:
        input_string (str): The input string to split.

    Returns:
        List[str]: A list of strings, each 280 characters or less.
    """
    title = find_title_between_asterisks(input_string)
    if title:
        bold_title = bold(title)
        input_string = input_string.replace(f"**{title}**", bold_title).replace(f"*{title}*", bold_title)

    result = []
    chunks = input_string.split("- ")
    current_string = chunks[0].replace('\n\n', '\n')

    for part in chunks[1:]:
        part = part.strip()
        if part.endswith('.'):
            part = part[:-1]

        if len(current_string + part) < 280:
            current_string += "• " + part + '\n'
        else:
            result.append(current_string)
            current_string = "• " + part + '\n'

    result.append(current_string)
    return result

def send_tweets_to_twitter(content: str, title: str) -> Tuple[str, int]:
    """
    Send a series of tweets to Twitter.

    Args:
        content (str): The content to be tweeted.
        title (str): The title of the content.

    Returns:
        Tuple[str, int]: A tuple containing a message and an HTTP status code.
    """
    if not content:
        return 'There is no content to send to Twitter', 404

    paragraphs = split_string(content)

    try:
        if len(paragraphs) == 1:
            response = auth.create_tweet(text=paragraphs[0])
            print('Response from Twitter:', response)
            return 'Summary sent to Twitter successfully', 200
        else:
            id = None
            for i, paragraph in enumerate(paragraphs):
                response = auth.create_tweet(text=paragraph, in_reply_to_tweet_id=id)
                print(f'Response from Twitter (tweet {i+1}):', response)
                id = response[0].get("id")
            return f'Summary of *{title}* sent to Twitter successfully', 200

    except TweepyException as e:
        print('An error occurred:', str(e))
        return f'An error occurred: {str(e)}', 500

# Example usage
# result, status_code = send_tweets_to_twitter("Your content here", "Your title here")
# print(result, status_code)
