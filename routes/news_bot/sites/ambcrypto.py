import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from config import AnalyzedArticle as ANALIZED_ARTICLE
from routes.news_bot.validations import validate_content, title_in_blacklist, title_in_db, url_in_db, find_matched_keywords

def validate_date_ambcrypto(date_text):
    try:
        date = datetime.strptime(date_text, '%B %d, %Y')
  
        if (datetime.now() - date) < timedelta(days=1):
            return date.strftime('%Y-%m-%d')
        else:
            return None
        
    except Exception as e:
        print("Error proccessing date in Ambcrypto" + str(e))
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
        print('Error proccessing the images in Ambcrypto' + str(e))
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

def validate_ambcrypto_article(article_link, main_keyword, session_instance):

    normalized_article_url = article_link.strip().casefold()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(normalized_article_url, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if not 'text/html' in article_content_type or article_response.status_code != 200:
            return None, None, None, None, None
        else:
            html = BeautifulSoup(article_response.text, 'html.parser')

            title, content = extract_article_content_ambcrypto(html)
            
            # These three following lines changes the status of the article to ANALIZED.
            is_url_analized = session_instance.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
            
            if is_url_analized:
                is_url_analized.is_analyzed = True
                session_instance.commit()

            try:
                if title and content:
                    is_title_in_blacklist = title_in_blacklist(title, session_instance)
                    is_valid_content = validate_content(main_keyword, content, session_instance)
                    is_url_in_db = url_in_db(normalized_article_url, session_instance)
                    is_title_in_db = title_in_db(title, session_instance)

                    # if the all conditions passed then go on
                    if not is_title_in_blacklist and is_valid_content and not is_url_in_db and not is_title_in_db:

                        date_element = html.find('time')
                        date_text = date_element.text.strip() if date_element else None
                        valid_date = validate_date_ambcrypto(date_text)
                        
                        image_urls = extract_image_urls_ambcrypto(html)
                    
                        if valid_date:
                            matched_keywords = find_matched_keywords(main_keyword, content, session_instance)
                            return title, content, valid_date, image_urls, matched_keywords

                    return None, None, None, None, None
                           
            except Exception as e:
                print("Inner Error in Ambcrypto" + str(e))
                return None, None, None, None, None

    except Exception as e:
        print(f"Error in Ambcrypto" + str(e))
        return None, None, None, None, None

# result_title, result_content, result_valid_date, result_image_urls = validate_ambcrypto_article('https://ambcrypto.com/blockchain-association-opposes-proposed-irs-tax-rules/', 'bitcoin')

# if result_title:
#     print('Article passed the verifications > ', result_title)
#     print('Date: ', result_valid_date)
# else:
#     print('ARTICLE DID NOT PASSED THE VERIFICATIONS')