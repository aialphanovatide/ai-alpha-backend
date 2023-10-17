from routes.news_bot.validations import validate_content, title_in_blacklist
from bs4 import BeautifulSoup
import requests

def validate_date_coingape(html):
    date_div = html.find('div', class_='publishby d-flex')

    if date_div:
        # Verifica si el texto del div contiene "mins ago" o "hours ago"
        date_text = date_div.text.lower()
        if "mins ago" in date_text or "hours ago" in date_text:
            return date_text.strip()

    return False

def extract_image_urls(html):
    image_urls = []
    soup = BeautifulSoup(html, 'html.parser')
    img_elements = soup.find_all('img')

    for img in img_elements:
        src = img.get('src')

        if src and src.startswith('https://coingape.com/wp-content/uploads/'):
            image_urls.append(src)

    return image_urls
        
def extract_article_content(html):
    # Encuentra el div con el ID 'main-content'
    main_content_div = html.find('div', id='main-content')

    if main_content_div:
        # Encuentra todas las etiquetas 'p' dentro del div 'main-content'
        p_elements = main_content_div.find_all('p')
        
        # Inicializa el contenido del artículo
        content = ""
        
        # Recorre todas las etiquetas 'p' y extrae el texto de las etiquetas 'span' dentro de ellas
        for p_element in p_elements:
            span_elements = p_element.find_all('span')
            for span_element in span_elements:
                content += span_element.text.strip()
        
        return content.strip().casefold()

    return None

# Function to validate the article using keywords
def validate_coingape_article(article_link, main_keyword):

    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
        }
    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower() 

        if article_response.status_code == 200 and 'text/html' in article_content_type:
            article_soup = BeautifulSoup(article_response.text, 'html.parser')

            title_element = article_soup.find('h1')
            title = title_element.text.strip() if title_element else None 

            # Extract article content using the new function
            content = extract_article_content(article_soup)

            # content = "" 
            # all_p_elements = article_soup.findAll("p")
            # for el in all_p_elements:
            #     content += el.text.lower()
        

            if not title or not content:
                # print('Article does not have a title or content')
                return None, None, None, None
            else:
                is_title_in_blacklist = title_in_blacklist(title)
                content_validation = validate_content(main_keyword, content)
            
            if is_title_in_blacklist or not content_validation:
                # print('Article does not meet requirements')
                return None, None, None, None
           
            valid_date = validate_date_coingape(article_soup)

            # Extract image URLs from the article
            image_urls = extract_image_urls(article_response.text)

            if  content_validation and valid_date and title:
                return title, content, valid_date, image_urls
            else:
                return None, None, None, None
    except Exception as e:
        return None, None, None, None


# validate_article('https://coingape.com/weekly-recap-crypto-market-remains-strong-btc-eth-rally/', keyword_dict)
