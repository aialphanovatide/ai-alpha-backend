from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Float
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
engine = create_engine(db_url, pool_size=30, max_overflow=20)


Base = declarative_base()


class Admin(Base):
    __tablename__ = 'admin'
    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    mail = Column(String(255))
    username = Column(String(255))
    password = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.now)

    def to_dict(self):
        return {'admin_id': self.admin_id, 'username': self.username, 'mail': self.mail}


class User(Base):
    __tablename__ = 'user_table'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String)
    email = Column(String)
    email_verified = Column(String)
    picture = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    purchased_plans = relationship(
        'PurchasedPlan', back_populates='user', lazy=True)


class PurchasedPlan(Base):
    __tablename__ = 'purchased_plan'
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    reference_name = Column(String)
    price = Column(Integer)
    is_subscribed = Column(Boolean)
    user_id = Column(Integer, ForeignKey('user_table.user_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

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
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='category', lazy=True)


class CoinBot(Base):
    __tablename__ = 'coin_bot'
    bot_id = Column(Integer, primary_key=True, autoincrement=True)
    bot_name = Column(String)
    image = Column(String, default='No Image')
    category_id = Column(Integer, ForeignKey(
        'category.category_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    chart = relationship('Chart', back_populates='coin_bot')
    alerts = relationship('Alert', back_populates='coin_bot')
    sites = relationship('Site', back_populates='coin_bot')
    keywords = relationship('Keyword', back_populates='coin_bot')
    blacklist = relationship('Blacklist', back_populates='coin_bot')
    article = relationship('Article', back_populates='coin_bot')
    analysis = relationship('Analysis', back_populates='coin_bot')
    top_story = relationship('TopStory', back_populates='coin_bot')
    category = relationship('Category', back_populates='coin_bot')
    introduction = relationship(
        "Introduction", back_populates="coin_bot", lazy=True)
    tokenomics = relationship(
        "Tokenomics", back_populates="coin_bot", lazy=True)
    token_distribution = relationship(
        "Token_distribution", back_populates="coin_bot", lazy=True)
    token_utility = relationship(
        "Token_utility", back_populates="coin_bot", lazy=True)
    value_accrual_mechanisms = relationship(
        "Value_accrual_mechanisms", back_populates="coin_bot", lazy=True)
    competitor = relationship(
        "Competitor", back_populates="coin_bot", lazy=True)
    revenue_model = relationship(
        'Revenue_model', back_populates='coin_bot', lazy=True)
    hacks = relationship('Hacks', back_populates='coin_bot', lazy=True)
    dapps = relationship('DApps', back_populates='coin_bot', lazy=True)
    upgrades = relationship('Upgrades', back_populates='coin_bot', lazy=True)
    narrative_trading = relationship('NarrativeTrading', back_populates='coin_bot', lazy=True)


class Keyword(Base):
    __tablename__ = 'keyword'
    keyword_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='keywords', lazy=True)



class Used_keywords(Base):
    __tablename__ = 'used_keywords'
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_content = Column(String)
    article_date = Column(String)
    article_url = Column(String)
    keywords = Column(String)
    source = Column(String)
    article_id = Column(Integer, ForeignKey('article.article_id'))
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'))
    created_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', backref='used_keywords')
    # article = relationship('Article', backref='used_keywords') 
    article = relationship('Article', back_populates='used_keywords')
    
    
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Site(Base):
    __tablename__ = 'site'
    site_id = Column(Integer, primary_key=True, autoincrement=True)
    site_name = Column(String)
    base_url = Column(String)
    data_source_url = Column(String)
    is_URL_complete = Column(Boolean)
    main_container = Column(String)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='sites', lazy=True)


class Blacklist(Base):
    __tablename__ = 'blacklist'
    blacklist_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='blacklist', lazy=True)


class Alert(Base):
    __tablename__ = 'alert'
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    alert_name = Column(String)
    alert_message = Column(String)
    symbol = Column(String)
    price = Column(Float)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='alerts', lazy=True)


class Article(Base):
    __tablename__ = 'article'
    article_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)
    title = Column(String)
    url = Column(String)
    summary = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='article', lazy=True)
    images = relationship('ArticleImage', back_populates='article', lazy=True)
    used_keywords = relationship('Used_keywords', back_populates='article', lazy=True)
   

    


class ArticleImage(Base):
    __tablename__ = 'article_image'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    article_id = Column(Integer, ForeignKey(
        'article.article_id'), nullable=False)
    article = relationship('Article', back_populates='images')


class TopStory(Base):
    __tablename__ = 'top_story'
    top_story_id = Column(Integer, primary_key=True, autoincrement=True)
    story_date = Column(String)
    summary = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='top_story', lazy=True)
    images = relationship('TopStoryImage', back_populates='top_story')


class TopStoryImage(Base):
    __tablename__ = 'top_story_image'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    top_story_id = Column(Integer, ForeignKey(
        'top_story.top_story_id'), nullable=False)

    top_story = relationship('TopStory', back_populates='images')


class Analysis(Base):
    __tablename__ = 'analysis'
    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    analysis = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    category_name = Column(String, nullable=False, default=None)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)

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
    created_at = Column(TIMESTAMP, default=datetime.now)
    analysis_id = Column(Integer, ForeignKey(
        'analysis.analysis_id'), nullable=False)

    analysis = relationship('Analysis', back_populates='images')


class AnalyzedArticle(Base):
    __tablename__ = 'analyzed_article'
    article_id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String)
    url = Column(String)
    is_analyzed = Column(Boolean)
    created_at = Column(TIMESTAMP, default=datetime.now)

class NarrativeTrading(Base):
    __tablename__ = 'narrative_trading'
    narrative_trading_id = Column(Integer, primary_key=True, autoincrement=True)
    narrative_trading = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    category_name = Column(String, nullable=False, default=None)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='narrative_trading', lazy=True)

    def to_dict(self):
        return {
            'narrative_trading_id': self.narrative_trading_id,
            'narrative_trading': self.narrative_trading,
            'created_at': str(self.created_at)}


class Chart(Base):
    __tablename__ = 'chart'
    chart_id = Column(Integer, primary_key=True, autoincrement=True)
    support_1 = Column(Float)
    support_2 = Column(Float)
    support_3 = Column(Float)
    support_4 = Column(Float)
    resistance_1 = Column(Float)
    resistance_2 = Column(Float)
    resistance_3 = Column(Float)
    resistance_4 = Column(Float)
    token = Column(String)
    pair = Column(String)
    temporality = Column(String)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='chart', lazy=True)


# -----------------------------------------------------------------------------------

class Introduction(Base):
    __tablename__ = 'introduction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    content = Column(String)
    website = Column(String)
    whitepaper = Column(String)
    dynamic = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    coin_bot = relationship(
        'CoinBot', back_populates='introduction', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Tokenomics(Base):
    __tablename__ = 'tokenomics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    token = Column(String)
    total_supply = Column(String)
    circulating_supply = Column(String)
    percentage_circulating_supply = Column(String)
    max_supply = Column(String)
    supply_model = Column(String)
    dynamic = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='tokenomics', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Token_distribution(Base):
    __tablename__ = 'token_distribution'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    holder_category = Column(String)
    percentage_held = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    coin_bot = relationship(
        'CoinBot', back_populates='token_distribution', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Token_utility(Base):
    __tablename__ = 'token_utility'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    token_application = Column(String)
    description = Column(String, default=True)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    coin_bot = relationship(
        'CoinBot', back_populates='token_utility', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Value_accrual_mechanisms(Base):
    __tablename__ = 'value_accrual_mechanisms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    mechanism = Column(String)
    description = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    coin_bot = relationship(
        'CoinBot', back_populates='value_accrual_mechanisms', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Revenue_model(Base):
    __tablename__ = 'revenue_model'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    analized_revenue = Column(String)
    fees_1ys = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    coin_bot = relationship(
        'CoinBot', back_populates='revenue_model', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Hacks(Base):
    __tablename__ = 'hacks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    hack_name = Column(String)
    date = Column(String)
    incident_description = Column(String)
    consequences = Column(String)
    mitigation_measure = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    coin_bot = relationship('CoinBot', back_populates='hacks', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# -----------------------   NEW COMPETITOR TABLE ------------------------------------------------


class Competitor(Base):
    __tablename__ = 'competitor'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    token = Column(String)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='competitor', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

# ------------------------------------------------------------------------------------------------------------


class DApps(Base):
    __tablename__ = 'dapps'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    dapps = Column(String)
    description = Column(String)
    tvl = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    coin_bot = relationship('CoinBot', back_populates='dapps', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Upgrades(Base):
    __tablename__ = 'upgrades'
    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    event = Column(String)
    date = Column(String)
    event_overview = Column(String)
    impact = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)
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


# --------- Populate or update the sources -------------------------
with session:
    try:
        if not session.query(Site).first():
            with open(f'{ROOT_DIRECTORY}/models/data.json', 'r', encoding="utf8") as data_file:
                config = json.load(data_file)

                for index, item in enumerate(config):
                    main_keyword = item['main_keyword']
                    alias = item['alias']
                    coins = item['coins']

                    for index, coin in enumerate(coins):
                        coin_keyword = coin['coin_keyword'].casefold()
                        coin_bot = session.query(CoinBot).filter_by(bot_name=coin_keyword).first()
                        
                        if coin_bot is None:
                            print(f"No CoinBot found for keyword: {coin_keyword}")
                            continue  # Skip this coin since there's no corresponding CoinBot

                        print("Bot ID: ", coin_bot.bot_id)
                        print("Bot name: ", coin_keyword)
                        keywords = coin['keywords']
                        sites = coin['sites']
                        black_list = coin['black_list']

                        for index, site_data in enumerate(sites):
                            site = Site(
                                site_name=str(site_data['website_name']),
                                base_url=str(site_data['base_url']).casefold(),
                                data_source_url=str(site_data['site']).capitalize(),
                                is_URL_complete=site_data['is_URL_complete'],
                                main_container=str(site_data['main_container']),
                                coin_bot_id=coin_bot.bot_id
                            )
                            session.add(site)
                        session.commit()
                print('-----Sources updated-----')

    except Exception as e:
        print(f"Error found populating the sources: {str(e)}")


# ------------- Populate the database with all the data.json ---------------------------
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
                            new_coin.keywords.append(
                                Keyword(word=keyword.casefold()))

                        for word in black_list:
                            new_coin.blacklist.append(
                                Blacklist(word=word.casefold()))

                        for site_data in sites:
                            site = Site(
                                site_name=str(site_data['website_name']),
                                base_url=str(site_data['base_url']).casefold(),
                                data_source_url=str(
                                    site_data['site']).capitalize(),
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


# --------- CREATE AN ADMIN USER ----------------------------------------

try:
    if not session.query(Admin).first():
        new_admin = Admin(mail='team@novatide.io',
                          username='novatideteam', password='Novatide2023!')
        session.add(new_admin)
        session.commit()
        print('---- Admin user created------')
    else:
        print('---- Admin user already exist------')
except Exception as e:
    print(f'---Error creating the admin user: {str(e)}---')
    session.rollback()
