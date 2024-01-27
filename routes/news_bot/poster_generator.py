import os
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
    
    prompt=f'Please generate a DALL-E prompt exactly related to this {article}, no more than 1 line longer'
    response = client.chat.completions.create(
            model="gpt-4",
            messages=[ {"role": "system", "content": prompt},
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
        "size": "1024x1024"
    }

    response = requests.post(api_url, headers=headers, data=json.dumps(data))


    if response.status_code == 200:
        result = response.json()
        return result['data'][0]['url']
    else:
        print("Error:", response.status_code, response.text)
        send_INFO_message_to_slack_channel(title_message="Error generating Image",
                                           sub_title="Reason",
                                           message=f"{response.text} - Article: {article}"
                                           )
        return 'No Image'

    
    
    
        



