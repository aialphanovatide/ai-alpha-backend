import os
import requests
from typing import Dict, Tuple
from dotenv import load_dotenv
from http import HTTPStatus

# Load environment variables
load_dotenv()

# Get WordPress API key from environment variables
WP_API_KEY = os.getenv('WP_API_KEY')

def delete_post(post_id: int) -> Tuple[Dict[str, str], int]:
    """
    Delete a WordPress post using the provided post ID.

    Args:
        post_id (int): The ID of the post to be deleted.

    Returns:
        Tuple[Dict[str, str], int]: A tuple containing a dictionary with message, success, and error keys,
        and an HTTP status code.
    """
    url = f"https://coinstrategdev.wpenginepowered.com/?wpwhpro_action=get_news&wpwhpro_api_key={WP_API_KEY}&action=delete_post"

    headers = {
        "Accept": "*/*",
        "User-Agent": "news",
    }

    json_payload = {
        "post_id": post_id
    }

    response_dict = {"message": None, "success": False, "error": None}
    status_code = HTTPStatus.OK

    try:
        response = requests.post(url, headers=headers, json=json_payload)
        response.raise_for_status() 
        data = response.json()

        success = data.get("success", False)
        msg = data.get("msg", "")

        if success:
            post_id_deleted = data.get("data", {}).get("post_id", "")
            permalink = data.get("data", {}).get("permalink", "")

            response_dict["message"] = f"Post with ID {post_id_deleted} has been successfully deleted. Permalink: {permalink}"
            response_dict["success"] = True
        else:
            response_dict["message"] = f"Failed to delete post. {msg}"
            response_dict["error"] = msg
            status_code = HTTPStatus.BAD_REQUEST

    except requests.exceptions.RequestException as e:
        response_dict["message"] = f"Error deleting post_id: {post_id}"
        response_dict["error"] = str(e)
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    return response_dict, status_code

# Example usage
# post_id_to_delete = 57
# result, status_code = delete_post(post_id_to_delete)
# print(result, status_code)
