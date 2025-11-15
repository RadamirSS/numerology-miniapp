from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from . import models

router = APIRouter(prefix="/users", tags=["users"])


def user_to_dict(user: models.User) -> dict:
    """Преобразует модель User в словарь для ответа API (без чувствительных данных)"""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "birth_date": user.birth_date,
        "tariff": user.tariff,
        "telegram_id": user.telegram_id,
        "telegram_username": user.telegram_username,
        "telegram_first_name": user.telegram_first_name,
        "telegram_last_name": user.telegram_last_name,
        "is_email_verified": user.is_email_verified,
    }


@router.get("/by-telegram/{telegram_id}")
def get_user_by_telegram(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_dict(user)


@router.get("/by-email/{email}")
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_dict(user)
