from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from routes.news_bot.validations import validate_content, title_in_blacklist
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
       print()
       return None

# Function to extract image URLs from the HTML content
def extract_image_urls(html):
    image_urls = []
    soup = BeautifulSoup(html, 'html.parser')
    img_elements = soup.find_all('img')
    
    for img in img_elements:
        src = img.get('src')
        if src and src.startswith('https://s32679.pcdn.co/'):
            image_urls.append(src)
    return image_urls


def validate_beincrypto_article(article_link, main_keyword):
    
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }
    try:
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
                # print('Article does not have a title or content')
                return None, None, None, None
            else:
                is_title_in_blacklist = title_in_blacklist(title) # verify if the title is in the blacklist - true if in blacklist
                content_validation = validate_content(main_keyword, content) # true if content valid
                
            if is_title_in_blacklist or not content_validation:
                # print('Article does not meet requirements')
                return None, None, None, None
        
            date_time_element = article_soup.find('time')
            date = date_time_element['datetime'].strip() if date_time_element and 'datetime' in date_time_element.attrs else None

            if not date:
                # print('Article does not have a date')
                return None, None, None, None
            else:
                valid_date = validate_date_beincrypto(date) # return the actual date

            image_urls = extract_image_urls(article_response.text) # return the images

            if  content_validation and valid_date and title:
                return title, content, valid_date, image_urls
            else:
                return None, None, None, None
    except Exception as e:
            print(f'Error in the request of Beincrypto {str(e)}')
            return None, None, None, None
        
