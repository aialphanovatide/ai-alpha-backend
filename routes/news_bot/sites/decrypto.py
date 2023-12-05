import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from config import AnalyzedArticle as ANALIZED_ARTICLE
from routes.news_bot.validations import title_in_blacklist, validate_content, url_in_db, title_in_db

def validate_date_decrypt(html):

    try:
        date_tag = html.find('time', datetime=True)
        if date_tag:
            date_text = date_tag.text.strip()
       
            date = datetime.strptime(date_text, '%b %d, %Y')
            current_time = datetime.now()
            time_difference = current_time - date
            if time_difference <= timedelta(hours=24):
                return date
        
        return None
            
    except Exception as e:
        print("Error proccessing date in Decrypto", str(e))
        return None

def extract_image_urls_decrypt(html):

    try:
        image_urls = []
        img_tags = html.find_all('img', src=True)
        for img in img_tags:
            src = img['src']
            image_urls.append(src)

        return image_urls
    
    except Exception as e:
        print("Error extracting images in Decrypto", str(e))
        return []


def validate_decrypt_article(article_link, main_keyword, session_instance):

    normalized_article_url = article_link.strip().casefold()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(normalized_article_url, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if not 'text/html' in article_content_type or article_response.status_code != 200:
            return None, None, None, None
        else:
            html = BeautifulSoup(article_response.text, 'html.parser')

            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None

            content = ""
            a_elements = html.find_all("p")
            for a in a_elements:
                content += a.text.strip()

            # These three following lines changes the status of the article to ANALIZED.
            is_url_analized = session_instance.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
            
            if is_url_analized:
                is_url_analized.is_analyzed = True
                session_instance.commit()

            try:
                if  title and content:
                    is_title_in_blacklist = title_in_blacklist(title, session_instance)
                    is_valid_content = validate_content(main_keyword, content, session_instance)
                    is_url_in_db = url_in_db(normalized_article_url, session_instance)
                    is_title_in_db = title_in_db(title, session_instance)

                    # if the all conditions passed then go on
                    if not is_title_in_blacklist and is_valid_content and not is_url_in_db and not is_title_in_db: 

                        valid_date = validate_date_decrypt(html)

                        # Extract image URL
                        image_urls = extract_image_urls_decrypt(html)   

                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in Investing" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in Investing" + str(e))
        return None, None, None, None   
    

# result_title, result_content, result_valid_date, result_image_urls = validate_decrypt_article('https://decrypt.co/205495/solana-touches-50-tron-optimism-see-gains', 'bitcoin')

# if result_title:
#     print('Article passed the verifications > ', result_title)
#     print('Date: ', result_valid_date)
# else:
#     print('ARTICLE DID NOT PASSED THE VERIFICATIONS')