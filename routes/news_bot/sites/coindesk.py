from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from models.news_bot.articles_model import ANALIZED_ARTICLE
from datetime import datetime
from bs4 import BeautifulSoup
from config import session
import requests
import re

def validate_date_coindesk(html):

    try:
        date_span = html.find('span', class_='typography__StyledTypography-sc-owin6q-0 hcIsFR')

        if date_span:
            date_text = date_span.text.strip()

            # Regular expression to get the date
            match = re.search(r'(\w+) (\d+), (\d+)', date_text)
            
            if match:
                month_str, day_str, year_str = match.groups()
                current_date = datetime.now()
                
                months = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                
                month = months.get(month_str)
                day = int(day_str)
                year = int(year_str)
                
                if year == current_date.year and month == current_date.month and day == current_date.day:
                    return date_text

        return False
    except Exception as e:
        print("Error proccessing the date in Coindesk" + str(e))
        return False


def extract_image_urls_coindesk(soup):
    try:
        image_urls = []
        img_elements = soup.find_all('img')

        for img in img_elements:
            src = img.get('src')
            if src and src.startswith('https://www.coindesk.com/resizer/'):
                image_urls.append(src)

        return image_urls
    
    except Exception as e:
        print("Error extracting images in Coindesk" + str(e))
        return []


def validate_coindesk_article(article_link, main_keyword):

    normalized_article_url = article_link.strip().casefold()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }

        article_response = requests.get(normalized_article_url, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
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
                        valid_date = validate_date_coindesk(article_soup)
                        image_urls = extract_image_urls_coindesk(article_soup)
                       
                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in Coindesk" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in Coindesk" + str(e))
        return None, None, None, None
      


        