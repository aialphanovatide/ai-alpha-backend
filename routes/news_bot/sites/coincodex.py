from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from news_bot.validations import validate_content, title_in_blacklist


def validate_date_coincodex(date_text):
    try:
        # Convertir la fecha en un objeto de fecha
        date = datetime.strptime(date_text, '%b %d, %Y')
        # Comprobar si la fecha está dentro de las últimas 24 horas
        current_time = datetime.now()
        time_difference = current_time - date
        if time_difference <= timedelta(hours=24):
            return date
    except ValueError:
        pass
    return None

def extract_image_url_coincodex(base_url, image_src):
    # Construir la URL completa de la imagen
    image_url = base_url + image_src
    return image_url

def extract_article_content_coincodex(html):
    content = ""
    h1_tags = html.find_all('h1')
    h2_tags = html.find_all('h2')
    h3_tags = html.find_all('h3')
    p_tags = html.find_all('p')
    for tag in h1_tags + h2_tags + h3_tags + p_tags:
        content += tag.text.strip()
    return content.casefold()

def validate_coincodex_article(article_link, main_keyword):
    base_url = "https://coincodex.com/en/resources/images"

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
            date_text = date_element.find('span').text.strip() if date_element else None
            valid_date = validate_date_coincodex(date_text)

            # Extract article content
            content = extract_article_content_coincodex(html)

            # Extract image URL
            image_element = html.find('img', class_='img-fluid')
            image_src = image_element['src'] if image_element else None
            image_url = extract_image_url_coincodex(base_url, image_src)

            # Validate title, content, and date
            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)

            if valid_date and content and title and not is_title_in_blacklist and content_validation:
                return content, valid_date, image_url
    except Exception as e:
        print("Error in CoinCodex:", str(e))

    return None, None, None
