from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

def validate_date_decrypt(html):
    date_tag = html.find('time', datetime=True)
    if date_tag:
        date_text = date_tag.text.strip()
        try:
            # Extrae la fecha de la etiqueta "datetime"
            date = datetime.fromisoformat(date_tag['datetime'])
            # Comprueba si la fecha está dentro de las últimas 24 horas
            current_time = datetime.now()
            time_difference = current_time - date
            if time_difference <= timedelta(hours=24):
                return date
        except (ValueError, KeyError):
            pass
    return None

def extract_image_urls_decrypt(html):
    image_urls = []
    img_tags = html.find_all('img', src=True)
    for img in img_tags:
        src = img['src']
        image_urls.append(src)
    return image_urls

def extract_article_content_decrypt(html):
    main_content_div = html.find('div', class_='post-content')
    if main_content_div:
        content = ""
        p_tags = main_content_div.find_all('p')
        for p in p_tags:
            content += p.text.strip()
        return content.strip().casefold()
    return None

def validate_decrypt_article(article_link):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            
            html = BeautifulSoup(article_response.text, 'html.parser')

            title_element = html.find('h1', class_='post-title')
            title = title_element.text.strip() if title_element else None

            valid_date = validate_date_decrypt(html)
            image_urls = extract_image_urls_decrypt(html)
            content = extract_article_content_decrypt(html)

            if valid_date and content and title:
                print("\nTitle:", title)
                print("Date:", valid_date)
                print("Image URLs:", image_urls)
                return title, content, valid_date, image_urls
            else:
                return None, None, None, None
    except Exception as e:
        print("Error in Decrypt:", str(e))
        return None, None, None, None

