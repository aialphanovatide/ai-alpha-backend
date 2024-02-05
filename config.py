from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import json  
import os


load_dotenv()

DB_PORT = os.getenv('DB_PORT')
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

class Admin(Base):
    __tablename__ = 'admin'
    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    mail = Column(String(255))
    username = Column(String(255))
    password = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {'admin_id': self.admin_id, 'username': self.username, 'mail': self.mail}

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
    category_name = Column(String)
    time_interval = Column(Integer, default=50)
    is_active = Column(Boolean, default=False)
    border_color = Column(String, default='No Color')
    icon = Column(String, default='No Image')
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
    introduction = relationship("Introduction", back_populates="coin_bot", lazy=True)
    # tokenomics = relationship("Tokenomics", back_populates="coin_bot", lazy=True)
    token_distribution = relationship("Token_distribution", back_populates="coin_bot", lazy=True)
    token_utility = relationship("Token_utility", back_populates="coin_bot", lazy=True)
    value_accrual_mechanisms = relationship("Value_accrual_mechanisms", back_populates="coin_bot", lazy=True)
    competitor = relationship("Competitor", back_populates="coin_bot", lazy=True)
    revenue_model = relationship('Revenue_model', back_populates='coin_bot', lazy=True)
    hacks = relationship('Hacks', back_populates='coin_bot', lazy=True)
    dapps = relationship('DApps', back_populates='coin_bot', lazy=True)
    upgrades = relationship('Upgrades', back_populates='coin_bot', lazy=True)

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
    top_story_id = Column(Integer, ForeignKey('top_story.top_story_id'), nullable=False)

    top_story = relationship('TopStory', back_populates='images')

class Analysis(Base):
    __tablename__ = 'analysis'
    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    analysis = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False) 
    
    images = relationship('AnalysisImage', back_populates='analysis')
    coin_bot = relationship('CoinBot', back_populates='analysis', lazy=True)
    
    def to_dict(self):
        return {
            'analysis_id': self.analysis_id,
            'analysis': self.analysis,
            'created_at': str(self.created_at)}
            

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


<<<<<<< HEAD
# ----------------------------------------
=======
# -----------------------------------------------------------------------------------
    
>>>>>>> 054d2134c5557cfb6d66d2bf0dda117b0427d520
class Introduction(Base):
    __tablename__ = 'introduction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    content = Column(String)
    website = Column(String)
    whitepaper = Column(String)
    dynamic = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot = relationship('CoinBot', back_populates='introduction', lazy=True)
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
        
# class Tokenomics(Base):
#     __tablename__ = 'tokenomics'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
#     token = Column(String)
#     total_supply = Column(String)
#     circulating_supply = Column(String)
#     percentage_circulating_supply = Column(String)
#     max_supply = Column(String)
#     supply_model = Column(String)
#     dynamic = Column(Boolean, default=False)
#     created_at = Column(TIMESTAMP, default=datetime.utcnow)
#     updated_at = Column(TIMESTAMP, default=datetime.utcnow)
#     coin_bot = relationship('CoinBot', back_populates='tokenomics', lazy=True)
#     def as_dict(self):
#         return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Token_distribution(Base):
    __tablename__ = 'token_distribution'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    holder_category = Column(String)
    percentage_held = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot = relationship('CoinBot', back_populates='token_distribution', lazy=True)
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
        
class Token_utility(Base):
    __tablename__ = 'token_utility'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    token_application = Column(String)
<<<<<<< HEAD
    description = Column(Boolean, default=True)
=======
    description = Column(String, default=True)
>>>>>>> 054d2134c5557cfb6d66d2bf0dda117b0427d520
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot = relationship('CoinBot', back_populates='token_utility', lazy=True)
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
        
class Value_accrual_mechanisms(Base):
    __tablename__ = 'value_accrual_mechanisms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    mechanism = Column(String)
    description = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot = relationship('CoinBot', back_populates='value_accrual_mechanisms', lazy=True)
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
        
class Revenue_model(Base):
    __tablename__ = 'revenue_model'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    analized_revenue = Column(String)
    fees_1ys = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot = relationship('CoinBot', back_populates='revenue_model', lazy=True)
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
        
class Hacks(Base):
    __tablename__ = 'hacks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    hack_name = Column(String)
    date = Column(String)
    incident_description = Column(String)
    consequences = Column(String)
    mitigation_measure = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot = relationship('CoinBot', back_populates='hacks', lazy=True)
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
        
class Competitor(Base):
    __tablename__ = 'competitor'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    token = Column(String)
    circulating_supply = Column(String)
    token_supply_model = Column(String)
    current_market_cap = Column(String)
    tvl = Column(String)
    daily_active_users = Column(String)
    transaction_fees = Column(String)
    transaction_speed = Column(String)
    inflation_rate_2022 = Column(String)
    inflation_rate_2023 = Column(String)
    apr = Column(String)
    active_developers = Column(Integer)
    revenue = Column(Integer)
    total_supply = Column(Integer)
    percentage_circulating_supply = Column(Integer)
    max_supply = Column(Integer)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
<<<<<<< HEAD
    coin_bot = relationship('CoinBot', back_populates='competitor', lazy=True)
    # def competitors(self):
    #     return {column.name: getattr(self, column.name) for column in self.__table__.columns}
=======
    
    coin_bot = relationship('CoinBot', back_populates='competitor', lazy=True)
>>>>>>> 054d2134c5557cfb6d66d2bf0dda117b0427d520
    
    def tokenomics(self):
        selected_columns = [
            'id','token','total_supply', 'circulating_supply', 'percentage_circulating_supply',
            'max_supply', 'token_supply_model'
        ]
        return {column: getattr(self, column) for column in selected_columns}
        
    def competitors(self):
        excluded_columns = [
            'id', 'token','circulating_supply', 'token_supply_model', 'current_market_cap',
            'tvl', 'daily_active_users', 'transaction_fees', 'transaction_speed' , 'inflation_rate_2022',
            'inflation_rate_2023', 'apr', 'active_developers', 'revenue'
        ]
<<<<<<< HEAD
        all_columns = [column.name for column in self.__table__.columns]
        remaining_columns = set(all_columns) - set(excluded_columns)
        return {column: getattr(self, column) for column in remaining_columns}
        
=======

        return {column: getattr(self, column) for column in excluded_columns}


>>>>>>> 054d2134c5557cfb6d66d2bf0dda117b0427d520
class DApps(Base):
    __tablename__ = 'dapps'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    dapps = Column(String)
    description = Column(String)
    tvl = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot = relationship('CoinBot', back_populates='dapps', lazy=True)
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
        
class Upgrades(Base):
    __tablename__ = 'upgrades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    event = Column(String)
    date = Column(String)
    event_overview = Column(String)
    impact = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    coin_bot = relationship('CoinBot', back_populates='upgrades', lazy=True)
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
        

# ----------------------------------------


# Export the sql session
Base.metadata.create_all(engine)
# Fa.metadata.create_all(engine) # Creates the FA tables

Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
session = Session() 

ROOT_DIRECTORY = Path(__file__).parent.resolve()

# Check if the user with the given email already exists
existing_user = session.query(User).filter_by(email='testuser@example.com').first()

# Creates the user if not exist
if existing_user is None:
    new_user = User(
        nickname='TestUser',
        email='testuser@example.com',
        email_verified=False,
        picture='https://example.com/testuser.jpg',
    )

    session.add(new_user)
    session.commit()
    print("---TestUser created successfully---")


# Creates the suscription plan
TestUser = session.query(User).filter_by(email='testuser@example.com').first()

if TestUser:
    # Check if a subscription plan with 'layer 1 lmc' already exists for the user
    existing_plan1 = session.query(PurchasedPlan).filter_by(
        user_id=TestUser.user_id, reference_name='layer 1 lmc').first()

    if not existing_plan1:
        subscription_plan1 = PurchasedPlan(
            reference_name='layer 1 lmc',
            price=10,
            is_subscribed=True,
            user_id=TestUser.user_id,
            created_at=datetime.utcnow()
        )
        session.add(subscription_plan1)

    # Check if a subscription plan with 'bitcoin' already exists for the user
    existing_plan2 = session.query(PurchasedPlan).filter_by(
        user_id=TestUser.user_id, reference_name='bitcoin').first()

    if not existing_plan2:
        subscription_plan2 = PurchasedPlan(
            reference_name='bitcoin',
            price=10,
            is_subscribed=True,
            user_id=TestUser.user_id,
            created_at=datetime.utcnow()
        )
        session.add(subscription_plan2)

    session.commit()
    if not existing_plan1 and not existing_plan2:
        print(f"---Subscription plans created successfully---")
else:
    print("---TestUser not found---")



with session:
    try:
        if not session.query(Category).first():
            with open(f'{ROOT_DIRECTORY}/models/data.json', 'r', encoding="utf8") as data_file:
                config = json.load(data_file)
            
                for item in config:   
                    main_keyword = item['main_keyword']
                    alias = item['alias']
                    coins = item['coins']

                    new_category = Category(category=main_keyword,
                                            category_name=alias,
                                            icon=item['icon'],
                                            border_color=item['borderColor'],
                                            )

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
        print(f'---Error populating the database: {str(e)}---')
        session.rollback()

