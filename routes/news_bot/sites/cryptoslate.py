from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from models.news_bot.articles_model import ANALIZED_ARTICLE
from config import session

def validate_date_cryptoslate(date_text):
    try:
        correct_date = date_text.split('<')[0].strip()
        date = datetime.strptime(correct_date, '%b. %d, %Y')
        current_time = datetime.now()
        time_difference = current_time - date
        if time_difference <= timedelta(hours=24):
            return date
    except ValueError as e:
        print("Error:", str(e))
    return None

def extract_image_url_cryptoslate(html):
    image = html.find('img', class_='nolazy')
    if image:
        src = image.get('src')
        if src:
            return src
    return None

def extract_article_content_cryptoslate(html):
    content = ""
    article = html.find('article', class_='full-article')
    if article:
        h2_tags = article.find_all('h2')
        h3_tags = article.find_all('h3')
        p_tags = article.find_all('p')
        for tag in h2_tags + h3_tags + p_tags:
            content += tag.text.strip()
    return content.casefold()

def validate_cryptoslate_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            # Extract date
            date_div = html.find('div', class_='post-date')
            if date_div:
                date_text = date_div.encode_contents().decode('utf-8')  # Convertir la fecha a string
                valid_date = validate_date_cryptoslate(date_text)
                
                # Extract image URL
                image_url = extract_image_url_cryptoslate(html)

                # Extract article content
                content = extract_article_content_cryptoslate(html)

                # Validate title, content, and date
                title_element = html.find('h1')
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
        print("Error in CryptoSlate:", str(e))

    return None, None, None, None
