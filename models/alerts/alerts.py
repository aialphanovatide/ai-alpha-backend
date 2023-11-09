from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


ALERT_MODEL = declarative_base()

class ALERT(ALERT_MODEL):
    __tablename__ = 'alert'

    alert_id = Column(Integer, primary_key=True)
    alert_name = Column(String)
    alert_message = Column(String)
    symbol = Column(String)
    price = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow) 