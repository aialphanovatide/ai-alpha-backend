import re
import requests
from config import session
from bs4 import BeautifulSoup
from datetime import datetime
from models.news_bot.articles_model import ANALIZED_ARTICLE
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db


def validate_date_utoday(html):

    try:
        date_text = html.get_text(strip=True)
        
        article_day = date_text.split(' - ')[0]
        day = article_day.split(', ')[1]

        article_date = datetime.strptime(day, '%m/%d/%Y')
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if article_date == current_date:
            return article_date

        return False
    
    except Exception as e:
        print("Error proccessing date in Utoday", str(e))
        return False
        

def extract_image_url_utoday(article_soup):

    try:
        image_urls = []
        img_elements = article_soup.find_all('img')

        for img in img_elements:
            src = img.get('src')
            if src and src.startswith('https://u.today/sites/default/files/'):
                image_urls.append(src)

       
        return image_urls
    
    except Exception as e:
        print("Error extracting images in Utoday", str(e))
        return False


def validate_utoday_article(article_link, main_keyword):

    normalized_article_url = article_link.strip().casefold()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(normalized_article_url, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            article_soup = BeautifulSoup(article_response.text, 'html.parser')

            # Firstly extract the title and content
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
                if  title and content:
                    is_title_in_blacklist = title_in_blacklist(title)
                    is_valid_content = validate_content(main_keyword, content)
                    is_url_in_db = url_in_db(article_link)
                    is_title_in_db = title_in_db(title)

                    # if the all conditions passed then go on
                    if not is_title_in_blacklist and is_valid_content and not is_url_in_db and not is_title_in_db:

                        # Extract date
                        date_div = article_soup.find('div', class_='humble article__short-humble', string=re.compile(r'\d{1,2}/\d{1,2}/\d{4} - \d{1,2}:\d{2}'))
                        valid_date = validate_date_utoday(date_div)

                        # Extract image URL
                        image_urls = extract_image_url_utoday(article_soup)

                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in Utoday" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in Utoday" + str(e))
        return None, None, None, None
    

# result_title, result_content, result_valid_date, result_image_urls = validate_utoday_article('https://u.today/bitcoin-btc-price-predicted-to-reach-600000-by-cathie-wood', 'bitcoin')

# if result_title:
#     print('Article passed the verifications > ', result_title)
#     print('Date: ', result_valid_date)
# else:
#     print('ARTICLE DID NOT PASSED THE VERIFICATIONS')
