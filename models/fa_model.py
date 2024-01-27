from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Fa = declarative_base()

class CoinBot(Fa):
    __tablename__ = 'coin_bot_test'
    bot_id = Column(Integer, primary_key=True, autoincrement=True)
    bot_name = Column(String)

    introduction = relationship("Introduction", back_populates="coin_bot_test")
    tokenomics = relationship("Tokenomics", back_populates="coin_bot_test")
    token_distribution = relationship("Token_distribution", back_populates="coin_bot_test")
    token_utility = relationship("Token_utility", back_populates="coin_bot_test")
    value_accrual_mechanisms = relationship("Value_accrual_mechanisms", back_populates="coin_bot_test")
    competitor = relationship("Competitor", back_populates="coin_bot_test")

class Introduction(Fa):
    __tablename__ = 'introduction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String)
    dynamic = Column(Boolean, default=False)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot_test.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)

    coin_bot_test = relationship('CoinBot', back_populates='introduction', lazy=True)

class Tokenomics(Fa):
    __tablename__ = 'tokenomics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    total_supply = Column(String)
    circulating_supply = Column(String)
    percentage_circulating_supply = Column(String)
    max_supply = Column(String)
    supply_model = Column(String)
    dynamic = Column(Boolean, default=False)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot_test.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    coin_bot_test = relationship('CoinBot', back_populates='tokenomics', lazy=True)

class Token_distribution(Fa):
    __tablename__ = 'token_distribution'
    id = Column(Integer, primary_key=True, autoincrement=True)
    holder_category = Column(String)
    percentage_held = Column(String)
    dynamic = Column(Boolean, default=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot_test.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    coin_bot_test = relationship('CoinBot', back_populates='token_distribution', lazy=True)

class Token_utility(Fa):
    __tablename__ = 'token_utility'
    id = Column(Integer, primary_key=True, autoincrement=True)
    gas_fees_and_transaction_settlement = Column(String)
    dynamic = Column(Boolean, default=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot_test.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    coin_bot_test = relationship('CoinBot', back_populates='token_utility', lazy=True)

class Value_accrual_mechanisms(Fa):
    __tablename__ = 'value_accrual_mechanisms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_burning = Column(String)
    token_buyback = Column(String)
    dynamic = Column(Boolean, default=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot_test.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    coin_bot_test = relationship('CoinBot', back_populates='value_accrual_mechanisms', lazy=True)

class Competitor(Fa):
    __tablename__ = 'competitor'
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String)
    circulating_supply = Column(String)
    token_supply_model = Column(String)
    current_market_cap = Column(String)
    tvl = Column(String)
    daily_active_users = Column(String)
    transaction_fees = Column(String)
    transaction_speed = Column(String)
    Inflation_rate = Column(String)
    apr = Column(String)
    active_developers = Column(Integer)
    revenue = Column(Integer)
    dynamic = Column(Boolean, default=True)
    coin_bot_id = Column(Integer, ForeignKey('coin_bot_test.bot_id'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    coin_bot_test = relationship('CoinBot', back_populates='competitor', lazy=True)
