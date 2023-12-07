from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import json  
import os

load_dotenv()

DB_PORT = os.getenv('DB_PORT_MAC')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(db_url)

from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user_table'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String)
    email = Column(String)
    email_verified = Column(String)
    picture = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    purchased_plans = relationship('PurchasedPlan', back_populates='user', lazy=True)

class PurchasedPlan(Base):
    __tablename__ = 'purchased_plan'
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    reference_name = Column(String)
    price = Column(Integer)
    is_subscribed = Column(Boolean)
    user_id = Column(Integer, ForeignKey('user_table.user_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    user = relationship('User', back_populates='purchased_plans')

class Category(Base):
    __tablename__ = 'category'
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, nullable=False)
    time_interval = Column(Integer, default=40)
    is_active = Column(Boolean, default=False)
    image = Column(String, default='No Image')
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    coin_bot = relationship('CoinBot', back_populates='category', lazy=True)

class CoinBot(Base):
    __tablename__ = 'coin_bot'
    bot_id = Column(Integer, primary_key=True, autoincrement=True)
    bot_name = Column(String)
    image = Column(String, default='No Image')
    category_id = Column(Integer, ForeignKey('category.category_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    chart = relationship('Chart', back_populates='coin_bot')
    alerts = relationship('Alert', back_populates='coin_bot')
    sites = relationship('Site', back_populates='coin_bot')
    keywords = relationship('Keyword', back_populates='coin_bot')
    blacklist = relationship('Blacklist', back_populates='coin_bot')
    article = relationship('Article', back_populates='coin_bot')
    analysis = relationship('Analysis', back_populates='coin_bot')
    top_story = relationship('TopStory', back_populates='coin_bot')
    category = relationship('Category', back_populates='coin_bot')

class Keyword(Base):
    __tablename__ = 'keyword'
    keyword_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    coin_bot = relationship('CoinBot', back_populates='keywords', lazy=True)

class Site(Base):
    __tablename__ = 'site'
    site_id = Column(Integer, primary_key=True, autoincrement=True)
    site_name = Column(String)
    base_url = Column(String)
    data_source_url = Column(String)
    is_URL_complete = Column(Boolean)
    main_container = Column(String)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    coin_bot = relationship('CoinBot', back_populates='sites', lazy=True)

class Blacklist(Base):
    __tablename__ = 'blacklist'
    blacklist_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    coin_bot = relationship('CoinBot', back_populates='blacklist', lazy=True)

class Alert(Base):
    __tablename__ = 'alert'
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    alert_name = Column(String)
    alert_message = Column(String)
    symbol = Column(String)
    price = Column(Float)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    coin_bot = relationship('CoinBot', back_populates='alerts', lazy=True)

class Article(Base):
    __tablename__ = 'article'
    article_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)
    title = Column(String)
    url = Column(String) 
    summary = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False) 

    coin_bot = relationship('CoinBot', back_populates='article', lazy=True)
    images = relationship('ArticleImage', back_populates='article', lazy=True)

class ArticleImage(Base):
    __tablename__ = 'article_image'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    article_id = Column(Integer, ForeignKey('article.article_id'), nullable=False)
    article = relationship('Article', back_populates='images')


class TopStory(Base):
    __tablename__ = 'top_story'
    top_story_id = Column(Integer, primary_key=True, autoincrement=True)
    story_date = Column(String)
    summary = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False) 

    coin_bot = relationship('CoinBot', back_populates='top_story', lazy=True)
    images = relationship('TopStoryImage', back_populates='top_story')

class TopStoryImage(Base):
    __tablename__ = 'top_story_image'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    top_story_id = Column(Integer, ForeignKey('top_story.top_story_id'))

    top_story = relationship('TopStory', back_populates='images')

class Analysis(Base):
    __tablename__ = 'analysis'
    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    analysis = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False) 
    
    images = relationship('AnalysisImage', back_populates='analysis')
    coin_bot = relationship('CoinBot', back_populates='analysis', lazy=True)

class AnalysisImage(Base):
    __tablename__ = 'analysis_image'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    analysis_id = Column(Integer, ForeignKey('analysis.analysis_id'), nullable=False)

    analysis = relationship('Analysis', back_populates='images')

class AnalyzedArticle(Base):
    __tablename__ = 'analyzed_article'
    article_id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String)
    url = Column(String)
    is_analyzed = Column(Boolean)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)



class Chart(Base):
    __tablename__ = 'chart'
    chart_id = Column(Integer, primary_key=True, autoincrement=True)
    support_1 = Column(Integer)
    support_2 = Column(Integer)
    support_3 = Column(Integer)
    support_4 = Column(Integer)
    resistance_1 = Column(Integer)
    resistance_2 = Column(Integer)
    resistance_3 = Column(Integer)
    resistance_4 = Column(Integer)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False) 
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    coin_bot = relationship('CoinBot', back_populates='chart', lazy=True)


# Export the sql session
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
session = Session() 

ROOT_DIRECTORY = Path(__file__).parent.resolve()

with session:
    try:
        if not session.query(Category).first():
            with open(f'{ROOT_DIRECTORY}/models/data.json', 'r', encoding="utf8") as data_file:
                config = json.load(data_file)
            
                for item in config:   
                    main_keyword = item['main_keyword']
                    coins = item['coins']

                    new_category = Category(category=main_keyword)

                    for coin in coins:
                        coin_keyword = coin['coin_keyword']
                        keywords = coin['keywords']
                        sites = coin['sites']
                        black_list = coin['black_list']
                        
                        new_coin = CoinBot(bot_name=coin_keyword.casefold())
                        new_coin.category = new_category
                        for keyword in keywords:
                            new_coin.keywords.append(Keyword(word=keyword.casefold()))

                        for word in black_list:
                            new_coin.blacklist.append(Blacklist(word=word.casefold()))

                        for site_data in sites:
                            site = Site(
                                site_name=str(site_data['website_name']),
                                base_url=str(site_data['base_url']).casefold(),
                                data_source_url=str(site_data['site']).capitalize(),
                                is_URL_complete=site_data['is_URL_complete'],
                                main_container=str(site_data['main_container'])
                            )
                            new_coin.sites.append(site)

                            session.add(new_coin)
                            print('-----CoinBot data saved-----')
                            session.commit()

                    session.add(new_category)
                    print('-----Category table populated-----')
                    session.commit()

    except Exception as e:
        print(f'Error populating the database: {str(e)}')
        session.rollback()

