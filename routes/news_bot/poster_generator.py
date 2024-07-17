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
    prompt = f'Generate a DALL-E prompt related to this {article}. It should be 400 characters or less and avoid specific names focused on abstract image without mention letters, numbers or words..'
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt},
                  {"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=1024,
    )
    final_prompt = response.choices[0].message.content[:450] 
    api_url = 'https://api.openai.com/v1/images/generations'

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    data = {
        "model": "dall-e-3",
        "prompt": f'{final_prompt} - depicting an anime style.', 
        "n": 1,
        "size": "1024x1024"
    }
    

    response = requests.post(api_url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json()
        image_url = result['data'][0]['url']
        print("img url: ", image_url)
        return image_url  # Retorna solo la URL de la imagen
    else:
        print("Error:", response.status_code, response.text)
        #send_INFO_message_to_slack_channel(title_message="Error generating DALL-E image", sub_title="Response", message=str(response.text))
        return None





# content='''
# - Fetch.ai (FET) experienced a significant rally of 36% within a 24-hour timeframe, with its price reaching over $2.75. 
# - This surge in value is attributed to a shift in investor interest from meme coins to AI-themed cryptocurrencies, further bolstered by Nvidia's favorable earnings report in February.
# - FET broke out of its five-day consolidation on February 28, resulting in a 166% upswing, with the current trading price around $2.13. 
# - A potential retracement into a stable support level of $2.5 could offer a buying opportunity for investors, possibly leading to a nearly 40% increase in the AI token's value to the $3.0 level.
# - The daily Relative Strength Index (RSI) and price strength at 91 suggest a bullish outlook, indicating the market is currently driven by the bulls. 
# - The Awesome Oscillator indicates a spike in bullish momentum, suggesting a potential bounce after an anticipated pullback.
# - The bullish outlook could be invalidated if Bitcoin's price continues to decline, dragging the entire crypto market down with it. If FET drops below $2.50, the $2.0 level could be the next target.
# - The article advises readers to conduct their own research and consult with financial experts before making any investment decisions, as crypto products and NFTs can be highly risky and unregulated.
# '''
# result = generate_poster_prompt(content)

# if result is not None:
#     image_data, image_url = result
#     file_path = "image.txt"
#     with open(file_path, 'w') as file:
#         file.write(image_data)
# else:
#     print("No se pudo generar la imagen.")
