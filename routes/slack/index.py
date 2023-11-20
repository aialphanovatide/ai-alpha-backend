import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.rtm_v2 import RTMClient

load_dotenv()

token=os.getenv("SLACK_BOT_TOKEN")

client = WebClient(
    token=token,
)



