from config import Article, CoinBot, Blacklist
from difflib import SequenceMatcher
from config import session
import ahocorasick



def title_in_db(input_title): # True if Title already in DB  
    try:
        # Open a session
        # with session:
            # Check if the title already exists in the database (case-insensitive)
            existing_title = session.query(Article).filter(Article.title.ilike(input_title)).first()

            return existing_title is not None

    except Exception as e:
        print(f'Error in title_in_db: {str(e)}')
        return False
    
def url_in_db(input_url): # True if URL already in DB
    try:
       
        # Open a session
        # with session:
            # Check if the URL already exists in the database (case-insensitive)
            existing_url = session.query(Article).filter(Article.url.ilike(input_url.casefold().strip())).first()

            return existing_url is not None

    except Exception as e:
        print(f'Error in url_in_db: {str(e)}')
        return False

def validate_content(bot_name, content):
    try:
        # Open a session
        # with session:
            coin_name = session.query(CoinBot).filter(CoinBot.bot_name == bot_name.casefold()).first()

            if not coin_name:
                # Handle the case where no matching SCRAPPING_DATA object is found
                return False

            keywords = coin_name.keywords
            keyword_values = {keyword.word.casefold() for keyword in keywords}  # Set of case-folded keywords for faster lookup

            # Build Aho-Corasick automaton
            A = ahocorasick.Automaton()
            for idx, keyword in enumerate(keyword_values):
                A.add_word(keyword, (idx, keyword))
            A.make_automaton()

            # Iterate through matches in content
            for _, keyword in A.iter(content.casefold()):
                # If a match is found, return True
                return True

            # No matches found
            return False

    except Exception as e:
        print(f'Error in validate_content: {str(e)}')
        return False


def title_in_blacklist(input_title_formatted): # True if Title in blacklist
    try:
        # Open a session
        # with session:
            # Query the database for the BLACKLIST objects
            black_list = session.query(Blacklist).all()
            black_list_values = {keyword.word.casefold() for keyword in black_list}  # Set for faster lookup

            similarity_threshold = 0.9

            for title in black_list_values:
                title_similarity_ratio = SequenceMatcher(None, input_title_formatted.casefold(), title).ratio()

                if title_similarity_ratio >= similarity_threshold:
                    return True  # If a similar title is found in the blacklist, return True

            # No similar title found in the blacklist
            return False

    except Exception as e:
        print(f'Error in title_in_blacklist: {str(e)}')
        return False




