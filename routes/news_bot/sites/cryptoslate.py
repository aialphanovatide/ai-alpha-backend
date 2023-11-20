from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from models.news_bot.articles_model import ANALIZED_ARTICLE
from config import session

def validate_date_cryptoslate(html):
    try:
        # Find the div with class "post-date"
        date_div = html.find('div', class_='post-date')

        if date_div:
            # Extract the date text
            date_text = date_div.get_text(strip=True)
      
            # Extract the correct date from the text
            correct_date = date_text.split('a')[0]
           
            # Convert the correct date string into a datetime object
            article_date = datetime.strptime(correct_date, '%b. %d, %Y')
            
            # Get today's date without the time
            today_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Check if the article date is the same as today
            if article_date.date() == today_date.date():
                return article_date
    except Exception as e:
        print("Error in CryptoSlate:", str(e))
    return None

def extract_image_url_cryptoslate(html):
    image = html.find('img')
    if image:
        src = image.get('src')
        if src:
            return src
    return None


def validate_cryptoslate_article(article_link, main_keyword):
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
                        valid_date = validate_date_cryptoslate(article_soup)
                        image_urls = extract_image_url_cryptoslate(article_soup)
                       
                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in cryptoslate" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in cryptoslate" + str(e))
        return None, None, None, None
      


