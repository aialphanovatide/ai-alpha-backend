from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime


SCRAPPER_MODEL = declarative_base()

# data of all sources
class SCRAPPING_DATA(SCRAPPER_MODEL):
    __tablename__ = 'scrapping_data'

    id = Column(Integer, primary_key=True)
    main_keyword = Column(String)
    keywords = relationship("KEWORDS", cascade="all, delete-orphan")
    sites = relationship("SITES", cascade="all, delete-orphan")
    blacklist = relationship("BLACKLIST", cascade="all, delete-orphan")
    created_at = Column(DateTime, default=datetime.utcnow) 

class KEWORDS(SCRAPPER_MODEL): 
    __tablename__ = 'keyword'

    id = Column(Integer, primary_key=True)
    keyword_info_id = Column(Integer, ForeignKey('scrapping_data.id'), nullable=False)
    keyword = Column(String)  
    created_at = Column(DateTime, default=datetime.utcnow) 

class BLACKLIST(SCRAPPER_MODEL): 
    __tablename__ = 'blacklist'

    id = Column(Integer, primary_key=True)
    keyword_info_id = Column(Integer, ForeignKey('scrapping_data.id'), nullable=False)
    black_Word = Column(String)  
    created_at = Column(DateTime, default=datetime.utcnow) 

class SITES(SCRAPPER_MODEL):
    __tablename__ = 'sites'

    id = Column(Integer, primary_key=True)
    keyword_info_id = Column(Integer, ForeignKey('scrapping_data.id'), nullable=False)
    site = Column(String)  
    base_url = Column(String)  
    website_name = Column(String)  
    is_URL_complete = Column(Boolean)  
    main_container = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow) 


