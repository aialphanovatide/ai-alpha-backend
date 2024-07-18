
from bs4 import BeautifulSoup


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

html_content = '''
<p><strong class="ql-size-huge" style="color: rgb(13, 13, 13);">Polkadot's Innovations in Blockchain and AI Integration</strong></p>
<p><span style="color: rgb(13, 13, 13);">Polkadot is revolutionising blockchain technology with groundbreaking advancements. Also, its scalable, sharded multichain architecture positions it as a vital force in the AI revolution, ensuring verifiable truth for AI applications.</span></p>
<p><span style="color: rgb(13, 13, 13);">The launch of Polkadot 2.0 is being positively anticipated with key advancements like the Asynchronous Backing, which doubles block production speed, and the Join-Accumulate Machine, which significantly enhances Relay Chain capabilities.&nbsp;</span></p>
<p><strong class="ql-size-large" style="color: rgb(13, 13, 13);">What about its Ecosystem, Treasury and Polkadot 2.0 advances?</strong></p>
'''

title, body = extract_title_and_body(html_content)
print("Title:", title)
print("Body:", body)