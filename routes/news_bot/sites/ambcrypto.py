import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist, title_in_db, url_in_db

def validate_date_ambcrypto(date_text):
    try:
        date = datetime.strptime(date_text, '%B %d, %Y')
  
        if (datetime.now() - date) < timedelta(days=1):
            return date.strftime('%Y-%m-%d')
        else:
            return None
    except Exception as e:
        print("Error proccessing date in ambcrypto" + str(e))
        return None

def extract_image_urls_ambcrypto(soup):

    try:
        image_urls = []
        base_url = "https://statics.ambcrypto.com/wp-content/"

        img_elements = soup.find_all('img')

        for img in img_elements:
            src = img.get('src')

            if src and src.startswith(base_url):
                image_urls.append(src)
        return image_urls
    
    except Exception as e:
        print('Error proccessing the images in ambcrypto' + str(e))
        return []

def extract_article_content_ambcrypto(html):

    try:
        title_element = html.find('h1')
        title = title_element.text.strip() if title_element else None

        content = ""
        content_paragraphs = html.find_all('p')

        for paragraph in content_paragraphs:
            content += paragraph.text.strip()

        return title, content

    except Exception as e:
        print('Error proccessing title and content in Ambcrypto', str(e))
        return None, None

def validate_ambcrypto_article(article_link, main_keyword):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            html = BeautifulSoup(article_response.text, 'html.parser')

            title, content = extract_article_content_ambcrypto(html)

            if title and content:

                is_title_in_blacklist = title_in_blacklist(title)
                is_valid_content = validate_content(main_keyword, content)
                is_url_in_db = url_in_db(article_link)
                is_title_in_db = title_in_db(title)


            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)

            date_element = html.find('time')
            date_text = date_element.text.strip() if date_element else None
            valid_date = validate_date_ambcrypto(date_text)

           
           
            image_urls = extract_image_urls_ambcrypto(article_response.text)

            if valid_date and content and title and not is_title_in_blacklist and content_validation:
                print(title, content, image_urls)
                return content, valid_date, image_urls
            
    except Exception as e:
        print("Error in ambcrypto:", str(e))
        return None, None, None, None

