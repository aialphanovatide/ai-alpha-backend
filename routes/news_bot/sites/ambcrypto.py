import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist

def validate_date_ambcrypto(date_text):
    try:
        date = datetime.strptime(date_text, '%B %d, %Y')
        # Comprueba si la fecha está dentro del rango de 24 horas o es el mismo día
        if (datetime.now() - date) < timedelta(days=2):
            return date.strftime('%Y-%m-%d')
        else:
            return None
    except ValueError:
        return None

def extract_image_urls_ambcrypto(html):
    image_urls = []
    base_url = "https://statics.ambcrypto.com/wp-content/"

    soup = BeautifulSoup(html, 'html.parser')
    img_elements = soup.find_all('img')

    for img in img_elements:
        src = img.get('src')

        if src and src.startswith(base_url):
            image_urls.append(src)
    return image_urls

def extract_article_content_ambcrypto(html):
    title_element = html.find('h1')
    if title_element:
        title = title_element.text.strip()
    else:
        title = None
    content = ""
    content_paragraphs = html.find_all('p')

    for paragraph in content_paragraphs:
        content += paragraph.text.strip() + '\n'
    return title, content

def validate_ambcrypto_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }
    
    print("link:")
    print(article_link)

    try:
        print("Article Link:", article_link) 
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            date_element = html.find('time')
            if date_element:
                date_text = date_element.text.strip()
                valid_date = validate_date_ambcrypto(date_text)
            else:
                print('error date')
                valid_date = None

            image_urls = extract_image_urls_ambcrypto(article_response.text)
            title, content = extract_article_content_ambcrypto(html)

            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)

            if valid_date and content and title and not is_title_in_blacklist and content_validation:
                return content, valid_date, image_urls
    except Exception as e:
        print("Error in ambcrypto:", str(e))

    return None, None, None


