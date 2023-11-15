from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from models.news_bot.articles_model import ANALIZED_ARTICLE
from config import session

def validate_date_cryptopotato(date_text):
    try:
        # Convertir la cadena de fecha en un objeto datetime
        article_date = datetime.strptime(date_text, '%d %b %Y')
        # Comprobar si la fecha está dentro de las últimas 24 horas
        current_time = datetime.now()
        time_difference = current_time - article_date
        if time_difference <= timedelta(hours=24):
            return article_date
    except Exception as e:
        print("Error in CryptoPotato:", str(e))
        return False

def extract_image_url_cryptopotato(html):
    try:
        image = html.find('img', class_='wp-post-image')
        if image:
            src = image.get('src') or image.get('data-src')
            if src:
                return src
    except Exception as e:
        print("Error in CryptoPotato:", str(e))
        return False

def extract_article_content_cryptopotato(html):
    try:
        content = ""
        content_div = html.find('div', class_='td-post-content')
        if content_div:
            p_tags = content_div.find_all('p')
            for tag in p_tags:
                content += tag.text.strip()
        return content.casefold()
    except Exception as e:
        print("Error in CryptoPotato:", str(e))
        return False

def validate_cryptopotato_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            # Extract date
            date_element = html.find('time', class_='entry-date published')
            date_text = date_element.text.strip() if date_element else None
            valid_date = validate_date_cryptopotato(date_text)

            # Extract image URL
            image_url = extract_image_url_cryptopotato(html)

            # Extract article content
            content = extract_article_content_cryptopotato(html)

            # Validate title, content, and date
            title_element = html.find('h1', class_='entry-title')
            title = title_element.text.strip() if title_element else None

            # These three following lines change the status of the article to ANALYZED.
            normalized_article_url = article_link.strip().casefold()
            is_url_analized = session.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
            if is_url_analized:
                is_url_analized.is_analized = True
                session.commit()

            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)
            is_url_in_db = url_in_db(article_link)
            is_title_in_db = title_in_db(title)

            # If all conditions are met, go on
            if not is_title_in_blacklist and content_validation and not is_url_in_db and not is_title_in_db:
                return content, valid_date, image_url, title
            else:
                return None, None, None, None
    except Exception as e:
        print("Error in CryptoPotato:", str(e))
        return None, None, None, None

    return None, None, None, None
