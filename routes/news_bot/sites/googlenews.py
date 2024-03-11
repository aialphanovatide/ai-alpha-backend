import requests
from bs4 import BeautifulSoup
from config import AnalyzedArticle as ANALIZED_ARTICLE
from routes.news_bot.validations import title_in_blacklist, validate_content, url_in_db, title_in_db, find_matched_keywords


def validate_google_news_article(article_link, main_keyword, session_instance):
    normalized_article_url = article_link.strip().casefold()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(normalized_article_url, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if not 'text/html' in article_content_type or article_response.status_code != 200:
            return None, None, None
        else:
            html = BeautifulSoup(article_response.text, 'html.parser')

            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None

            content = ""
            if normalized_article_url.startswith("https://blockchainreporter.net/"):
                content_div = html.find('div', class_='content-inner')
                if content_div:
                    p_elements = content_div.find_all("p")
                    for p in p_elements:
                        content += p.text.strip()
            else:
                p_elements = html.find_all("p")
                for p in p_elements:
                    content += p.text.strip()
            
            # Estas tres siguientes líneas cambian el estado del artículo a ANALIZED.
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

                    if not is_title_in_blacklist and is_valid_content and not is_url_in_db and not is_title_in_db:
                        matched_keywords = find_matched_keywords(main_keyword, content, session_instance)
                        return title, content, matched_keywords
                return None, None, None
                        
            except Exception as e:
                print("Inner Error in Investing" + str(e))
                return None, None, None

    except Exception as e:
        print(f"Error in Investing" + str(e))
        return None, None, None

# result_title, result_content = validate_google_news_article('https://news.google.com/articles/CBMiR2h0dHBzOi8vYmxvY2tjaGFpbnJlcG9ydGVyLm5ldC9kYWlseS1tYXJrZXQtcmV2aWV3LWJ0Yy1ldGgtd2lmLWFwdC1mZXQv0gEA?hl=en-US&gl=US&ceid=US%3Aen', 'ai')

# if result_title:
#     print('Article passed the verifications > ', result_title)
#     print('Content: ', result_content)
# else:
#     print('ARTICLE DID NOT PASSED THE VERIFICATIONS')