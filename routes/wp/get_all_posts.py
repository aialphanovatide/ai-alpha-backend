import requests

def get_all_posts():

    url = "https://coinstrategdev.wpenginepowered.com/?wpwhpro_action=get_news&wpwhpro_api_key=5fjtogfdmtjbdljfnvmqt2och2fl3ppvjd9nkxdoa0jt1vkp9ri81nwm1lbfgfrn&action=get_posts"

    headers = {
        "Accept": "*/*",
        "User-Agent": "news"
    }

    json_payload = {"arguments": {"post_type":"post","posts_per_page":8}}

    try:
        response = requests.post(url, headers=headers, json=json_payload)
        response.raise_for_status() 
        data = response.json()

        posts = data.get("data", {}).get("posts", [])

        # for post in posts:
        #     title = post.get("post_title", "N/A")
        #     id = post.get("ID", "N/A")
        #     print(f"Post Title: {title}")
        #     print(f"Post ID: {id}")

        return posts, 200
    
    except requests.exceptions.RequestException as e:
        print(f"Error getting all the post from WP: {e}")
        return [], 500

# Example usage
# posts = get_all_posts()
