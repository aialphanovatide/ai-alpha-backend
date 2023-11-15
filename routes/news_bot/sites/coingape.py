from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from models.news_bot.articles_model import ANALIZED_ARTICLE
from datetime import datetime
from bs4 import BeautifulSoup
from config import session
import requests
import re

def validate_date_coingape(html):
    try:
        date_div = html.find('div', class_='publishby d-flex')
        print(date_div)
        if date_div:
            date_text = date_div.text.lower()
            print("date: ", date_text)
            if "mins ago" in date_text or "hours ago" in date_text:
                return date_text.strip()
        print("error de fechas")
        return False
    except Exception as e:
        print("Error processing the date in coingape > " + str(e))

def extract_image_urls(html):
    try:
        image_urls = []
        soup = BeautifulSoup(html, 'html.parser')
        img_elements = soup.find_all('img')

        for img in img_elements:
            src = img.get('src')

            if src and src.startswith('https://coingape.com/wp-content/uploads/'):
                image_urls.append(src)

        return image_urls
    except Exception as e:
        print("Error finding Images in coingape" + str(e))
        
def extract_article_content(html):
    
    main_content_div = html.find('div', id='main-content')

    if main_content_div:
        p_elements = main_content_div.find_all('p')
        
        content = ""
        
        for p_element in p_elements:
            content += p_element.text.strip().casefold()
        
        return content

    return None

# Function to validate the article using keywords
def validate_coingape_article(article_link, main_keyword):
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

            # Extract article content using the new function
            content = extract_article_content(article_soup)

            if not title or not content:
                return None, None, None, None
            else:
                # These three following lines change the status of the article to ANALIZED.
                normalized_article_url = article_link.strip().casefold()
                
                is_url_analized = session.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
                if is_url_analized:
                    is_url_analized.is_analized = True
                    session.commit()

                    is_title_in_blacklist = title_in_blacklist(title)
                    content_validation = validate_content(main_keyword, content)
                    is_url_in_db = url_in_db(article_link)
                    is_title_in_db = title_in_db(title)

                    # Check if is_url_analized is not None before accessing attributes
                    if is_title_in_blacklist or not content_validation or is_url_in_db or is_title_in_db:
                        return None, None, None, None

                    valid_date = validate_date_coingape(article_soup)

                    # Extract image URLs from the article
                    image_urls = extract_image_urls(article_response.text)
                    

                    if content_validation and valid_date and title:
                        return title, content, valid_date, image_urls
                    else:
                        return None, None, None, None
    except Exception as e:
        print("Error in extracting content in coingape:" + str(e))
        return None, None, None, None

    
result = validate_coingape_article('https://coingape.com/breaking-sec-delays-grayscale-ethereum-etf-decision-to-2024/?utm_source=24hrsupdateall', 'bitcoin')

if result:
    title, content, valid_date, image_urls = result
    print('Article passed the verifications > ', valid_date)
else:

    print('ARTICLE DID NOT PASS THE VERIFICATIONS')