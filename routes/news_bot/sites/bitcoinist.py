from news_bot.validations import validate_content, title_in_blacklist

from bs4 import BeautifulSoup
from datetime import datetime
import requests

def validate_date_bitcoinist(html):
    # Encuentra el div con la clase 'jeg_meta_date'
    date_div = html.find('div', class_='jeg_meta_date')

    if date_div:
        # Encuentra la etiqueta 'a' dentro del div
        date_link = date_div.find('a')
        if date_link:
            date_text = date_link.text.lower()
            
            # Comprueba si el texto contiene "hours ago"
            if "hours ago" in date_text:
                return date_text

    return False


def extract_image_urls(html):
    image_urls = []
    soup = BeautifulSoup(html, 'html.parser')
    img_elements = soup.find_all('img')

    for img in img_elements:
        src = img.get('src')

        if src and src.startswith('https://bitcoinist.com/wp-content/uploads/'):
            image_urls.append(src)

    return image_urls


# Function to validate the article using keywords
def validate_bitcoinist_article(article_link, main_keyword):


    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }
    
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
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)
        
        if is_title_in_blacklist or not content_validation:
            # print('Article does not meet requirements')
            return None, None, None, None

        valid_date = validate_date_bitcoinist(article_soup)

        # Extract image URLs from the article
        image_urls = extract_image_urls(article_response.text)

        if  content_validation and valid_date and title:
                return title, content, valid_date, image_urls
        else:
            return None, None, None, None
    
