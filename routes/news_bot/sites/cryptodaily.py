from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from config import AnalyzedArticle as ANALIZED_ARTICLE
from config import session

from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def validate_date_cryptodaily(html):
    try:
        date_element = html.find('div', class_='date-count')
        if date_element:
            # Buscar todas las etiquetas <b> dentro del div con clase "date-count"
            b_elements = date_element.find_all('b')

            # Obtener el contenido de las etiquetas <b>
            b_contents = [b.get_text(separator=' ', strip=True) for b in b_elements]

            if any(keyword in content.lower() for keyword in ["hour ago", "hours ago", "minutes ago"] for content in b_contents):
                return b_contents

            return False
        
    except Exception as e:
        print("Error in CryptoDaily:", str(e))
        return False



def extract_image_url_cryptodaily(html):
    try:
        image = html.find('img', class_='img-fluid post-image')
        if image:
            src = image.get('data-src') or image.get('src')
            if src:
                return src
    except Exception as e:
        print("Error in CryptoDaily:", str(e))
        return None

def validate_cryptodaily_article(article_link, main_keyword):

    normalized_article_url = article_link.strip().casefold()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }

        article_response = requests.get(normalized_article_url, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if not 'text/html' in article_content_type or article_response.status_code != 200:
            return None, None, None, None
        else:
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            #Firstly extract the title and content

            content = ""
            a_elements = article_soup.find_all("p")
            for a in a_elements:
                content += a.text.strip()

            title_element = article_soup.find('h1')
            title = title_element.text.strip() if title_element else None

            is_url_analized = session.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
            if is_url_analized:
                is_url_analized.is_analyzed = True
                session.commit()


            try:
                if title and content:
                    is_title_in_blacklist = title_in_blacklist(title)
                    is_valid_content = validate_content(main_keyword, content)
                    is_url_in_db = url_in_db(article_link)
                    is_title_in_db = title_in_db(title)


                    # if the all conditions passed then go on
                    if not is_title_in_blacklist and is_valid_content and not is_url_in_db and not is_title_in_db:
                        valid_date = validate_date_cryptodaily(article_soup)
                        image_urls = extract_image_url_cryptodaily(article_soup)
                       
                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in Cryptodaily" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in Cryptodaily" + str(e))
        return None, None, None, None
      

