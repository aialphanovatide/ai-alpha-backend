from models.news_bot.news_bot_model import SCRAPPER_MODEL, SCRAPPING_DATA, BLACKLIST, KEWORDS, SITES
from models.word_files.word_files_model import FILES_MODEL
from models.news_bot.articles_model import ARTICLE_MODEL
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path
import json  
import os

load_dotenv()

news_bot_start_time = 40

DB_PORT = os.getenv('DB_PORT_MAC')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)

FILES_MODEL.metadata.create_all(engine)
SCRAPPER_MODEL.metadata.create_all(engine)
ARTICLE_MODEL.metadata.create_all(engine)

# Export the sql session
session = Session() 
 

ROOT_DIRECTORY = Path(__file__).parent.resolve()

print('_________________')
try: 
    # Populates the sites and keyword tables
    if not session.query(SCRAPPING_DATA).first():

        with open(f'{ROOT_DIRECTORY}/models/news_bot/data.json', 'r') as data_file:
            config = json.load(data_file)

        for item in config:   
            keyword = item['main_keyword']
            keywords = item['keywords']
            sites = item['sites']
            black_list = item['black_list']

            scrapping_data = SCRAPPING_DATA(main_keyword=keyword.casefold())

            for keyword in keywords:
                scrapping_data.keywords.append(KEWORDS(keyword=keyword.casefold()))

            for word in black_list:
                scrapping_data.blacklist.append(BLACKLIST(black_Word=word.casefold()))

            for site_data in sites:
                site = SITES(
                    site=site_data['site'],
                    base_url=site_data['base_url'],
                    website_name=site_data['website_name'],
                    is_URL_complete=site_data['is_URL_complete'],
                    main_container=site_data['main_container']
                )
                scrapping_data.sites.append(site)

            
            session.add(scrapping_data)

        print('Initial site data saved to db')
        session.commit()
except Exception as e:
    print(f'An error occurred: {str(e)}')

