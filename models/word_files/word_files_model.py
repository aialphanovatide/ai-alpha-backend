from sqlalchemy import Column, Integer, String, LargeBinary
from config import Base


# word files
class Files(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    paragraphs = Column(String) 
    embeddings = Column(LargeBinary)