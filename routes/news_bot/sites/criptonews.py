import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from routes.news_bot.validations import title_in_blacklist, validate_content

def validate_date_cryptonews(date_text):
    try:
        if 'm' in date_text:
            # Si la fecha está en minutos
            minutes_ago = int(date_text.split()[0])
            current_time = datetime.now()
            article_date = current_time - timedelta(minutes=minutes_ago)
        else:
            # Si la fecha está en un formato diferente, puedes adaptarlo según el caso
            article_date = None

        if article_date and (current_time - article_date) < timedelta(days=1):
            return article_date.strftime('%Y-%m-%d')
        else:
            return None
    except Exception:
        return None

def extract_image_urls_cryptonews(html):
    image_urls = []
    base_url = "https://cnews24.ru/uploads/"

    soup = BeautifulSoup(html, 'html.parser')
    image_divs = soup.find_all('div', class_='detail-image-wrap')

    for div in image_divs:
        style = div.get('style')
        if style:
            url_start = style.find('(') + 1
            url_end = style.find(')')
            image_url = style[url_start:url_end]
            if image_url.startswith(base_url):
                image_urls.append(image_url)

    return image_urls

def extract_article_content_cryptonews(html):
    title_element = html.find('h1')
    if title_element:
        title = title_element.text.strip()
    else:
        title = None

    content = ""
    content_tags = html.find_all(['h2', 'p'])
    for tag in content_tags:
        content += tag.text.strip() + '\n'

    return title, content

def validate_cryptonews_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Your User-Agent String Here'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        if article_response.status_code != 200:
            return None, None, None, None

        html = BeautifulSoup(article_response.text, 'html.parser')

        date_element = html.find('span', class_='datetime flex middle-xs')
        if date_element:
            date_text = date_element.text.strip()
            valid_date = validate_date_cryptonews(date_text)
        else:
            print('Error: Date not found')
            valid_date = None

        image_urls = extract_image_urls_cryptonews(article_response.text)
        title, content = extract_article_content_cryptonews(html)

        is_title_in_blacklist = title_in_blacklist(title)
        content_validation = validate_content(main_keyword, content)

        if valid_date and content and title and not is_title_in_blacklist and content_validation:
                return content, valid_date, image_urls
    except Exception as e:
        print("Error in CryptoNews:", str(e))

    return None, None, None
