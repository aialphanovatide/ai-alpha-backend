import os
from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()

token=os.getenv("SLACK_BOT_TOKEN")

client = WebClient(
    token='xoxb-3513855583013-5898199192705-a9ya5KSY45LCdhKd4eeMa8Yx',
)