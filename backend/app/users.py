from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
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
        "avatar_url": getattr(user, "avatar_url", None),
    }


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    avatar_url: Optional[str] = None
    tariff: Optional[str] = None


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


@router.put("/{user_id}")
def update_user(user_id: int, payload: UpdateProfileRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Обновляем только переданные поля
    if payload.name is not None:
        user.name = payload.name
    if payload.email is not None:
        # Проверяем, что email не занят другим пользователем
        existing = db.query(models.User).filter(
            models.User.email == payload.email,
            models.User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        user.email = payload.email
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.birth_date is not None:
        user.birth_date = payload.birth_date
    if payload.tariff is not None:
        user.tariff = payload.tariff
    if payload.avatar_url is not None and hasattr(user, "avatar_url"):
        user.avatar_url = payload.avatar_url
    
    try:
        db.commit()
        db.refresh(user)
        return user_to_dict(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении пользователя: {str(e)}")


@router.post("/by-telegram/{telegram_id}/create-or-update")
def create_or_update_user_by_telegram(telegram_id: int, payload: UpdateProfileRequest, db: Session = Depends(get_db)):
    """Создаёт или обновляет пользователя по Telegram ID"""
    try:
        user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
        
        if not user:
            # Создаём нового пользователя
            # Генерируем уникальный email, если не передан
            email = payload.email
            if not email:
                email = f"user_{telegram_id}@telegram.local"
                # Проверяем, что такой email не занят
                existing_email = db.query(models.User).filter(models.User.email == email).first()
                if existing_email:
                    email = f"user_{telegram_id}_{existing_email.id}@telegram.local"
            
            user = models.User(
                telegram_id=telegram_id,
                name=payload.name or "Пользователь",
                email=email,
                phone=payload.phone,
                birth_date=payload.birth_date or "",
                tariff=payload.tariff,
            )
            # Устанавливаем avatar_url, если поле существует в модели
            if hasattr(models.User, "avatar_url") and payload.avatar_url is not None:
                user.avatar_url = payload.avatar_url
            db.add(user)
        else:
            # Обновляем существующего
            if payload.name is not None:
                user.name = payload.name
            if payload.email is not None:
                existing = db.query(models.User).filter(
                    models.User.email == payload.email,
                    models.User.id != user.id
                ).first()
                if existing:
                    raise HTTPException(status_code=400, detail="Email already taken")
                user.email = payload.email
            if payload.phone is not None:
                user.phone = payload.phone
            if payload.birth_date is not None:
                user.birth_date = payload.birth_date
            if payload.tariff is not None:
                user.tariff = payload.tariff
            if hasattr(models.User, "avatar_url") and payload.avatar_url is not None:
                user.avatar_url = payload.avatar_url
        
        db.commit()
        db.refresh(user)
        return user_to_dict(user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании/обновлении пользователя: {str(e)}")
