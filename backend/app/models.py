from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from .db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    birth_date = Column(String, nullable=False)  # 'dd.mm.yyyy'
    tariff = Column(String, nullable=True)
    
    # Поля для авторизации
    password_hash = Column(String, nullable=True)
    email_code = Column(String, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    
    # Поля для восстановления пароля
    password_reset_code = Column(String, nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Поля для Telegram
    telegram_id = Column(Integer, index=True, nullable=True)
    telegram_username = Column(String, nullable=True)
    telegram_first_name = Column(String, nullable=True)
    telegram_last_name = Column(String, nullable=True)
    telegram_raw = Column(Text, nullable=True)
    
    # Служебное поле
    created_at = Column(DateTime(timezone=True), server_default=func.now())
