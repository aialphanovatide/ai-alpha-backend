from bs4 import BeautifulSoup
import datetime

def extract_title_and_body(html_content):
    # Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract all <p> tags
    paragraphs = soup.find_all('p')
    
    if not paragraphs:
        return None, None
    
    # Get the title (text inside the first <p>)
    title = paragraphs[0].get_text()
    
    # Get the body (text inside all other <p> tags)
    body = ' '.join(p.get_text() for p in paragraphs[1:])
    
    return title, body

def validate_date(date_text):
    try:
        datetime.datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False