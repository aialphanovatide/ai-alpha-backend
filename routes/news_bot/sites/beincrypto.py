from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from models.news_bot.articles_model import ANALIZED_ARTICLE
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import session
import requests
import re


def validate_date_beincrypto(date):
   
    try:
        current_date = datetime.now()
        valid_date = None

        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, date)
        
        if match:
            article_date = datetime.strptime(match.group(1), '%Y-%m-%d')
           
            if current_date.date() == article_date.date() or current_date.date() - article_date.date() == timedelta(days=1):
                valid_date = date

        return valid_date
   
    except Exception as e:
        print("Error proccessing date in Beincrypto", str(e))
        return None


def extract_image_urls(soup):

    try:
        image_urls = []
        img_elements = soup.find_all('img')
        
        for img in img_elements:
            src = img.get('src')
            if src and src.startswith('https://s32679.pcdn.co/'):
                image_urls.append(src)
        return image_urls
    
    except Exception as e:
        print("Error extracting images in Beincrypto", str(e))
        return []


def validate_beincrypto_article(article_link, main_keyword):

    normalized_article_url = article_link.strip().casefold()
    
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }
    
    try:
        article_response = requests.get(normalized_article_url, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower() 

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            article_soup = BeautifulSoup(article_response.text, 'html.parser')

            # title
            title_element = article_soup.find('h1')
            title = title_element.text.strip() if title_element else None


            # content
            content = ""
            all_p_elements = article_soup.findAll("p")
            for el in all_p_elements:
                content += el.text.lower()

            # These three following lines changes the status of the article to ANALIZED.
            is_url_analized = session.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
            
            if is_url_analized:
                is_url_analized.is_analized = True
                session.commit()

            try:
                if title and content:
                    is_title_in_blacklist = title_in_blacklist(title)
                    is_valid_content = validate_content(main_keyword, content)
                    is_url_in_db = url_in_db(article_link)
                    is_title_in_db = title_in_db(title)


                    # if the all conditions passed then go on
                    if not is_title_in_blacklist and is_valid_content and not is_url_in_db and not is_title_in_db:

                        # get date and extract it
                        date_time_element = article_soup.find('time')
                        date = date_time_element['datetime'].strip() if date_time_element and 'datetime' in date_time_element.attrs else None
                        valid_date = validate_date_beincrypto(date)

                        # Extract images
                        image_urls = extract_image_urls(article_soup)
                       
                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in Beincrypto" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in Beincrypto" + str(e))
        return None, None, None, None
        

# result_title, result_content, result_valid_date, result_image_urls = validate_beincrypto_article('https://beincrypto.com/bitcoin-continue-uptrend-funding-rates-reset/', 'bitcoin')

# if result_title:
#     print('Article passed the verifications > ', result_title)
#     print('Date: ', result_valid_date)
# else:
#     print('ARTICLE DID NOT PASSED THE VERIFICATIONS')