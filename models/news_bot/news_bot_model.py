from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from config import Base, session
from datetime import datetime
from pathlib import Path
import json

ROOT_DIRECTORY = Path(__file__).parent.resolve()


#data of all sources
class SCRAPPING_DATA(Base):
    __tablename__ = 'scrapping_data'

    id = Column(Integer, primary_key=True)
    main_keyword = Column(String)
    keywords = relationship("KEWORDS", cascade="all, delete-orphan")
    sites = relationship("SITES", cascade="all, delete-orphan")
    blacklist = relationship("BLACKLIST", cascade="all, delete-orphan")
    created_at = Column(DateTime, default=datetime.utcnow) 

class KEWORDS(Base): 
    __tablename__ = 'keyword'

    id = Column(Integer, primary_key=True)
    keyword_info_id = Column(Integer, ForeignKey('scrapping_data.id'), nullable=False)
    keyword = Column(String)  
    created_at = Column(DateTime, default=datetime.utcnow) 

class BLACKLIST(Base): # son palabras que no deberian pasar el filtro en el titulo o contenido.
    __tablename__ = 'blacklist'

    id = Column(Integer, primary_key=True)
    keyword_info_id = Column(Integer, ForeignKey('scrapping_data.id'), nullable=False)
    black_Word = Column(String)  
    created_at = Column(DateTime, default=datetime.utcnow) 

class SITES(Base):
    __tablename__ = 'sites'

    id = Column(Integer, primary_key=True)
    keyword_info_id = Column(Integer, ForeignKey('scrapping_data.id'), nullable=False)
    site = Column(String)  
    base_url = Column(String)  
    website_name = Column(String)  
    is_URL_complete = Column(Boolean)  
    created_at = Column(DateTime, default=datetime.utcnow) 


# Populates the sites and keyword tables
if not session.query(SCRAPPING_DATA).first():

    with open(f'{ROOT_DIRECTORY}\summary_bot\data.json', 'r') as data_file:
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
                is_URL_complete=site_data['is_URL_complete']
            )
            scrapping_data.sites.append(site)

        
        session.add(scrapping_data)

    print('Initial site data saved to db')
    session.commit()
