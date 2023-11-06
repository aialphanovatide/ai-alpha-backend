from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist


def validate_date_cryptopotato(date_text):
    try:
        # Convertir la fecha en un objeto de fecha
        date = datetime.strptime(date_text, '%b %d, %Y @ %H:%M')
        # Comprobar si la fecha está dentro de las últimas 24 horas
        current_time = datetime.now()
        time_difference = current_time - date
        if time_difference <= timedelta(hours=24):
            return date
    except ValueError:
        pass
    return None

def extract_article_content_cryptopotato(html):
    content = ""
    content_div = html.find('div', class_='entry-content col-sm-11')
    if content_div:
        h2_tags = content_div.find_all('h2')
        p_tags = content_div.find_all('p')
        for tag in h2_tags + p_tags:
            content += tag.text.strip()
    return content.casefold()

def validate_cryptopotato_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            # Extract date
            date_span = html.find('span', class_='last-modified-timestamp')
            date_text = date_span.text.strip() if date_span else None
            valid_date = validate_date_cryptopotato(date_text)

            # Extract article content
            content = extract_article_content_cryptopotato(html)

            # Validate title, content, and date
            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)

            if valid_date and content and title and not is_title_in_blacklist and content_validation:
                return content, valid_date, None
    except Exception as e:
        print("Error in CryptoPotato:", str(e))

    return None, None, None
