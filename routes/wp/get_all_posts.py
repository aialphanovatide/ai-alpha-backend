import os
import requests
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from http import HTTPStatus

# Load environment variables
load_dotenv()

# Get WordPress API key from environment variables
WP_API_KEY = os.getenv('WP_API_KEY')

def get_all_posts() -> Tuple[Dict[str, str], int]:
    """
    Retrieve all posts from WordPress.

    Returns:
        Tuple[Dict[str, str], int]: A tuple containing a dictionary with message, success, error,
        and posts keys, and an HTTP status code.
    """
    url = f"https://coinstrategdev.wpenginepowered.com/?wpwhpro_action=get_news&wpwhpro_api_key={WP_API_KEY}&action=get_posts"

    headers = {
        "Accept": "*/*",
        "User-Agent": "news"
    }

    json_payload = {"arguments": {"post_type": "post", "posts_per_page": 8}}

    response_dict = {"message": None, "success": False, "error": None, "posts": []}
    status_code = HTTPStatus.OK

    try:
        response = requests.post(url, headers=headers, json=json_payload)
        response.raise_for_status() 
        data = response.json()

        posts = data.get("data", {}).get("posts", [])

        if posts:
            response_dict["message"] = f"Successfully retrieved {len(posts)} posts"
            response_dict["success"] = True
            response_dict["posts"] = posts
        else:
            response_dict["message"] = "No posts found"
            response_dict["success"] = True  # Still considered successful, just empty

    except requests.exceptions.RequestException as e:
        response_dict["message"] = "Error getting all posts from WordPress"
        response_dict["error"] = str(e)
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    return response_dict, status_code

# Example usage
# result, status_code = get_all_posts()
# print(result, status_code)

# if result["success"]:
#     for post in result["posts"]:
#         print(f"Post Title: {post.get('post_title', 'N/A')}")
#         print(f"Post ID: {post.get('ID', 'N/A')}")
#         print("---")
