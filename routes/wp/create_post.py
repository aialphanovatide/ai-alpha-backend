import os
import requests
from typing import Dict, Tuple
from dotenv import load_dotenv
from http import HTTPStatus

# Load environment variables
load_dotenv()

# Get WordPress API key from environment variables
WP_API_KEY = os.getenv('WP_API_KEY')

def send_post_request(post_title: str, post_date: str, post_content: str, post_status: str = "publish") -> Tuple[Dict[str, str], int]:
    """
    Send a POST request to create a new WordPress post.

    Args:
        post_title (str): The title of the post.
        post_date (str): The date of the post in YYYY-MM-DD format.
        post_content (str): The content of the post.
        post_status (str, optional): The status of the post. Defaults to "publish".

    Returns:
        Tuple[Dict[str, str], int]: A tuple containing a dictionary with message, success, and error keys,
        and an HTTP status code.
    """
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
    
    response_dict = {"message": None, "success": False, "error": None}
    status_code = HTTPStatus.OK

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  
        
        response_data = response.json()

        if response_data.get("success", False):
            post_title = response_data.get("data", {}).get("post_data", {}).get("post_title", "Unknown Title")
            permalink = response_data.get("data", {}).get("permalink", "Unknown Permalink")
            response_dict["message"] = f"{post_title} has been published successfully. Permalink: {permalink}"
            response_dict["success"] = True
        else:
            fail_info = response_data.get("msg", "Unknown Error")
            response_dict["message"] = f"Failed to create post. {fail_info}"
            response_dict["error"] = fail_info
            status_code = HTTPStatus.BAD_REQUEST
        
    except requests.exceptions.HTTPError as errh:
        response_dict["message"] = "HTTP Error occurred"
        response_dict["error"] = str(errh)
        status_code = HTTPStatus.MULTIPLE_CHOICES
    except requests.exceptions.ConnectionError as errc:
        response_dict["message"] = "Error Connecting"
        response_dict["error"] = str(errc)
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    except requests.exceptions.Timeout as errt:
        response_dict["message"] = "Timeout Error"
        response_dict["error"] = str(errt)
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    except requests.exceptions.RequestException as err:
        response_dict["message"] = "Request Exception"
        response_dict["error"] = str(err)
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    return response_dict, status_code

# Example usage
post_title = "New Article: Bitcoin Hits $44,000"
post_date = "2023-12-05"
post_content = """
Bitcoin Hits $44,000, Highest Since April
- Bitcoin (BTC) reached $44,011 on Bitstamp, marking its highest levels since early April 2022.
- The week-to-date gains of BTC have reached 10%, challenging significant resistance.
- The $44,000 mark is the high point of a range that has occurred several times since early 2021.
- Over $100 million in crypto shorts were liquidated on the day, according to data from statistics resource Coinglass.
- Optimistic predictions suggest that Bitcoin is on its way to reach the $48.5-$50.5k marker.
- The daily Relative Strength Index (RSI) stood at 80 at the time of writing, which can suggest overbought conditions.

Additional Points:
- Derivatives led the upside charge for Bitcoin, with spot following.
- Some market participants expressed concerns about potential manipulatory moves by large-volume traders.
- Analysts warn that these moves could lead to a significant sell-off to lock in profits at the new highs.
"""

# Sending the request and printing the result
# result, status_code = send_post_request(post_title, post_date, post_content)
# print(result, status_code)
