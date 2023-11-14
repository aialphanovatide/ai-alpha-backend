from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime


ARTICLE_MODEL = declarative_base()

# data of each article
class ARTICLE(ARTICLE_MODEL):
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True)
    title = Column(String)  
    content = Column(String)   
    date = Column(String)   
    url = Column(String)   
    website_name = Column(String)
    images = relationship("IMAGE", backref="article", cascade="all, delete-orphan")

class IMAGE(ARTICLE_MODEL):
    __tablename__ = 'image'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('article.id'))
    url = Column(String) 


class ANALIZED_ARTICLE(ARTICLE_MODEL):
    __tablename__ = 'is_article_analized'

    id = Column(Integer, primary_key=True)
    source = Column(String) 
    url = Column(String) 
    is_analized = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow) 



