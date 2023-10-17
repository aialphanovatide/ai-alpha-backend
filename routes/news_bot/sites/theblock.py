from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

def validate_date_theblock(html):
    date_div = html.find('div', class_='timestamp tbcoTimestamp')
    if date_div:
        date_text = date_div.text.strip()
        try:
            # Extract the date and time from the text
            date = datetime.strptime(date_text, '• %B %d, %Y, %I:%M%p EDT')
            # Check if the date is within the last 24 hours
            current_time = datetime.now()
            time_difference = current_time - date
            if time_difference <= timedelta(hours=24):
                return date
        except ValueError:
            pass
    return None

def extract_image_urls_theblock(html):
    image_urls = []
    img_elements = html.find_all('img', class_='articleFeatureImage type:primaryImage')
    for img in img_elements:
        src = img.get('src')
        if src:
            image_urls.append(src)
    return image_urls

def extract_article_content_theblock(html):
    main_content_div = html.find('div', id='main-content')
    if main_content_div:
        content = ""
        p_elements = main_content_div.find_all('p')
        for p_element in p_elements:
            content += p_element.text.strip()
        return content.strip().casefold()
    return None

def validate_theblock_article(article_link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:

            html = BeautifulSoup(article_response.text, 'html.parser')
            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None

            valid_date = validate_date_theblock(html)
            image_urls = extract_image_urls_theblock(html)
            content = extract_article_content_theblock(html)

            if valid_date and content and title:
                print("\nTitle:", title)
                print("Date:", valid_date)
                print("Image URLs:", image_urls)
                return title, content, valid_date, image_urls
            else:
                return None, None, None, None
    except Exception as e:
        print("Error in Theblock:", str(e))
        return None, None, None, None



