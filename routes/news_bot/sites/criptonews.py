import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.parser import parse
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from models.news_bot.articles_model import ANALIZED_ARTICLE
from config import session


def validate_date_cryptonews(date_text):
    try:
        article_date = parse(date_text, fuzzy_with_tokens=True)
        current_date = datetime.now()
        time_difference = current_date - article_date[0]

        if time_difference <= timedelta(hours=24):
            return article_date[0].strftime('%Y-%m-%d %H:%M:%S')
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
        
        
def validate_cryptonews_article(article_link, main_keyword):

    try:

        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
            }
   
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower() 

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            article_soup = BeautifulSoup(article_response.text, 'html.parser')

            title_element = article_soup.find('h1')
            title = title_element.text.strip() if title_element else None 

            content = "" 
            all_p_elements = article_soup.findAll("p")
            for el in all_p_elements:
                content += el.text.lower()
        

            if not title or not content:
                return None, None, None, None
            else:
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

                if is_title_in_blacklist or not content_validation or is_url_in_db or is_title_in_db:
                    return None, None, None, None

                date_time_element = article_soup.find('time')
                date = date_time_element['datetime'].strip() if date_time_element and 'datetime' in date_time_element.attrs else None
                valid_date = validate_date_cryptonews(date)

                image_urls = extract_image_urls_cryptonews(article_response.text)

                if  content_validation and valid_date and title:
                    return title, content, valid_date, image_urls
                else:
                    return None, None, None, None
    except Exception as e:
        print("Error in Cryptonews:", str(e))
        return None, None, None, None
