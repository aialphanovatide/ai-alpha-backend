import os
import base64
import json
import requests
from openai import OpenAI
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key=OPENAI_API_KEY,
)


def generate_poster_prompt(article):
    prompt = f'Please generate a DALL-E prompt exactly related to this {article}, no more than 1 line longer'
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt},
                  {"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1024,
    )
    final_prompt = response.choices[0].message.content

    api_url = 'https://api.openai.com/v1/images/generations'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    data = {
        "model": "dall-e-3",
        "prompt": f'{final_prompt} - depicting an anime style, exclusively in English. DONT USE WEIRD CHARACTERS, unreadable characters or unconventional symbols.',
        "n": 1,
        "size": "512x512"
    }

    response = requests.post(api_url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json()
        image_url = result['data'][0]['url']
        print('image_url: ', image_url)
        image_data = base64.b64encode(requests.get(image_url).content).decode('utf-8')
        return image_data
    else:
        print("Error:", response.status_code, response.text)
        # send_INFO_message_to_slack_channel(title_message="Error generating Image",
        #                                    sub_title="Reason",
        #                                    message=f"{response.text} - Article: {article}"
        #                                    )
        return 'No Image'


generate_poster_prompt("""
Step One: "Bitcoin Wallets Decline Amid Market Pressure"
Step Two:
- Bitcoin has faced significant selling pressure, with its price dropping below $40,000 earlier this week.
- Small Bitcoin wallets have seen major liquidation, with over 487,000 wallets, each holding 1 BTC or less, liquidated in the last four days.
- The swift decline in Bitcoin wallets is the fastest since October, before the start of the major crypto bull cycle.
- Historical patterns suggest such rapid declines often precede a market price bounce.
- The approval of 11 ETFs over the past two weeks, followed by disappointing market performances, is considered a significant factor in the wallet liquidation.
- Analysts warn of a potential further 15-20% slide in Bitcoin price.
- Crypto analyst Ali Martinez warns that if Bitcoin drops below $38,130, short-term holders may face losses, potentially triggering a new wave of panic selling.
Secondary Points:
- Bitcoin is currently trading 0.73% up at $40,104 with a market cap of $786 billion.
- The recent developments may indicate a shift in sentiment among smaller traders, signaling potential market adjustments.
- Investors and the crypto community are closely watching Bitcoin price movements, preparing for potential market reactions.
""")