from models.news_bot.news_bot_model import SCRAPPER_MODEL
from models.news_bot.articles_model import ARTICLE_MODEL
from models.word_files.word_files_model import FILES_MODEL
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DB_PORT = os.getenv('DB_PORT')
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
