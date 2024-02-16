from routes.news_bot.validations import find_matched_keywords, validate_content, title_in_blacklist, url_in_db, title_in_db
from config import AnalyzedArticle as ANALIZED_ARTICLE
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import re


def validate_date_beincrypto(date):
   
    try:
        current_date = datetime.now()
        valid_date = None

        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, date)
        
        if match:
            article_date = datetime.strptime(match.group(1), '%Y-%m-%d')
           
            if current_date.date() == article_date.date() or current_date.date() - article_date.date() == timedelta(days=1):
                valid_date = date

        return valid_date
   
    except Exception as e:
        print("Error proccessing date in Beincrypto", str(e))
        return None


def extract_image_urls(soup):

    try:
        image_urls = []
        img_elements = soup.find_all('img')
        
        for img in img_elements:
            src = img.get('src')
            if src and src.startswith('https://s32679.pcdn.co/'):
                image_urls.append(src)
        return image_urls
    
    except Exception as e:
        print("Error extracting images in Beincrypto", str(e))
        return []


def validate_beincrypto_article(article_link, main_keyword, session_instance):

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
            article_soup = BeautifulSoup(article_response.text, 'html.parser')

            # title
            title_element = article_soup.find('h1')
            title = title_element.text.strip() if title_element else None


            # content
            content = ""
            all_p_elements = article_soup.findAll("p")
            for el in all_p_elements:
                content += el.text.lower()

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

                        # get date and extract it
                        date_time_element = article_soup.find('time')
                        date = date_time_element['datetime'].strip() if date_time_element and 'datetime' in date_time_element.attrs else None
                        valid_date = validate_date_beincrypto(date)

                        # Extract images
                        image_urls = extract_image_urls(article_soup)
                       
                        if valid_date:
                            matched_keywords = find_matched_keywords(main_keyword, content, session_instance)
                            return title, content, valid_date, image_urls, matched_keywords
                        
                return None, None, None, None, None
                        
            except Exception as e:
                print("Inner Error in Beincrypto" + str(e))
                return None, None, None, None, None

    except Exception as e:
        print(f"Error in Beincrypto" + str(e))
        return None, None, None, None, None
        

# result_title, result_content, result_valid_date, result_image_urls = validate_beincrypto_article('https://servedbyadbutler.com/redirect.spark?mid=177750&plid=2144261&setid=609748&channelid=0&cid=786862&banid=521184991&pid=0&textadid=0&tc=1&scheduleid=2067757&adsize=0x0&mt=1700511831918366&sw=1280&sh=720&spr=1&referrer=https%3a%2f%2fbeincrypto.com%2f&hc=1d5c1abe79f03a66926c52de792c314d7f6e9069&location=https://track.youhodler.app/32d78590-62e2-4a0b-b3b4-778ad9160f88?utm_source=bic&utm_medium=fixed&utm_campaign=aff_eng_toppage_youhodler_cloudmining', 'layer 1')

# if result_title:
#     print('Article passed the verifications > ', result_title)
#     print('Date: ', result_valid_date)
# else:
#     print('ARTICLE DID NOT PASSED THE VERIFICATIONS')