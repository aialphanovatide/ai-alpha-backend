from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist, url_in_db, title_in_db
from config import AnalyzedArticle as ANALIZED_ARTICLE
from config import session

def validate_date_coinpedia(article_soup):
    try:
        # Find the specific element containing the date text
        date_element = article_soup.find('span', class_='post_date_display')  # Replace 'your-date-class' with the actual class name
        if date_element:
            date_text = date_element.get_text(strip=True)
            date = datetime.strptime(date_text, '%b %d, %Y %H:%M')
            current_time = datetime.now()
            time_difference = current_time - date
            if time_difference <= timedelta(hours=24):
                return date
    except ValueError:
        pass
    return None


from bs4 import BeautifulSoup

def extract_image_url_coinpedia(html):
    try:
       

        # Find the img tag with a src attribute containing the base URL
        img_tag = html.find('img', {'src': lambda x: x and x.startswith('https://image.coinpedia.org/wp-content/uploads')})

        # Extract the image URL from the src attribute
        if img_tag:
            image_url = img_tag['src']
            return image_url
    except Exception as e:
        print(f"Error extracting image URL: {str(e)}")
        return None

            
def validate_coinpedia_article(article_link, main_keyword):
    normalized_article_url = article_link.strip().casefold()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }

        article_response = requests.get(normalized_article_url, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if not 'text/html' in article_content_type or article_response.status_code != 200:
            return None, None, None, None
        else:
            article_soup = BeautifulSoup(article_response.text, 'html.parser')

            #Firstly extract the title and content

            content = ""
            a_elements = article_soup.find_all("p")
            for a in a_elements:
                content += a.text.strip()

            title_element = article_soup.find('h1')
            title = title_element.text.strip() if title_element else None

            is_url_analized = session.query(ANALIZED_ARTICLE).filter(ANALIZED_ARTICLE.url == normalized_article_url).first()
            if is_url_analized:
                is_url_analized.is_analyzed = True
                session.commit()


            try:
                if title and content:
                    is_title_in_blacklist = title_in_blacklist(title)
                    is_valid_content = validate_content(main_keyword, content)
                    is_url_in_db = url_in_db(article_link)
                    is_title_in_db = title_in_db(title)


                    # if the all conditions passed then go on
                    if not is_title_in_blacklist and is_valid_content and not is_url_in_db and not is_title_in_db:
                        valid_date = validate_date_coinpedia(article_soup)
                        
                        image_urls = extract_image_url_coinpedia(article_soup)

                        if valid_date:
                            return title, content, valid_date, image_urls
                        
                return None, None, None, None
                        
            except Exception as e:
                print("Inner Error in cryptoslate" + str(e))
                return None, None, None, None

    except Exception as e:
        print(f"Error in cryptoslate" + str(e))
        return None, None, None, None
      

