from sqlalchemy import (
    Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Float, 
    create_engine, Text, Enum, Date, DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from pathlib import Path
import json
import os
import uuid


# Load environment variables
load_dotenv()

# Database connection details
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

# Construct database URL
db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

# Create engine with connection pool settings
engine = create_engine(db_url, pool_size=30, max_overflow=20)

# Create base class for declarative models
Base = declarative_base()

# _________________________ AI ALPHA DASHBOARD TABLES _______________________________________


class Admin(Base):   
    """
    Represents an admin user in the system.

    This class defines the structure and behavior of admin users, including
    their authentication details and timestamps for record-keeping.

    Attributes:
        admin_id (int): The primary key for the admin.
        uuid (str): A unique identifier for the admin.
        email (str): The admin's email address (unique).
        username (str): The admin's username (unique).
        _password (str): The hashed password of the admin.
        created_at (datetime): Timestamp of when the admin was created.
        updated_at (datetime): Timestamp of the last update to the admin record.
        roles (relationship): Relationship to the roles assigned to this admin.
    """
    __tablename__ = 'admins'
    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    _password = Column('password', String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    roles = relationship('Role', secondary='admin_roles', back_populates='admins')

    def to_dict(self):
        """
        Convert the admin object to a dictionary.

        Returns:
            dict: A dictionary representation of the admin.
        """
        return {
            'admin_id': self.admin_id,
            'uuid': self.uuid,
            'username': self.username,
            'email': self.email,
            'roles': [role.name for role in self.roles],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @property
    def password(self):
        """
        Getter for password. Raises an error if attempted to be read.

        Raises:
            AttributeError: Always raised when this property is accessed.
        """
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """
        Setter for password. Hashes the password before storing.

        Args:
            password (str): The plain text password to be hashed and stored.
        """
        self._password = generate_password_hash(password)

    def verify_password(self, password):
        """
        Verify a given password against the stored hash.

        Args:
            password (str): The password to verify.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        return check_password_hash(self._password, password)
    
class Role(Base):
    """
    Represents a role in the system.

    This class defines the structure of roles that can be assigned to admins.

    Attributes:
        id (int): The primary key for the role.
        name (str): The name of the role (unique).
        description (str): A description of the role.
        admins (relationship): Relationship to the admins assigned this role.
    """
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))

    admins = relationship('Admin', secondary='admin_roles', back_populates='roles')

class AdminRole(Base):
    """
    Represents the many-to-many relationship between admins and roles.

    This class serves as an association table linking admins to their roles.

    Attributes:
        admin_id (int): Foreign key referencing the admin.
        role_id (int): Foreign key referencing the role.
    """
    __tablename__ = 'admin_roles'

    admin_id = Column(Integer, ForeignKey('admins.admin_id'), primary_key=True, nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True, nullable=False)


# __________________________ AI ALPHA APP TABLES __________________________________________


class User(Base):
    __tablename__ = 'user_table'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String)
    email = Column(String)
    email_verified = Column(String)
    picture = Column(String)
    auth0id = Column(String)
    provider = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    update_at = Column(TIMESTAMP, default=datetime.now)
    purchased_plans = relationship(
        'PurchasedPlan', back_populates='user', lazy=True)
    
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


class PurchasedPlan(Base):
    __tablename__ = 'purchased_plan'
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    reference_name = Column(String)
    price = Column(Integer)
    is_subscribed = Column(Boolean)
    user_id = Column(Integer, ForeignKey('user_table.user_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

    user = relationship('User', back_populates='purchased_plans')
    
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


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

    coin_bot = relationship('CoinBot', back_populates='category', lazy=True)
    
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


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

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


class Keyword(Base):
    __tablename__ = 'keyword'
    keyword_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='keywords', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 



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

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


class Blacklist(Base):
    __tablename__ = 'blacklist'
    blacklist_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
    coin_bot_id = Column(Integer, ForeignKey(
        'coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

    coin_bot = relationship('CoinBot', back_populates='blacklist', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


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

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


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

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 
   

class ArticleImage(Base):
    __tablename__ = 'article_image'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    article_id = Column(Integer, ForeignKey(
        'article.article_id'), nullable=False)
    article = relationship('Article', back_populates='images')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


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

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


class TopStoryImage(Base):
    __tablename__ = 'top_story_image'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    top_story_id = Column(Integer, ForeignKey(
        'top_story.top_story_id'), nullable=False)

    top_story = relationship('TopStory', back_populates='images')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


class Analysis(Base):
    __tablename__ = 'analysis'
    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    analysis = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    category_name = Column(String)
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

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


class AnalyzedArticle(Base):
    __tablename__ = 'analyzed_article'
    article_id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String)
    url = Column(String)
    is_analyzed = Column(Boolean)
    created_at = Column(TIMESTAMP, default=datetime.now)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 

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

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 


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


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
session = Session()

ROOT_DIRECTORY = Path(__file__).parent.resolve()


# ------------- Populate the database with all the data from data.json ---------------------------
with session:
    try:
        if not session.query(Category).first() and not session.query(Site).first():
            with open(f'{ROOT_DIRECTORY}/models/data.json', 'r', encoding="utf8") as data_file:
                config = json.load(data_file)

                for item in config:
                    main_keyword = item['main_keyword']
                    alias = item['alias']
                    coins = item['coins']

                    new_category = Category(
                        category=main_keyword,
                        category_name=alias,
                        icon=item['icon'],
                        border_color=item['borderColor'],
                    )

                    for coin in coins:
                        coin_keyword = coin['coin_keyword'].casefold()
                        keywords = coin['keywords']
                        sites = coin['sites']
                        black_list = coin['black_list']

                        new_coin = CoinBot(bot_name=coin_keyword)
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
                        print(f'-----CoinBot data saved for {coin_keyword}-----')

                    session.add(new_category)
                    print(f'-----Category {main_keyword} populated-----')
                    
                session.commit()
                print('-----All data successfully populated-----')

    except Exception as e:
        print(f'---Error populating the database: {str(e)}---')
        session.rollback()


# --------- CREATE AN ADMIN USER ----------------------------------------

def init_superadmin():
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

    if not all([ADMIN_EMAIL, ADMIN_USERNAME, ADMIN_PASSWORD]):
        print("---- Error: Admin credentials not fully provided in environment variables ----")
        return

    session = Session()

    try:
        # Check if the admin user already exists
        existing_admin = session.query(Admin).filter_by(username=ADMIN_USERNAME).first()
        
        if not existing_admin:
            # Create new admin
            new_admin = Admin(
                email=ADMIN_EMAIL,
                username=ADMIN_USERNAME,
                password=ADMIN_PASSWORD
            )
            session.add(new_admin)
            session.flush()  # This will populate the admin_id

            # Check if superadmin role exists, create if not
            superadmin_role = session.query(Role).filter_by(name='superadmin').first()
            if not superadmin_role:
                superadmin_role = Role(name='superadmin', description='Super Administrator')
                session.add(superadmin_role)
                session.flush()  # This will populate the role_id

            # Assign superadmin role to the new admin
            admin_role = AdminRole(admin_id=new_admin.admin_id, role_id=superadmin_role.id)
            session.add(admin_role)

            session.commit()
            print('---- Superadmin user created successfully ----')
        else:
            print('---- Superadmin user already exists ----')

    except SQLAlchemyError as e:
        print(f'---- Database error creating the superadmin user: {str(e)} ----')
        session.rollback()
    except Exception as e:
        print(f'---- Unexpected error creating the superadmin user: {str(e)} ----')
        session.rollback()
    finally:
        session.close()


# Create SuperAdmin
init_superadmin()
