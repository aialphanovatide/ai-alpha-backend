from openai import OpenAI
import requests
import json
import os
import base64
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key=OPENAI_API_KEY,
)

def resize_image(image_data, target_size=(500, 500)):
    image_binary = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_binary))
    resized_image = image.resize(target_size)
    resized_image_data = base64.b64encode(resized_image.tobytes()).decode('utf-8')
    return resized_image_data

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
        "model": "dall-e-2",
        "prompt": f'{final_prompt} - depicting an anime style, exclusively in English. DONT USE WEIRD CHARACTERS, unreadable characters or unconventional symbols.',
        "n": 1,
        "size": "256x256"
    }

    response = requests.post(api_url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json()
        image_url = result['data'][0]['url']
        image_data = base64.b64encode(requests.get(image_url).content).decode('utf-8')
        return image_data, image_url
    else:
        print("Error:", response.status_code, response.text)
        send_INFO_message_to_slack_channel(title_message="Error generating Image",
                                           sub_title="Reason",
                                           message=f"{response.text} - Article: {article}"
                                           )
        return None



# content='''

# Ripple co-founder and executive chairman Chris Larsen said on Jan. 31 that his personal accounts had been hacked. The news was first reported by crypto analyst ZachXBT, where it was initially thought that the company itself had been hacked.


# According to Larsen:

# “Yesterday, there was unauthorized access to a few of my personal XRP accounts (not @Ripple) — we were quickly able to catch the problem and notify exchanges to freeze the affected addresses. Law enforcement is already involved.”
# The Ripple chairman didn’t confirm the amounts but, per ZachXBT, the breach netted 213 million XRP 
# XRP
# tickers down
# $0.51
#  worth about $112.5 million as of the time of the event.

# Advertisement

# BlockShow by Cointelegraph is back with a crypto festival in Hong Kong, May 8-9 - Secure Your Spot!

# Ad
# The funds were reportedly siphoned and then the perpetrator(s) attempted to launder the XRP through at least six different exchanges.
# '''
# result = generate_poster_prompt(content)

# file_path = "image.txt"
# with open(file_path, 'w') as file:
#     file.write(result)
