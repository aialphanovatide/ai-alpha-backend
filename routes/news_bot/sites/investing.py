from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from news_bot.validations import validate_content, title_in_blacklist


def validate_date_investing(date_text):
    try:
        # Extrae la fecha del texto, por ejemplo, "Published Oct 27, 2023 05:30AM ET"
        date = datetime.strptime(date_text, "Published %b %d, %Y %I:%M%p ET")
        # Comprueba si la fecha está dentro de las últimas 24 horas
        current_time = datetime.now()
        time_difference = current_time - date
        if time_difference <= timedelta(hours=24):
            return date
    except ValueError:
        pass
    return None

def extract_image_url_investing(html):
    image = html.find('img', id='carouselImage')
    if image:
        src = image.get('src')
        if src and src.startswith("https://i-invdn-com.investing.com/news/"):
            return src
    return None

def extract_article_content_investing(html):
    content = ""
    p_tags = html.find_all('p')
    for tag in p_tags:
        content += tag.text.strip()
    return content.casefold()

def validate_investing_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            # Extract date
            date_div = html.find('div', class_='contentSectionDetails')
            date_text = date_div.find('span').text if date_div else None
            valid_date = validate_date_investing(date_text)

            # Extract image URL
            image_url = extract_image_url_investing(html)

            # Extract article content
            content = extract_article_content_investing(html)

            # Validate title, content, and date
            title_element = html.find('h1', class_='articleHeader')
            title = title_element.text.strip() if title_element else None
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)

            if valid_date and content and title and not is_title_in_blacklist and content_validation:
                return content, valid_date, image_url
    except Exception as e:
        print("Error in Investing:", str(e))

    return None, None, None
