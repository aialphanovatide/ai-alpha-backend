import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from datetime import datetime
from routes.news_bot.validations import validate_content, title_in_blacklist

def validate_date_coindesk(html):
    # Encuentra el span con la clase 'typography__StyledTypography-sc-owin6q-0 hcIsFR'
    date_span = html.find('span', class_='typography__StyledTypography-sc-owin6q-0 hcIsFR')

    if date_span:
        date_text = date_span.text.strip()
        
        # Utiliza una expresión regular para extraer el día y el mes del texto de la fecha
        match = re.search(r'(\w+) (\d+), (\d+)', date_text)
        
        if match:
            month_str, day_str, year_str = match.groups()
            current_date = datetime.now()
            
            # Convierte el mes a número utilizando un diccionario de mapeo
            months = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            month = months.get(month_str)
            day = int(day_str)
            year = int(year_str)
            
            # Comprueba si el día, mes y año coinciden con la fecha actual
            if year == current_date.year and month == current_date.month and day == current_date.day:
                return date_text

    return False


def extract_image_urls_coindesk(html):
    image_urls = []
    soup = BeautifulSoup(html, 'html.parser')
    img_elements = soup.find_all('img')

    for img in img_elements:
        src = img.get('src')

        if src and src.startswith('https://www.coindesk.com/resizer/'):
            image_urls.append(src)

    return image_urls


def validate_coindesk_article(article_link, main_keyword):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    article_response = requests.get(article_link, headers=headers)
    article_content_type = article_response.headers.get("Content-Type", "").lower()

    if article_response.status_code == 200 and 'text/html' in article_content_type:
        article_soup = BeautifulSoup(article_response.text, 'html.parser')

        content = ""  

        # Busca el div con la clase 'at-content-wrapper'
        content_div = article_soup.find('div', class_='at-content-wrapper')

        if content_div:
            # Encuentra todos los párrafos (etiquetas <p>) dentro del div
            paragraphs = content_div.find_all('p')

            # Concatena el texto de todos los párrafos para obtener el contenido del artículo
            content = "\n".join(paragraph.text.strip() for paragraph in paragraphs)

        title_element = article_soup.find('h1')
        title = title_element.text.strip() if title_element else None

        if not title or not content:
            # print('Article does not have a title or content')
            return None, None, None, None
        else:
            is_title_in_blacklist = title_in_blacklist(title)
            content_validation = validate_content(main_keyword, content)
            
        if is_title_in_blacklist or not content_validation:
            # print('Article does not meet requirements')
            return None, None, None, None

        valid_date = validate_date_coindesk(article_soup)

        # Extract image URLs from the article
        image_urls = extract_image_urls_coindesk(article_response.text)

        
        if  content_validation and valid_date and title:
            return title, content, valid_date, image_urls
        else:
            # print("The article does not meet the required conditions.")
            return None, None, None, None




# validate_coindesk_article('https://www.coindesk.com/consensus-magazine/2023/09/25/how-much-does-the-first-mover-advantage-matter-for-crypto-staking/', 'lsd')
           