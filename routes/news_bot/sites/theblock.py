from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
from routes.news_bot.validations import validate_content, title_in_blacklist



def validate_date_theblock(html):
    try:
        date_div = html.find('div', class_='timestamp tbcoTimestamp')
        if date_div:
            # Obtener el texto dentro del div
            print(date_div)
            date_text = date_div.get_text().strip()
            dateee = date_text.split('• ')[1]
            datex = dateee.replace(',', '').split(' ')
            if datex:
                final_date_to_validate_str = f"{datex[1]} {datex[0]} {datex[2]}"
                # print(final_date_to_validate_str)
            else:
                print("Incorrect date:", datex)

            # Convertir la cadena a un objeto datetime
            final_date_to_validate = datetime.strptime(final_date_to_validate_str, '%d %B %Y')
            # print("sisi", final_date_to_validate)

            # Obtener la fecha en el formato deseado (sin la hora y la zona horaria)
            formatted_date = final_date_to_validate.strftime('%B %d %Y')
            # print(formatted_date)

            # Verificar si la fecha está dentro de las últimas 24 horas
            current_date = datetime.now().strftime('%B %d %Y')
            if formatted_date == current_date:
                return final_date_to_validate
    except ValueError:
        pass
    return None

def extract_image_urls_theblock(html):
    image_urls = []
    img_elements = html.find_all('img', class_='articleFeatureImage type:primaryImage')
    for img in img_elements:
        src = img.get('src')
        if src:
            image_urls.append(src)
    return image_urls

def extract_article_content_theblock(html):
    main_content_div = html.find('div')
    if main_content_div:
        content = ""
        p_elements = main_content_div.find_all('p')
        for p_element in p_elements:
            content += p_element.text.strip()
        return content.strip().casefold()
    return None

def validate_theblock_article(article_link, main_keyword):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'
    }

    try:
        article_response = requests.get(article_link, headers=headers)
        article_content_type = article_response.headers.get("Content-Type", "").lower()

        if article_response.status_code == 200 and 'text/html' in article_content_type:

            html = BeautifulSoup(article_response.text, 'html.parser')
            title_element = html.find('h1')
            title = title_element.text.strip() if title_element else None

            valid_date = validate_date_theblock(html)
            image_urls = extract_image_urls_theblock(html)
            content = extract_article_content_theblock(html)

            if valid_date and content and title:
                content_validation = validate_content(main_keyword, content)
                title_blacklist = title_in_blacklist(title)
                if content_validation and not title_blacklist:
                    return title, content, valid_date, image_urls
            return None, None, None, None
    
    except Exception as e:
        print("Error in Theblock:", str(e))
        return None, None, None, None



