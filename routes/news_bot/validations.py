from models.news_bot.news_bot_model import SCRAPPING_DATA, BLACKLIST
from models.news_bot.articles_model import ARTICLE
from difflib import SequenceMatcher
from config import session
import ahocorasick

def title_in_db(input_title): # true if title already in db
    try:
        # Check if the title already exists in the database (case-insensitive)
        existing_title = session.query(ARTICLE).filter(ARTICLE.title.ilike(input_title)).first()

        if existing_title:
            return True
        else:
            return False

    except Exception as e:
        print(f'Error in title_in_db: {str(e)}')
        return f'Error in title_in_db: {str(e)}'

def url_in_db(input_url): # true if url already in db
    try:

        url = input_url.casefold().strip()
        
        # Check if the URL already exists in the database (case-insensitive)
        existing_url = session.query(ARTICLE).filter(ARTICLE.url.ilike(url)).first()

        if existing_url:
            return True
        else:
            return False

    except Exception as e:
        print(f'Error in url_in_db: {str(e)}')
        return f'Error in url_in_db: {str(e)}'

def validate_content(main_keyword, content): # true if content is valid
    try:
        # Query the database for the SCRAPPING_DATA objects with a case-insensitive match for main_keyword
        scrapping_data_objects = session.query(SCRAPPING_DATA).filter(SCRAPPING_DATA.main_keyword == main_keyword.casefold()).all()

        keywords = scrapping_data_objects[0].keywords
        keyword_values = [keyword.keyword.casefold() for keyword in keywords]  # List of case-folded keywords

        A = ahocorasick.Automaton()
        for idx, keyword in enumerate(keyword_values):
            A.add_word(keyword, (idx, keyword))
        A.make_automaton()

        for _, keyword in A.iter(content.casefold()):
            return True

        return False
    except Exception as e:
        print(f'error in validate_content: {str(e)}')
        return f'error in validate_content: {str(e)}'

def title_in_blacklist(input_title_formatted): # true if title in blacklist

    try:
        black_list = session.query(BLACKLIST).all()
        black_list_values = [keyword.black_Word for keyword in black_list] # list of blacklist

        is_title_in_blacklist = False
        similarity_threshold = 0.9

        for title in black_list_values:
            title_similarity_ratio = SequenceMatcher(None, input_title_formatted.casefold(), title.casefold()).ratio()
        
            if title_similarity_ratio >= similarity_threshold:
                is_title_in_blacklist = True
                break

        return is_title_in_blacklist
    
    except Exception as e:
        print(f'error in title_in_blacklist: {str(e)}')
        return f'error in title_in_blacklist: {str(e)}'




