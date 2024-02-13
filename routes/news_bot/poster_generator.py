from openai import OpenAI
import requests
import json
import os
import base64
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
#from routes.slack.templates.news_message import send_INFO_message_to_slack_channel

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key=OPENAI_API_KEY,
)


def resize_image(image_data, target_size=(500, 500)):
    image_binary = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_binary))
    resized_image = image.resize(target_size)
    resized_image_data = base64.b64encode(
        resized_image.tobytes()).decode('utf-8')
    return resized_image_data

def generate_poster_prompt(article):
    prompt = f'Please generate a DALL-E prompt related to this {article}, no more than 1 line longer. IF THERE IS SOME WORD ABOUT TRUMP, BIDEN OR SOME PRESIDENT, PLEASE KEEP IT OFF AND MAKE A PROMPT WITHOUT THESE WORDS'
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt},
                  {"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1024,
    )
    final_prompt = response.choices[0].message.content
    print(final_prompt)

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
        image_data = base64.b64encode(
            requests.get(image_url).content).decode('utf-8')
        return image_data, image_url
    else:
        print("Error:", response.status_code, response.text)
        # Si la solicitud falla, intenta con un nuevo prompt
        return generate_poster_prompt(article)

content='''
- Article: Step One: "Trump's Re-election: Implications for Bitcoin"
Step Two:
- DWS Group, managing $924.5 billion assets, expresses concerns about the potential impact of Trump's re-election on US treasury bonds and Bitcoin.
- The firm recalls the 2016 election aftermath when Trump’s victory led to a sharp increase in 10-year government bond yields, hinting at possible inflationary pressures with another term.
- CNBC’s Rick Santelli warns of high yield close for 30-year bonds in 2024, a situation that could trigger a wave of selling.
'''
result = generate_poster_prompt(content)

if result is not None:
    image_data, image_url = result
    file_path = "image.txt"
    with open(file_path, 'w') as file:
        file.write(image_data)
else:
    print("No se pudo generar la imagen.")
