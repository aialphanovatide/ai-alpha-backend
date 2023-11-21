import requests
from config import session
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from models.news_bot.articles_model import ANALIZED_ARTICLE
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db


def validate_date_blockworks(date_text):

    try:
        date = datetime.fromisoformat(date_text['datetime'])
        current_time = datetime.now(date.tzinfo)
        time_difference = current_time - date

        if time_difference <= timedelta(hours=24):
            return date
        
        return None
        
    except Exception as e:
        print("Error proccessing date in Blockworks", str(e))
        return None

def extract_image_url_blockworks(html):

    try:
        image = html.find('img')
        if image:
            srcset = image.get('srcset')
            if srcset:
                parts = srcset.split()
                for i in range(0, len(parts), 2):
                    if parts[i].startswith("https://blockworks-co.imgix.net/"):
                        return parts[i]
        return None
    
    except Exception as e:
        print('Error extracting images in Blockworks', str(e))
        return None


def validate_blockworks_article(article_link, main_keyword):

    normalized_article_url = article_link.strip().casefold()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
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

                        # Extract date
                        date_element = article_soup.find('time')
                        valid_date = validate_date_blockworks(date_element)

                        # Extract image URL
                        image_urls = extract_image_url_blockworks(article_soup)
                       
                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in Blockworks" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in Blockworks" + str(e))
        return None, None, None, None


           

  


