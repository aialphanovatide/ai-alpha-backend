import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from helpers.verifications import validate_content, title_in_blacklist

def validate_date_cointelegraph(date):
   
    current_date = datetime.now()
    valid_date = None

    # Utiliza una expresión regular para extraer la fecha en formato año-mes-día
    date_pattern = r'(\d{4}-\d{2}-\d{2})'
    match = re.search(date_pattern, date)

    if match:
        article_date = datetime.strptime(match.group(1), '%Y-%m-%d')
        # Comprueba si la fecha está dentro del rango de 24 horas
        if current_date.date() == article_date.date() or current_date.date() - article_date.date() == timedelta(days=1):
            valid_date = date

    return valid_date

def extract_image_urls(html):
    image_urls = []
    soup = BeautifulSoup(html, 'html.parser')
    img_elements = soup.find_all('img')

    for img in img_elements:
        srcset = img.get('srcset')
        src = img.get('src')

        if srcset:
            # Divide el atributo srcset en sus componentes y toma la URL de la imagen más grande (última URL)
            srcset_parts = srcset.split(',')
            largest_img_url = srcset_parts[-1].strip().split(' ')[-1]
            image_urls.append(largest_img_url)
        elif src and not src.startswith('data:'):
            image_urls.append(src)

    return image_urls


def validate_cointelegraph_article(article_link, main_keyword):

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


            date_time_element = article_soup.find('time')
            date = date_time_element['datetime'].strip() if date_time_element and 'datetime' in date_time_element.attrs else None
            valid_date = validate_date_cointelegraph(date)

            image_urls = extract_image_urls(article_response.text)

            if  content_validation and valid_date and title:
                return title, content, valid_date, image_urls
            else:
                return None, None, None, None
    except Exception as e:
        # print(str(e))
        return None, None, None, None

