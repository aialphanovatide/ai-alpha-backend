import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.parser import parse

def validate_date_cryptonews(date_text):
    try:
        # Utiliza dateutil.parser para analizar el formato de fecha dado
        article_date = parse(date_text)
        # Formatea la fecha en el formato deseado
        return article_date.strftime('%Y-%m-%d')
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

def validate_cryptonews_article(article_link):
    headers = {
        'User-Agent': 'Your User-Agent String Here'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        if article_response.status_code != 200:
            return None, None, None, None

        html = BeautifulSoup(article_response.text, 'html.parser')

        date_element = html.find('time')
        date_text = date_element['datetime'].strip() if date_element and 'datetime' in date_element.attrs else None
        valid_date = validate_date_cryptonews(date_text)



        image_urls = extract_image_urls_cryptonews(article_response.text)
        title, content = extract_article_content_cryptonews(html)

        if valid_date and content and title:
 
            return content, valid_date, image_urls, title
    except Exception as e:
        print(f"Error in cryptonews: {str(e)}")

    return None, None, None

link = "https://cryptonews.com/news/bitcoin-price-prediction-as-btc-price-reverses-on-anticipation-that-blackrock-to-apply-for-spot-ethereum-etf-here-are-the-key-levels-to-watch.htm"
validate_cryptonews_article(link)