import os
import requests
from dotenv import load_dotenv

load_dotenv()

WP_API_KEY = os.getenv('WP_API_KEY')


def send_post_request(post_title, post_date, post_content, post_status="publish"):

    url = f"https://coinstrategdev.wpenginepowered.com/?wpwhpro_action=get_news&wpwhpro_api_key={WP_API_KEY}&action=create_post"
    
    data = {
        "post_title": post_title, 
        "post_date": post_date,
        "post_content": post_content,
        "post_status": post_status
    }

    headers = {
        "Accept": "*/*",
        "User-Agent": "news"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  
        
        # Try to parse the JSON response
        response_data = response.json()

        if response_data.get("success", False):
            post_title = response_data.get("data", {}).get("post_data", {}).get("post_title", "Unknown Title")
            permalink = response_data.get("data", {}).get("permalink", "Unknown Permalink")
            return f"{post_title} has been published successfully. Permalink: {permalink}", 200
        else:
            fail_info = response_data.get("msg", "Unknown Error")
            return f"Failed to create post. {fail_info}", 400
        
    except requests.exceptions.HTTPError as errh:
        return f"HTTP Error: {errh}", 300
    except requests.exceptions.ConnectionError as errc:
        return f"Error Connecting: {errc}", 500
    except requests.exceptions.Timeout as errt:
        return f"Timeout Error: {errt}", 500
    except requests.exceptions.RequestException as err:
        return f"Request Exception: {err}", 500 

# # Example usage
post_title = "new article?"
post_date = "2023-12-05"
post_content = "Bitcoin Hits $44,000, Highest Since April - Bitcoin (BTC) reached $44,011 on Bitstamp, marking its highest levels since early April 2022. - The week-to-date gains of BTC have reached 10%, challenging significant resistance. - The $44,000 mark is the high point of a range that has occurred several times since early 2021. - Over $100 million in crypto shorts were liquidated on the day, according to data from statistics resource Coinglass. - Optimistic predictions suggest that Bitcoin is on its way to reach the $48.5-$50.5k marker. - The daily Relative Strength Index (RSI) stood at 80 at the time of writing, which can suggest overbought conditions. Additional Points: - Derivatives led the upside charge for Bitcoin, with spot following. - Some market participants expressed concerns about potential manipulatory moves by large-volume traders. - Analysts warn that these moves could lead to a significant sell-off to lock in profits at the new highs."

# Sending the request and printing the result
result, status_code = send_post_request(post_title, post_date, post_content)
print(result, status_code)