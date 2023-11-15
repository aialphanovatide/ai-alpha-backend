from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from models.news_bot.articles_model import ANALIZED_ARTICLE
from config import session

def validate_date_coincodex(date_text):
    try:
        date = datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()
        time_difference = current_time - date
        if time_difference <= timedelta(hours=24):
            return date
    except Exception as e:
        print("Error processing the date in CoinCodex: " + str(e))
        return False

def extract_image_url_coincodex(base_url, image_src):
    image_url = base_url + image_src
    return image_url

def extract_article_content_coincodex(html):
    content = ""
    h2_tags = html.find_all('h2')
    h3_tags = html.find_all('h3')
    p_tags = html.find_all('p')
    for tag in h2_tags + h3_tags + p_tags:
        content += tag.text.strip()
    return content.casefold()

def validate_coincodex_article(article_link, main_keyword):
    base_url = "https://coincodex.com/en/resources/images"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            # Extract date
            date_element = html.find('time')
            date_text = date_element['datetime'].strip() if date_element and 'datetime' in date_element.attrs else None
            valid_date = validate_date_coincodex(date_text)

            # Extract article content
            content = extract_article_content_coincodex(html)

            # Extract image URL
            image_element = html.find('img', class_='img-fluid')
            image_src = image_element['src'] if image_element else None
            image_url = extract_image_url_coincodex(base_url, image_src)

            # Validate title, content, and date
            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)
            is_url_in_db = url_in_db(article_link)
            is_title_in_db = title_in_db(title)

            # If all conditions are met, go on
            if not is_title_in_blacklist and content_validation and not is_url_in_db and not is_title_in_db and valid_date:
                # Update the status to ANALYZED
                normalized_article_url = article_link.strip().casefold()
                is_url_analized = session.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
                if is_url_analized:
                    is_url_analized.is_analized = True
                    session.commit()

                # You might want to do something with the validated data here
                return content, valid_date, image_url, title
    except Exception as e:
        print("Error in CoinCodex: " + str(e))

    return None, None, None, None


