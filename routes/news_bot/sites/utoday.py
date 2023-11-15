import re
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist


def validate_date_utoday(html):
    try:
        # Obtener el texto dentro del div
        date_text = html.get_text(strip=True)
        
        # Obtener el día de la fecha en el artículo
        article_day = date_text.split(' - ')[0]
        day = article_day.split(', ')[1]

        # Convertir la fecha a formato datetime
        article_date = datetime.strptime(day, '%m/%d/%Y')
 

        # Obtener la fecha actual sin la información de la hora, los minutos y los segundos
        current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


        # Comparar las fechas
        if article_date == current_date:
            return True
        else:
             print("Date Not Correct")
    except (ValueError, IndexError):
        pass
    return False



def extract_image_url_utoday(base_url, image_src):
    # Construir la URL completa de la imagen
    image_url = base_url + image_src
    return image_url

def extract_article_content_utoday(html):
    content = ""
    content_div = html.find('div', class_='article__content')
    if content_div:
        p_tags = content_div.find_all('p')
        for tag in p_tags:
            content += tag.text.strip()
    return content.casefold()


def validate_utoday_article(article_link, main_keyword):
    base_url = "https://u.today/sites/default/files/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            # Extract date
            date_div = html.find('div', class_='humble article__short-humble', string=re.compile(r'\d{1,2}/\d{1,2}/\d{4} - \d{1,2}:\d{2}'))
            valid_date = validate_date_utoday(date_div)

            # Extract article content
            content = extract_article_content_utoday(html)
    

            # Extract image URL
            image_element = html.find('img')
            image_src = image_element['src'] if image_element else None
            image_url = extract_image_url_utoday(base_url, image_src)

            # Validate title, content, and date
            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)

            if valid_date and content and title and not is_title_in_blacklist and content_validation:
                return content, valid_date, image_url, title
    except Exception as e:
        print("Error in U.Today:", str(e))
    return None, None, None
