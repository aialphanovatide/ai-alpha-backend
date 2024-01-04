from openai import OpenAI
import requests
import json
import os




from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv('OPENAI_KEY')

client = OpenAI(
   
    api_key=OPENAI_KEY,
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
    print(final_prompt)
    generate_article_poster(final_prompt)
    return final_prompt

def generate_article_poster(final_prompt): 
    api_url = 'https://api.openai.com/v1/images/generations'
    
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_KEY}'
    }
    data = {
        "model": "dall-e-3",
        "prompt": f'{final_prompt} - using an anime style',
        "n": 1,
        "size": "1024x1024"
    }

    response = requests.post(api_url, headers=headers, data=json.dumps(data))


    if response.status_code == 200:
        result = response.json()
        print("Generated image URL:", result['data'][0]['url'])
    else:
        print("Error:", response.status_code, response.text)
        
        
        
prompt="""
Potential ETF Approval May Impact Bitcoin
- Data provider CryptoQuant predicts a potential Bitcoin correction to $32,000 following the potential approval of a spot ETF.
- This is viewed as a possible "sell the news" event, a term familiar in capital markets where asset prices, leverage, and sentiment increase before a bullish event only to drop shortly after.
- The approval of an ETF is seen as a bullish event as it will open flows to Bitcoin from institutions, creating consistent buying pressure.
- Short-term Bitcoin holders are currently experiencing high unrealized profit margins of 30%, which has historically preceded price corrections.
- CryptoQuant suggests that Bitcoin's price could drop to $32,000, which corresponds to the realized price by the short-term holder.
- Capriole Investments advises prudent portfolio management in light of the potential spot ETF approval.
- In Bitcoin's history, "sell the news" events are common - in 2017, BTC peaked at $20,000 after BTC futures were listed by CME, and in 2021, the world's largest cryptocurrency again reached a peak, hitting $65,000 after Coinbase completed its IPO, before losing ground in subsequent months.
Additional points:
- Bitcoin is currently trading at $42,450 having started the year at $16,000.
- The daily trading volume remains stable at $80 billion, according to CoinMarketCap.
"""


generate_poster_prompt(prompt)