from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from news_bot.validations import validate_content, title_in_blacklist


def validate_date_cryptonews(date_text):
    if "m" in date_text or "h" in date_text:
        try:
            time_unit = 1 if "m" in date_text else 60
            time_value = int(date_text.split()[0])
            date = datetime.now() - timedelta(minutes=time_unit * time_value)
            return date
        except ValueError:
            pass
    return None

def extract_image_url_cryptonews(html):
    image_div = html.find('div', class_='detail-image-wrap')
    if image_div:
        style = image_div.get('style')
        if style:
            url_start = style.find('url(')
            url_end = style.find(')', url_start)
            if url_start != -1 and url_end != -1:
                image_url = style[url_start + 4 : url_end]
                return image_url
    return None


def extract_article_content_cryptonews(html):
    content = ""
    h1_tags = html.find_all('h1')
    h2_tags = html.find_all('h2')
    p_tags = html.find_all('p')
    for tag in h1_tags + h2_tags + p_tags:
        content += tag.text.strip()
    return content.casefold()

def validate_cryptonews_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            # Extract date
            date_element = html.find('span', class_='datetime')
            date_text = date_element.text.strip() if date_element else None
            valid_date = validate_date_cryptonews(date_text)

            # Extract article content
            content = extract_article_content_cryptonews(html)

            # Extract image URL
            image_url = extract_image_url_cryptonews(html)

            # Validate title, content, and date
            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)

            if valid_date and content and title and not is_title_in_blacklist and content_validation:
                return content, valid_date, image_url
    except Exception as e:
        print("Error in CryptoNews:", str(e))

    return None, None, None
