from sqlalchemy import (
    Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Float, 
    create_engine, Text, Enum, Date, DateTime, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from pathlib import Path
import json
import os
import uuid



load_dotenv()

DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(db_url, pool_size=30, max_overflow=20)


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
    """
    Represents a user in the system.

    This class defines the structure for storing user information, including
    authentication details and related purchased plans.

    Attributes:
        user_id (int): The primary key for the user.
        nickname (str): The user's nickname or display name.
        email (str): The user's email address.
        email_verified (str): Indicates if the user's email has been verified.
        picture (str): URL or path to the user's profile picture.
        auth0id (str): The user's Auth0 ID for authentication.
        provider (str): The authentication provider used by the user.
        created_at (datetime): Timestamp of when the user was created.
        updated_at (datetime): Timestamp of the last update to the user record.
        purchased_plans (relationship): Relationship to the user's purchased plans.
    """
    __tablename__ = 'user_table'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String)
    email = Column(String)
    email_verified = Column(String)
    picture = Column(String)
    auth0id = Column(String)
    provider = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    purchased_plans = relationship('PurchasedPlan', back_populates='user', lazy=True)
    
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class PurchasedPlan(Base):
    """
    Represents a purchased plan associated with a user.

    This class defines the structure for storing information about plans
    purchased by users, including pricing and subscription status.

    Attributes:
        product_id (int): The primary key for the purchased plan.
        reference_name (str): The name or reference of the purchased plan.
        price (int): The price of the plan.
        is_subscribed (bool): Indicates if the user is currently subscribed to this plan.
        user_id (int): Foreign key referencing the associated User.
        created_at (datetime): Timestamp of when the plan was purchased.
        updated_at (datetime): Timestamp of the last update to the plan record.
        user (relationship): Relationship to the associated User.
    """
    __tablename__ = 'purchased_plan'

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    reference_name = Column(String)
    price = Column(Integer)
    is_subscribed = Column(Boolean)
    user_id = Column(Integer, ForeignKey('user_table.user_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship('User', back_populates='purchased_plans')
    
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Category(Base):
    """
    Represents a category for organizing CoinBots.

    This class defines the structure for storing category information,
    including visual elements and activity status.

    Attributes:
        category_id (int): The primary key for the category.
        category (str): The main identifier for the category.
        category_name (str): A user-friendly name for the category.
        time_interval (int): The time interval associated with the category.
        is_active (bool): Indicates if the category is currently active.
        border_color (str): The color used for visual representation of the category.
        icon (str): The icon or image associated with the category.
        created_at (datetime): Timestamp of when the category was created.
        updated_at (datetime): Timestamp of the last update to the category record.
        coin_bot (relationship): Relationship to the associated CoinBots.
    """
    __tablename__ = 'category'

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, nullable=False)
    category_name = Column(String)
    time_interval = Column(Integer, default=50)
    is_active = Column(Boolean, default=False)
    border_color = Column(String, default='No Color')
    icon = Column(String, default='No Image')
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='category', lazy=True)
    
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns} 

class CoinBot(Base):
    """
    Represents a CoinBot in the system.

    This class defines the structure for storing CoinBot information, including
    its name, image, category, and various relationships to other entities.

    Attributes:
        bot_id (int): The primary key for the CoinBot.
        bot_name (str): The name of the CoinBot.
        image (str): URL or path to the CoinBot's image.
        category_id (int): Foreign key referencing the associated Category.
        created_at (datetime): Timestamp of when the CoinBot was created.
        updated_at (datetime): Timestamp of the last update to the CoinBot record.
        chart (relationship): Relationship to associated Chart objects.
        alerts (relationship): Relationship to associated Alert objects.
        sites (relationship): Relationship to associated Site objects.
        keywords (relationship): Relationship to associated Keyword objects.
        blacklist (relationship): Relationship to associated Blacklist objects.
        article (relationship): Relationship to associated Article objects.
        analysis (relationship): Relationship to associated Analysis objects.
        top_story (relationship): Relationship to associated TopStory objects.
        category (relationship): Relationship to the associated Category.
        introduction (relationship): Relationship to the associated Introduction.
        tokenomics (relationship): Relationship to associated Tokenomics objects.
        token_distribution (relationship): Relationship to associated Token_distribution objects.
        token_utility (relationship): Relationship to associated Token_utility objects.
        value_accrual_mechanisms (relationship): Relationship to associated Value_accrual_mechanisms objects.
        competitor (relationship): Relationship to associated Competitor objects.
        revenue_model (relationship): Relationship to associated Revenue_model objects.
        hacks (relationship): Relationship to associated Hacks objects.
        dapps (relationship): Relationship to associated DApps objects.
        upgrades (relationship): Relationship to associated Upgrades objects.
        narrative_trading (relationship): Relationship to associated NarrativeTrading objects.
    """
    __tablename__ = 'coin_bot'

    bot_id = Column(Integer, primary_key=True, autoincrement=True)
    bot_name = Column(String)
    image = Column(String, default='No Image')
    category_id = Column(Integer, ForeignKey('category.category_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

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
    tokenomics = relationship("Tokenomics", back_populates="coin_bot", lazy=True)
    token_distribution = relationship("Token_distribution", back_populates="coin_bot", lazy=True)
    token_utility = relationship("Token_utility", back_populates="coin_bot", lazy=True)
    value_accrual_mechanisms = relationship("Value_accrual_mechanisms", back_populates="coin_bot", lazy=True)
    competitor = relationship("Competitor", back_populates="coin_bot", lazy=True)
    revenue_model = relationship('Revenue_model', back_populates='coin_bot', lazy=True)
    hacks = relationship('Hacks', back_populates='coin_bot', lazy=True)
    dapps = relationship('DApps', back_populates='coin_bot', lazy=True)
    upgrades = relationship('Upgrades', back_populates='coin_bot', lazy=True)
    narrative_trading = relationship('NarrativeTrading', back_populates='coin_bot', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Keyword(Base):
    """
    Represents a keyword associated with a CoinBot.

    This class defines the structure for storing keyword information,
    including the word itself and its association with a CoinBot.

    Attributes:
        keyword_id (int): The primary key for the keyword.
        word (str): The keyword text.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        created_at (datetime): Timestamp of when the keyword was created.
        updated_at (datetime): Timestamp of the last update to the keyword record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'keyword'

    keyword_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='keywords', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Used_keywords(Base):
    """
    Represents used keywords associated with articles and CoinBots.

    This class defines the structure for storing information about keywords used in articles,
    including the article content, date, URL, and associated CoinBot.

    Attributes:
        id (int): The primary key for the used keywords record.
        article_content (str): The content of the associated article.
        article_date (str): The date of the article.
        article_url (str): The URL of the article.
        keywords (str): The keywords used in the article.
        source (str): The source of the article.
        article_id (int): Foreign key referencing the associated Article.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        coin_bot (relationship): Relationship to the associated CoinBot.
        article (relationship): Relationship to the associated Article.
    """
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
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    coin_bot = relationship('CoinBot', backref='used_keywords')
    # article = relationship('Article', backref='used_keywords') 
    article = relationship('Article', back_populates='used_keywords')
    
    
    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Site(Base):
    """
    Represents a website associated with a CoinBot.

    This class defines the structure for storing information about websites,
    including their URLs, data sources, and associated CoinBot.

    Attributes:
        site_id (int): The primary key for the site.
        site_name (str): The name of the site.
        base_url (str): The base URL of the site.
        data_source_url (str): The URL of the data source.
        is_URL_complete (bool): Indicates if the URL is complete.
        main_container (str): The main container element for scraping.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        created_at (datetime): Timestamp of when the site was created.
        updated_at (datetime): Timestamp of the last update to the site record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'site'

    site_id = Column(Integer, primary_key=True, autoincrement=True)
    site_name = Column(String)
    base_url = Column(String)
    data_source_url = Column(String)
    is_URL_complete = Column(Boolean)
    main_container = Column(String)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='sites', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Blacklist(Base):
    """
    Represents a blacklisted word associated with a CoinBot.

    This class defines the structure for storing blacklisted words,
    which are used to filter out unwanted content for a CoinBot.

    Attributes:
        blacklist_id (int): The primary key for the blacklisted word.
        word (str): The blacklisted word.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        created_at (datetime): Timestamp of when the blacklist entry was created.
        updated_at (datetime): Timestamp of the last update to the blacklist entry.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'blacklist'

    blacklist_id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='blacklist', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Alert(Base):
    """
    Represents an alert associated with a CoinBot.

    This class defines the structure for storing alert information, including
    the alert name, message, symbol, and price.

    Attributes:
        alert_id (int): The primary key for the alert.
        alert_name (str): The name of the alert.
        alert_message (str): The message associated with the alert.
        symbol (str): The symbol of the coin/token.
        price (float): The price associated with the alert.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        created_at (datetime): Timestamp of when the alert was created.
        updated_at (datetime): Timestamp of the last update to the alert record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'alert'

    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    alert_name = Column(String)
    alert_message = Column(String)
    symbol = Column(String)
    price = Column(Float)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='alerts', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Article(Base):
    """
    Represents an article associated with a CoinBot.

    This class defines the structure for storing article information, including
    the date, title, URL, and summary.

    Attributes:
        article_id (int): The primary key for the article.
        date (str): The date of the article.
        title (str): The title of the article.
        url (str): The URL of the article.
        summary (str): A summary of the article.
        created_at (datetime): Timestamp of when the article was created.
        updated_at (datetime): Timestamp of the last update to the article record.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        coin_bot (relationship): Relationship to the associated CoinBot.
        images (relationship): Relationship to associated ArticleImage objects.
        used_keywords (relationship): Relationship to associated Used_keywords objects.
    """
    __tablename__ = 'article'

    article_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)
    title = Column(String)
    url = Column(String)
    summary = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='article', lazy=True)
    images = relationship('ArticleImage', back_populates='article', lazy=True)
    used_keywords = relationship('Used_keywords', back_populates='article', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class ArticleImage(Base):
    """
    Represents an image associated with an article.

    This class defines the structure for storing image information related to articles.

    Attributes:
        image_id (int): The primary key for the image.
        image (str): The URL or path to the image.
        created_at (datetime): Timestamp of when the image was created.
        updated_at (datetime): Timestamp of the last update to the image record.
        article_id (int): Foreign key referencing the associated Article.
        article (relationship): Relationship to the associated Article.
    """
    __tablename__ = 'article_image'

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    article_id = Column(Integer, ForeignKey('article.article_id'), nullable=False)

    article = relationship('Article', back_populates='images')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class TopStory(Base):
    """
    Represents a top story associated with a CoinBot.

    This class defines the structure for storing top story information,
    including the story date, summary, and associated images.

    Attributes:
        top_story_id (int): The primary key for the top story.
        story_date (str): The date of the story.
        summary (str): A summary of the top story.
        created_at (datetime): Timestamp of when the top story was created.
        updated_at (datetime): Timestamp of the last update to the top story record.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        coin_bot (relationship): Relationship to the associated CoinBot.
        images (relationship): Relationship to associated TopStoryImage objects.
    """
    __tablename__ = 'top_story'

    top_story_id = Column(Integer, primary_key=True, autoincrement=True)
    story_date = Column(String)
    summary = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)

    coin_bot = relationship('CoinBot', back_populates='top_story', lazy=True)
    images = relationship('TopStoryImage', back_populates='top_story')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class TopStoryImage(Base):
    """
    Represents an image associated with a top story.

    This class defines the structure for storing image information related to top stories.

    Attributes:
        image_id (int): The primary key for the image.
        image (str): The URL or path to the image.
        created_at (datetime): Timestamp of when the image was created.
        updated_at (datetime): Timestamp of the last update to the image record.
        top_story_id (int): Foreign key referencing the associated TopStory.
        top_story (relationship): Relationship to the associated TopStory.
    """
    __tablename__ = 'top_story_image'

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    top_story_id = Column(Integer, ForeignKey('top_story.top_story_id'), nullable=False)

    top_story = relationship('TopStory', back_populates='images')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Analysis(Base):
    """
    Represents an analysis associated with a CoinBot.

    This class defines the structure for storing analysis information,
    including the analysis content, category, and associated images.

    Attributes:
        analysis_id (int): The primary key for the analysis.
        analysis (str): The content of the analysis.
        created_at (datetime): Timestamp of when the analysis was created.
        updated_at (datetime): Timestamp of the last update to the analysis record.
        category_name (str): The name of the category for this analysis.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        images (relationship): Relationship to associated AnalysisImage objects.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'analysis'

    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    analysis = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    category_name = Column(String)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)

    images = relationship('AnalysisImage', back_populates='analysis')
    coin_bot = relationship('CoinBot', back_populates='analysis', lazy=True)

    def to_dict(self):
        return {
            'analysis_id': self.analysis_id,
            'analysis': self.analysis,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'category_name': self.category_name
        }

class AnalysisImage(Base):
    """
    Represents an image associated with an analysis.

    This class defines the structure for storing image information related to analyses.

    Attributes:
        image_id (int): The primary key for the image.
        image (str): The URL or path to the image.
        created_at (datetime): Timestamp of when the image was created.
        updated_at (datetime): Timestamp of the last update to the image record.
        analysis_id (int): Foreign key referencing the associated Analysis.
        analysis (relationship): Relationship to the associated Analysis.
    """
    __tablename__ = 'analysis_image'

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    analysis_id = Column(Integer, ForeignKey('analysis.analysis_id'), nullable=False)

    analysis = relationship('Analysis', back_populates='images')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class AnalyzedArticle(Base):
    """
    Represents an analyzed article.

    This class defines the structure for storing information about articles
    that have been analyzed, including their source and analysis status.

    Attributes:
        article_id (int): The primary key for the analyzed article.
        source (str): The source of the article.
        url (str): The URL of the article.
        is_analyzed (bool): Indicates whether the article has been analyzed.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
    """
    __tablename__ = 'analyzed_article'

    article_id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String)
    url = Column(String)
    is_analyzed = Column(Boolean)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class NarrativeTrading(Base):
    """
    Represents narrative trading information associated with a CoinBot.

    This class defines the structure for storing narrative trading data,
    including the narrative content and associated category.

    Attributes:
        narrative_trading_id (int): The primary key for the narrative trading record.
        narrative_trading (str): The content of the narrative trading.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        category_name (str): The name of the category associated with this narrative.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'narrative_trading'

    narrative_trading_id = Column(Integer, primary_key=True, autoincrement=True)
    narrative_trading = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    category_name = Column(String, nullable=False)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    test = Column(String, default=False)

    coin_bot = relationship('CoinBot', back_populates='narrative_trading', lazy=True)

    def to_dict(self):
        return {
            'narrative_trading_id': self.narrative_trading_id,
            'narrative_trading': self.narrative_trading,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'category_name': self.category_name
        }

class Chart(Base):
    """
    Represents a chart associated with a CoinBot.

    This class defines the structure for storing chart data, including support and resistance levels,
    token information, and chart metadata.

    Attributes:
        chart_id (int): The primary key for the chart record.
        support_1 (float): The first support level.
        support_2 (float): The second support level.
        support_3 (float): The third support level.
        support_4 (float): The fourth support level.
        resistance_1 (float): The first resistance level.
        resistance_2 (float): The second resistance level.
        resistance_3 (float): The third resistance level.
        resistance_4 (float): The fourth resistance level.
        token (str): The token or coin symbol.
        pair (str): The trading pair (e.g., "BTC/USD").
        temporality (str): The time frame of the chart (e.g., "1h", "4h", "1d").
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        created_at (datetime): Timestamp of when the chart record was created.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
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
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='chart', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# -------------------------------- FUNDAMENTALS ----------------------------

class Introduction(Base):
    """
    Represents an introduction associated with a CoinBot.

    This class defines the structure for storing introductory information about a coin or token,
    including content, website, whitepaper, and dynamic status.

    Attributes:
        id (int): The primary key for the introduction record.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        content (str): The main content of the introduction.
        website (str): The official website URL of the coin or token.
        whitepaper (str): The URL or reference to the coin's whitepaper.
        dynamic (bool): Indicates if the introduction information is dynamically updated.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'introduction'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    content = Column(String)
    website = Column(String)
    whitepaper = Column(String)
    dynamic = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='introduction', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Tokenomics(Base):
    """
    Represents tokenomics information associated with a CoinBot.

    This class defines the structure for storing tokenomics data, including
    supply information, token details, and dynamic status.

    Attributes:
        id (int): The primary key for the tokenomics record.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        token (str): The name or symbol of the token.
        total_supply (str): The total supply of the token.
        circulating_supply (str): The current circulating supply of the token.
        percentage_circulating_supply (str): The percentage of total supply in circulation.
        max_supply (str): The maximum possible supply of the token.
        supply_model (str): Description of the token's supply model.
        dynamic (bool): Indicates if the tokenomics information is dynamically updated.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'tokenomics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    token = Column(String)
    total_supply = Column(String)
    circulating_supply = Column(String)
    percentage_circulating_supply = Column(String)
    max_supply = Column(String)
    supply_model = Column(String)
    dynamic = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='tokenomics', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Token_distribution(Base):
    """
    Represents token distribution information associated with a CoinBot.

    This class defines the structure for storing token distribution data,
    including holder categories and their respective percentages.

    Attributes:
        id (int): The primary key for the token distribution record.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        holder_category (str): The category of token holders (e.g., "Team", "Investors").
        percentage_held (str): The percentage of tokens held by this category.
        dynamic (bool): Indicates if the distribution information is dynamically updated.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'token_distribution'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    holder_category = Column(String)
    percentage_held = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='token_distribution', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Token_utility(Base):
    """
    Represents token utility information associated with a CoinBot.

    This class defines the structure for storing token utility data,
    including various applications and descriptions of the token's use cases.

    Attributes:
        id (int): The primary key for the token utility record.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        token_application (str): The specific application or use case of the token.
        description (str): A description of the token's application or utility.
        dynamic (bool): Indicates if the utility information is dynamically updated.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'token_utility'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    token_application = Column(String)
    description = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='token_utility', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Value_accrual_mechanisms(Base):
    """
    Represents value accrual mechanisms associated with a CoinBot.

    This class defines the structure for storing information about value accrual mechanisms,
    including the mechanism description and its dynamic status.

    Attributes:
        id (int): The primary key for the value accrual mechanism.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        mechanism (str): The name or type of the value accrual mechanism.
        description (str): A description of the value accrual mechanism.
        dynamic (bool): Indicates if the mechanism information is dynamically updated.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'value_accrual_mechanisms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    mechanism = Column(String)
    description = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='value_accrual_mechanisms', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Revenue_model(Base):
    """
    Represents a revenue model associated with a CoinBot.

    This class defines the structure for storing information about revenue models,
    including analyzed revenue, fees, and its dynamic status.

    Attributes:
        id (int): The primary key for the revenue model.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        analized_revenue (str): The analyzed revenue information.
        fees_1ys (str): The fees for the first year.
        dynamic (bool): Indicates if the revenue model information is dynamically updated.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'revenue_model'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    analized_revenue = Column(String)
    fees_1ys = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='revenue_model', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Hacks(Base):
    """
    Represents a hack or security incident associated with a CoinBot.

    This class defines the structure for storing information about hacks or security incidents,
    including details about the incident, its consequences, and mitigation measures.

    Attributes:
        id (int): The primary key for the hack record.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        hack_name (str): The name or identifier of the hack.
        date (str): The date of the hack incident.
        incident_description (str): A description of the hack incident.
        consequences (str): The consequences of the hack.
        mitigation_measure (str): Measures taken to mitigate the hack's impact.
        dynamic (bool): Indicates if the hack information is dynamically updated.
        created_at (datetime): Timestamp of when the record was created.
        updated_at (datetime): Timestamp of the last update to the record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'hacks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    hack_name = Column(String)
    date = Column(String)
    incident_description = Column(String)
    consequences = Column(String)
    mitigation_measure = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='hacks', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

# -----------------------   NEW COMPETITOR TABLE ------------------------------------------------


class Competitor(Base):
    """
    Represents a competitor associated with a CoinBot.

    This class defines the structure for storing information about competitors,
    including their token, key-value pairs, and dynamic status.

    Attributes:
        id (int): The primary key for the competitor.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        token (str): The token or identifier of the competitor.
        key (str): A key representing a specific attribute of the competitor.
        value (str): The value associated with the key.
        dynamic (bool): Indicates if the competitor information is dynamically updated.
        created_at (datetime): Timestamp of when the competitor record was created.
        updated_at (datetime): Timestamp of the last update to the competitor record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'competitor'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    token = Column(String)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='competitor', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class DApps(Base):
    """
    Represents a decentralized application (DApp) associated with a CoinBot.

    This class defines the structure for storing information about DApps,
    including their description, Total Value Locked (TVL), and dynamic status.

    Attributes:
        id (int): The primary key for the DApp.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        dapps (str): The name or identifier of the DApp.
        description (str): A description of the DApp.
        tvl (str): The Total Value Locked in the DApp.
        dynamic (bool): Indicates if the DApp information is dynamically updated.
        created_at (datetime): Timestamp of when the DApp record was created.
        updated_at (datetime): Timestamp of the last update to the DApp record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'dapps'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    dapps = Column(String)
    description = Column(String)
    tvl = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='dapps', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Upgrades(Base):
    """
    Represents an upgrade event associated with a CoinBot.

    This class defines the structure for storing information about upgrade events,
    including the event details, date, overview, impact, and dynamic status.

    Attributes:
        id (int): The primary key for the upgrade event.
        coin_bot_id (int): Foreign key referencing the associated CoinBot.
        event (str): The name or description of the upgrade event.
        date (str): The date of the upgrade event.
        event_overview (str): An overview of the upgrade event.
        impact (str): The impact of the upgrade event.
        dynamic (bool): Indicates if the upgrade information is dynamically updated.
        created_at (datetime): Timestamp of when the upgrade record was created.
        updated_at (datetime): Timestamp of the last update to the upgrade record.
        coin_bot (relationship): Relationship to the associated CoinBot.
    """
    __tablename__ = 'upgrades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot.bot_id'), nullable=False)
    event = Column(String)
    date = Column(String)
    event_overview = Column(String)
    impact = Column(String)
    dynamic = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    coin_bot = relationship('CoinBot', back_populates='upgrades', lazy=True)

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
session = Session()



ROOT_DIRECTORY = Path(__file__).parent.resolve()


# ------------- POPULATE THE DB WITH DATA.JSON -------------------

def populate_database():
    """
    Populate the database with initial data from a JSON file.
    This function creates categories, coins, keywords, blacklists, and sites.
    """
    session = Session()
    
    try:
        # Check if the database is already populated
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
        else:
            print('-----Database is already populated. Skipping population process-----')

    except SQLAlchemyError as e:
        print(f'---Database error while populating the database: {str(e)}---')
        session.rollback()
    except json.JSONDecodeError as e:
        print(f'---Error decoding JSON file: {str(e)}---')
        session.rollback()
    except FileNotFoundError as e:
        print(f'---Error: JSON file not found: {str(e)}---')
    except Exception as e:
        print(f'---Unexpected error while populating the database: {str(e)}---')
        session.rollback()
    finally:
        session.close()


# Populates the DB
populate_database()

# ------------- CREATE AN ADMIN USER -----------------------------

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
