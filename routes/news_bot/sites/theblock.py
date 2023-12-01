import requests
from config import session
from bs4 import BeautifulSoup
from datetime import datetime
from config import AnalyzedArticle as ANALIZED_ARTICLE
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db



def validate_date_theblock(html):

    try:
        date_div = html.find('div', class_='timestamp tbcoTimestamp')

        if date_div:
            date_text = date_div.get_text().strip()
            date = date_text.split('• ')[1]
            datex = date.replace(',', '').split(' ')
            if datex:
                final_date_to_validate_str = f"{datex[1]} {datex[0]} {datex[2]}"

                final_date_to_validate = datetime.strptime(final_date_to_validate_str, '%d %B %Y')
                formatted_date = final_date_to_validate.strftime('%B %d %Y')
           
                current_date = datetime.now().strftime('%B %d %Y')
                if formatted_date == current_date:
                    return final_date_to_validate
        return None
    
    except Exception as e:
        print("Error proccessing date in TheBlock", str(e))
        return None


def extract_image_urls_theblock(html):

    try:
        image_urls = []
        img_elements = html.find_all('img')
        for img in img_elements:
            src = img.get('src')
            if src:
                image_urls.append(src)
      
        return image_urls
    
    except Exception as e:
        print("Error extracting images in Theblock", str(e))
        return []


def validate_theblock_article(article_link, main_keyword):

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
            is_url_analized = session.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
            
            if is_url_analized:
                is_url_analized.is_analyzed = True
                session.commit()

            try:
                if  title and content:
                    is_title_in_blacklist = title_in_blacklist(title)
                    is_valid_content = validate_content(main_keyword, content)
                    is_url_in_db = url_in_db(normalized_article_url)
                    is_title_in_db = title_in_db(title)

                    # if the all conditions passed then go on
                    if not is_title_in_blacklist and is_valid_content and not is_url_in_db and not is_title_in_db:
                    
                        valid_date = validate_date_theblock(html)
                        image_urls = extract_image_urls_theblock(html)
            
                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in Theblock" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in Theblock" + str(e))
        return None, None, None, None
            


# result_title, result_content, result_valid_date, result_image_urls = validate_theblock_article('https://www.theblock.co/post/263127/bitcoin-etp-exposure-hits-all-time-highs-approval-window-spot-etfs-nears-end', 'bitcoin')

# if result_title:
#     print('Article passed the verifications > ', result_title)
#     print('Date: ', result_valid_date)
# else:
#     print('ARTICLE DID NOT PASSED THE VERIFICATIONS')