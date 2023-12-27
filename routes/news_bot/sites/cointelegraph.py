import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from config import AnalyzedArticle as ANALIZED_ARTICLE


def validate_date_cointelegraph(date):
    try:
        current_date = datetime.now()
        valid_date = None

        # Utiliza una expresión regular para extraer la fecha en formato año-mes-día
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, date)

        if match:
            article_date = datetime.strptime(match.group(1), '%Y-%m-%d')
            time_difference = current_date - article_date
            if timedelta(days=1) > time_difference:
                valid_date = date
        return valid_date
    except Exception as e:
        print("Error in Cointelegraph:", str(e))
        return None

        

def extract_image_urls(html):
    try:
        image_urls = []
        soup = BeautifulSoup(html, 'html.parser')
        img_elements = soup.find_all('img')

        for img in img_elements:
            srcset = img.get('srcset')
            src = img.get('src')

            if srcset:
                srcset_parts = srcset.split(',')
                largest_img_url = srcset_parts[-1].strip().split(' ')[-1]
                image_urls.append(largest_img_url)
            elif src and not src.startswith('data:'):
                image_urls.append(src)
            return image_urls
    except Exception as e:
        print("Error in Cointelegraph:", str(e))
        return None

    

def validate_cointelegraph_article(article_link, main_keyword, session_instance):

    try:

        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
            }
   
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower() 

        if not 'text/html' in article_content_type or article_response.status_code != 200:
            return None, None, None, None
        else:
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
                is_url_analized = session_instance.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
                if is_url_analized:
                    is_url_analized.is_analyzed = True
                    session_instance.commit()

                is_title_in_blacklist = title_in_blacklist(title, session_instance)
                is_valid_content = validate_content(main_keyword, content, session_instance)
                is_url_in_db = url_in_db(normalized_article_url, session_instance)
                is_title_in_db = title_in_db(title, session_instance)

                if is_title_in_blacklist or not is_valid_content or is_url_in_db or is_title_in_db:
                    return None, None, None, None

                date_time_element = article_soup.find('time')
                date = date_time_element['datetime'].strip() if date_time_element and 'datetime' in date_time_element.attrs else None
                valid_date = validate_date_cointelegraph(date)

                image_urls = extract_image_urls(article_response.text)

                if  is_valid_content and valid_date and title:
                    print("date ", valid_date)
                    print("title ", title)
                    print("content ", content)
                    print("imgs ", image_urls)
                    return title, content, valid_date, image_urls
                else:
                    return None, None, None, None
    except Exception as e:
        print("Error in Cointelegraph:", str(e))
        return None, None, None, None
