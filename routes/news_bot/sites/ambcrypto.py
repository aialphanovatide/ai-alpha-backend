import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist

def validate_date_ambcrypto(date_text):
    try:
        # Parse the date format: "Published Oct 27, 2023 05:30AM ET"
        date = datetime.strptime(date_text, 'Published %b %d, %Y %I:%M%p %Z')
        return date if (datetime.now() - date) < timedelta(days=1) else None
    except ValueError:
        return None

def extract_image_url_ambcrypto(html):
    img_tag = html.find('img', id='carouselImage')
    if img_tag:
        image_url = img_tag['src']
        return image_url if "i-invdn-com.ambcrypto.com/news" in image_url else None
    return None

def extract_article_content_ambcrypto(html):
    title = html.find('h1', class_='articleHeader').text.strip()
    content = ""
    content_section = html.find('section', class_='w-full')
    if content_section:
        for tag in content_section.find_all(['p', 'h2', 'h3']):
            content += tag.text.strip() + '\n'
    return title, content

def validate_ambcrypto_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            # Extract date
            date_element = html.find('div', class_='contentSectionDetails')
            date_text = date_element.find('span').text.strip()
            valid_date = validate_date_ambcrypto(date_text)

            # Extract image URL
            image_url = extract_image_url_ambcrypto(html)

            # Extract article content
            title, content = extract_article_content_ambcrypto(html)

            # Validate title, content, and date
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)

            if valid_date and content and title and not is_title_in_blacklist and content_validation:
                return content, valid_date, image_url
    except Exception as e:
        print("Error in ambcrypto:", str(e))

    return None, None, None

