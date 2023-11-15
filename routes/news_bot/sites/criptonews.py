import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.parser import parse
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from models.news_bot.articles_model import ANALIZED_ARTICLE
from config import session

def validate_date_cryptonews(date_text):
    try:
        article_date = parse(date_text)
        current_date = datetime.now()
        time_difference = current_date - article_date

        if time_difference <= timedelta(hours=24) or article_date.date() == current_date.date():
            return article_date.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"Error in cryptonews: {str(e)}")
        return None


def extract_image_urls_cryptonews(html):
    try:
        image_urls = []
        base_url = "https://cnews24.ru/uploads/"

        soup = BeautifulSoup(html, 'html.parser')
        image_divs = soup.find_all('div', class_='detail-image-wrap')

        for div in image_divs:
            style = div.get('style')
            if style:
                url_start = style.find('(') + 1
                url_end = style.find(')')
                image_url = style[url_start:url_end]
                if image_url.startswith(base_url):
                    image_urls.append(image_url)
        return image_urls
    except Exception as e:
        print(f"Error in cryptonews: {str(e)}")
        return None
        
        
def extract_article_content_cryptonews(html):
    try:
        title_element = html.find('h1')
        if title_element:
            title = title_element.text.strip()
        else:
            title = None

        content = ""
        content_tags = html.find_all(['h2', 'p'])
        for tag in content_tags:
            content += tag.text.strip() + '\n'
        return title, content
    except Exception as e:
        print(f"Error in cryptonews: {str(e)}")
        return None, None

def validate_cryptonews_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Your User-Agent String Here'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        if article_response.status_code != 200:
            return None, None, None, None

        html = BeautifulSoup(article_response.text, 'html.parser')

        date_element = html.find('time')
        date_text = date_element['datetime'].strip() if date_element and 'datetime' in date_element.attrs else None
        valid_date = validate_date_cryptonews(date_text)

        image_urls = extract_image_urls_cryptonews(article_response.text)
        title, content = extract_article_content_cryptonews(html)

        if valid_date and content and title:
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
                return content, valid_date, image_urls, title
            else:
                return None, None, None, None

    except Exception as e:
        print(f"Error in cryptonews: {str(e)}")
        return None, None, None, None
    

