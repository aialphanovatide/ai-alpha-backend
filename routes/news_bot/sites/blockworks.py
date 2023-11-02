from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from news_bot.validations import validate_content, title_in_blacklist


def validate_date_blockworks(date_text):
    try:
        # Extrae la fecha de la etiqueta "time"
        date = datetime.fromisoformat(date_text['datetime'])
        # Comprueba si la fecha está dentro de las últimas 24 horas
        current_time = datetime.now()
        time_difference = current_time - date
        if time_difference <= timedelta(hours=24):
            return date
    except (ValueError, KeyError):
        pass
    return None

def extract_image_url_blockworks(html):
    image = html.find('img', class_='object-cover w-full')
    if image:
        srcset = image.get('srcset')
        if srcset:
            # Obtiene la URL de la imagen de la cadena srcset
            parts = srcset.split()
            for i in range(0, len(parts), 2):
                if parts[i].startswith("https://blockworks-co.imgix.net/"):
                    return parts[i]
    return None

def extract_article_content_blockworks(html):
    content = ""
    section = html.find('section', class_='w-full')
    if section:
        p_tags = section.find_all('p')
        for tag in p_tags:
            content += tag.text.strip()
    return content.casefold()

def validate_blockworks_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            # Extract date
            date_element = html.find('time')
            valid_date = validate_date_blockworks(date_element)

            # Extract image URL
            image_url = extract_image_url_blockworks(html)

            # Extract article content
            content = extract_article_content_blockworks(html)

            # Validate title, content, and date
            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)
        
            if valid_date and content and title and not is_title_in_blacklist and content_validation:
                return content, valid_date, image_url
    except Exception as e:
        print("Error in Blockworks:", str(e))

    return None, None, None
