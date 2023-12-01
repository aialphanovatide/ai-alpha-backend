from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from config import AnalyzedArticle as ANALIZED_ARTICLE
from config import session

def validate_date_cryptopotato(html):
    try:
        # Find the span with class "last-modified-timestamp"
        date_span = html.find('span', class_='last-modified-timestamp')
        
        if date_span:
            # Extract the date string from the span
            date_text = date_span.get_text(strip=True)
            
            # Convert the date string to datetime
            article_date = datetime.strptime(date_text, '%b %d, %Y @ %H:%M')
            
            # Check if the date is within the last 24 hours
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

def validate_cryptopotato_article(article_link, main_keyword):
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
                        valid_date = validate_date_cryptopotato(article_soup)
                        image_urls = extract_image_url_cryptopotato(article_soup)
                       
                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in Cryptopotato" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in Cryptopotato" + str(e))
        return None, None, None, None
      

