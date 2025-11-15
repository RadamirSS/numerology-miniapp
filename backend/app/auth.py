import os
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from dotenv import load_dotenv

from fastapi import APIRouter, Depends, HTTPException
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .db import get_db
from . import models

# Загружаем переменные окружения из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================
#  Конфиг почты (SendGrid / SMTP)
# =========================

# Читаем настройки из переменных окружения
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@example.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.sendgrid.net")
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"

# USE_CREDENTIALS должен быть True только если есть username и password
USE_CREDENTIALS = bool(MAIL_USERNAME and MAIL_PASSWORD)

# Логируем конфигурацию (без пароля)
logger.info(f"SMTP Config: server={MAIL_SERVER}, port={MAIL_PORT}, from={MAIL_FROM}, "
            f"starttls={MAIL_STARTTLS}, ssl={MAIL_SSL_TLS}, use_credentials={USE_CREDENTIALS}")

conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_STARTTLS=MAIL_STARTTLS,
    MAIL_SSL_TLS=MAIL_SSL_TLS,
    USE_CREDENTIALS=USE_CREDENTIALS,
    VALIDATE_CERTS=True,
)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["auth"])

# =========================
#  Вспомогательные функции
# =========================

def hash_password(password: str) -> str:
    # pbkdf2_sha256 нормально работает с длинными паролями
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return pwd_context.verify(plain_password, password_hash)


def generate_code() -> str:
    return f"{random.randint(100000, 999999)}"


async def send_email(subject: str, body: str, recipient: str) -> None:
    """
    Универсальная отправка писем через SMTP.
    
    Если конфиг/SMTP сломан — логируем ошибку, но не роняем приложение.
    
    Требуемые переменные окружения:
    - MAIL_SERVER: SMTP сервер (например, smtp.sendgrid.net, smtp.gmail.com)
    - MAIL_PORT: Порт SMTP (обычно 587 для TLS или 465 для SSL)
    - MAIL_USERNAME: Имя пользователя SMTP (для SendGrid это 'apikey')
    - MAIL_PASSWORD: Пароль или API ключ SMTP
    - MAIL_FROM: Email отправителя (должен быть подтверждён у провайдера)
    - MAIL_STARTTLS: True/False (обычно True для порта 587)
    - MAIL_SSL_TLS: True/False (обычно False для порта 587, True для 465)
    
    Для dev-режима можно использовать:
    - Mailtrap (mailtrap.io) - тестовый SMTP сервер
    - Gmail с паролем приложения
    - SendGrid (sendgrid.com) - для продакшена
    """
    if not MAIL_SERVER or not MAIL_FROM:
        logger.warning(f"SMTP не настроен: MAIL_SERVER={MAIL_SERVER}, MAIL_FROM={MAIL_FROM}")
        logger.warning("Письмо не отправлено. Настройте переменные окружения для отправки email.")
        return
    
    logger.info(f"Отправка письма '{subject}' на {recipient}")
    
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype="plain",
    )
    
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        logger.info(f"✅ Письмо успешно отправлено на {recipient}")
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"❌ Ошибка отправки письма на {recipient}: {error_type}: {error_msg}")
        logger.error(f"   Проверьте настройки SMTP в .env файле")
        logger.error(f"   MAIL_SERVER={MAIL_SERVER}, MAIL_PORT={MAIL_PORT}, MAIL_FROM={MAIL_FROM}")
        # Не выбрасываем исключение, чтобы не ломать регистрацию
        # В проде можно добавить отправку в очередь или retry логику


def user_to_dict(user: models.User) -> dict:
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
        "is_email_verified": getattr(user, "is_email_verified", False),
    }


# =========================
#  Pydantic-схемы
# =========================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    birth_date: str
    tariff: Optional[str] = None

    telegram_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_first_name: Optional[str] = None
    telegram_last_name: Optional[str] = None
    telegram_raw: Optional[Any] = None

    password: str
    password_confirm: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str
    new_password_confirm: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class TestEmailRequest(BaseModel):
    email: EmailStr
    subject: Optional[str] = "Тестовое письмо"
    body: Optional[str] = "Это тестовое письмо для проверки настройки SMTP."


# =========================
#  Эндпоинты
# =========================

@router.post("/register")
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # 1. Пароли
    if payload.password != payload.password_confirm:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    # 2. Email уже есть?
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    code = generate_code()

    user = models.User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        birth_date=payload.birth_date,
        tariff=payload.tariff,
        telegram_id=payload.telegram_id,
        telegram_username=payload.telegram_username,
        telegram_first_name=payload.telegram_first_name,
        telegram_last_name=payload.telegram_last_name,
        password_hash=hash_password(payload.password),
        email_code=code,
        is_email_verified=False,
    )

    # если поле telegram_raw есть в модели — можно добавить:
    if hasattr(models.User, "telegram_raw") and payload.telegram_raw is not None:
        import json
        user.telegram_raw = json.dumps(payload.telegram_raw, ensure_ascii=False)

    db.add(user)
    db.commit()
    db.refresh(user)

    # Письмо с кодом
    subject = "Код подтверждения e-mail"
    body = f"""Здравствуйте, {user.name}!

Ваш код подтверждения e-mail: {code}

Введите этот код в приложении для подтверждения вашего email адреса.

Если вы не регистрировались в Numerology Mini App, просто проигнорируйте это письмо.

С уважением,
Команда Numerology Mini App"""

    # Отправляем письмо (не блокируем регистрацию при ошибке)
    try:
        await send_email(subject, body, user.email)
        logger.info(f"Код подтверждения отправлен пользователю {user.email} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Не удалось отправить письмо пользователю {user.email}: {e}")
        # Пользователь всё равно создан, но письмо не отправлено
        # В dev-режиме можно вывести код в лог
        logger.warning(f"DEV MODE: Код подтверждения для {user.email}: {code}")

    return {
        "status": "ok",
        "message": "Код подтверждения отправлен на e-mail",
        "user": user_to_dict(user),
    }


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if not user.email_code or user.email_code != payload.code:
        raise HTTPException(status_code=400, detail="Неверный код")

    user.is_email_verified = True
    user.email_code = None
    db.commit()
    db.refresh(user)

    return {"status": "ok", "user": user_to_dict(user)}


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    
    if not user or not user.password_hash:
        raise HTTPException(status_code=400, detail="Неверный e-mail или пароль")
    
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный e-mail или пароль")

    return {"status": "ok", "user": user_to_dict(user)}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    # Чтобы нельзя было проверить наличие email в системе — всегда возвращаем ok.
    if user:
        code = generate_code()
        user.password_reset_code = code
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.commit()

        subject = "Восстановление пароля"
        body = f"""Здравствуйте!

Ваш код для восстановления пароля: {code}

Введите этот код в приложении для сброса пароля.

Код действителен в течение 15 минут.

Если вы не запрашивали восстановление пароля, просто проигнорируйте это письмо.

С уважением,
Команда Numerology Mini App"""
        
        try:
            await send_email(subject, body, user.email)
            logger.info(f"Код восстановления пароля отправлен пользователю {user.email}")
        except Exception as e:
            logger.error(f"Не удалось отправить письмо восстановления пароля на {user.email}: {e}")
            logger.warning(f"DEV MODE: Код восстановления для {user.email}: {code}")

    return {
        "status": "ok",
        "message": "Если e-mail есть в системе, мы отправили на него код для восстановления",
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Неверный код или e-mail")

    if payload.new_password != payload.new_password_confirm:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    if not user.password_reset_code or user.password_reset_code != payload.code:
        raise HTTPException(status_code=400, detail="Неверный код или срок действия кода истёк")

    if not user.password_reset_expires or user.password_reset_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Неверный код или срок действия кода истёк")

    user.password_hash = hash_password(payload.new_password)
    user.password_reset_code = None
    user.password_reset_expires = None
    db.commit()
    db.refresh(user)

    return {"status": "ok", "message": "Пароль изменён", "user": user_to_dict(user)}


@router.post("/resend-verification")
async def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Повторная отправка кода подтверждения email.
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    
    if not user:
        # Для безопасности не сообщаем, что пользователь не найден
        return {
            "status": "ok",
            "message": "Если e-mail зарегистрирован, код подтверждения отправлен"
        }
    
    # Если email уже подтверждён
    if user.is_email_verified:
        return {
            "status": "ok",
            "message": "Email уже подтверждён"
        }
    
    # Генерируем новый код
    code = generate_code()
    user.email_code = code
    db.commit()
    db.refresh(user)
    
    subject = "Код подтверждения e-mail (повторная отправка)"
    body = f"""Здравствуйте, {user.name}!

Ваш код подтверждения e-mail: {code}

Введите этот код в приложении для подтверждения вашего email адреса.

Если вы не запрашивали повторную отправку кода, просто проигнорируйте это письмо.

С уважением,
Команда Numerology Mini App"""
    
    try:
        await send_email(subject, body, user.email)
        logger.info(f"Повторная отправка кода подтверждения пользователю {user.email} (ID: {user.id})")
    except Exception as e:
        logger.error(f"Не удалось отправить письмо пользователю {user.email}: {e}")
        logger.warning(f"DEV MODE: Код подтверждения для {user.email}: {code}")
    
    return {
        "status": "ok",
        "message": "Код подтверждения отправлен на e-mail"
    }


@router.post("/send-test-email")
async def send_test_email(payload: TestEmailRequest):
    """
    Тестовый эндпоинт для проверки настройки SMTP.
    
    ВНИМАНИЕ: Этот эндпоинт только для разработки и отладки!
    В продакшене его следует отключить или защитить авторизацией.
    """
    logger.info(f"Тестовая отправка письма на {payload.email}")
    
    try:
        await send_email(payload.subject, payload.body, payload.email)
        return {
            "status": "ok",
            "message": f"Тестовое письмо отправлено на {payload.email}"
        }
    except Exception as e:
        logger.error(f"Ошибка при тестовой отправке: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Не удалось отправить тестовое письмо: {str(e)}"
        )