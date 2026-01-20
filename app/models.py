from sqlalchemy import Column, DateTime, Float, String
from datetime import datetime
from .database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    uuid = Column(String, primary_key=True, index=True)
    balance = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    