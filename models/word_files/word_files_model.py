from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base

FILES_MODEL = declarative_base()

# word files
class Files(FILES_MODEL):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    paragraphs = Column(String) 
    embeddings = Column(LargeBinary)