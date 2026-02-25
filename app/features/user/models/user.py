from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum
from app.shared.config.database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    rol = Column(Enum('streamer', 'follower', name='user_roles'), nullable=False)