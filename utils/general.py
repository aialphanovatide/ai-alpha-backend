from bs4 import BeautifulSoup
from external_apis_values import CAPITALCOM_RESOLUTION_VALUES

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

def validate_resolution(resolution):
    if resolution is None:
        return "HOUR"
    if resolution.upper() not in CAPITALCOM_RESOLUTION_VALUES:
        raise ValueError(
            f"Invalid resolution value. Expected one of {CAPITALCOM_RESOLUTION_VALUES}"
        )
    return resolution

def validate_max(max_value):
    if max_value is not None:
        max_int = int(max_value)
        if not 1 <= max_int <= 1000:
            raise ValueError("Invalid max value. Expected integer between 1 and 1000")

def validate_headers(headers, required_headers):
    missing_headers = [h for h in required_headers if not headers.get(h)]
    if missing_headers:
        raise ValueError(f"Missing required headers: {', '.join(missing_headers)}")