# Backend для Numerology Mini App

FastAPI приложение для нумерологических расчётов и AI интерпретаций.

## Установка и запуск

### 1. Создание виртуального окружения

```bash
cd backend
python3 -m venv .venv
```

### 2. Активация виртуального окружения

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в папке `backend/` с необходимыми переменными:

```env
# База данных (опционально, по умолчанию используется SQLite)
DATABASE_URL=sqlite:///./numerology.db

# OpenAI API (для AI интерпретации)
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Email (SMTP для отправки писем)
# Для SendGrid:
MAIL_USERNAME=apikey
MAIL_PASSWORD=your_sendgrid_api_key
MAIL_FROM=your_verified_email@example.com
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

# Для Gmail (с паролем приложения):
# MAIL_USERNAME=your_email@gmail.com
# MAIL_PASSWORD=your_app_password
# MAIL_FROM=your_email@gmail.com
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_STARTTLS=True
# MAIL_SSL_TLS=False

# Для Mailtrap (тестовый SMTP для разработки):
# MAIL_USERNAME=your_mailtrap_username
# MAIL_PASSWORD=your_mailtrap_password
# MAIL_FROM=noreply@example.com
# MAIL_SERVER=smtp.mailtrap.io
# MAIL_PORT=2525
# MAIL_STARTTLS=True
# MAIL_SSL_TLS=False

# Base URL для статических файлов (опционально)
BASE_URL=http://localhost:8000
```

### 5. Создание базы данных

```bash
python create_db.py
```

### 6. Запуск сервера

```bash
uvicorn app.main:app --reload --port 8000
```

Сервер будет доступен по адресу: http://localhost:8000

Документация API (Swagger UI): http://localhost:8000/docs

## Структура проекта

```
backend/
├── app/
│   ├── main.py              # Основное FastAPI приложение
│   ├── auth.py              # Авторизация и регистрация
│   ├── models.py            # Модели SQLAlchemy
│   ├── db.py                # Настройка базы данных
│   ├── calculators.py       # Эндпоинты калькуляторов
│   ├── matrix_api.py        # API для матрицы судьбы
│   ├── users.py             # API для работы с пользователями
│   ├── ai_interpretation.py # AI интерпретация
│   ├── openai_client.py     # Клиент OpenAI
│   └── data/
│       ├── books/            # PDF книги для индексации
│       └── ai_knowledge/     # Индексированные данные
├── calc/                     # Модули калькуляторов
├── scripts/
│   └── index_books.py       # Скрипт индексации PDF книг
├── requirements.txt         # Зависимости Python
└── README.md                # Этот файл
```

## Индексация книг для AI интерпретации

1. Положите PDF-книги в папку `app/data/books/`
2. Запустите скрипт индексации:

```bash
python -m scripts.index_books
```

Результат сохранится в `app/data/ai_knowledge/chunks.json`

## Зависимости

Основные зависимости указаны в `requirements.txt`. Особое внимание:

- **passlib[bcrypt]==1.7.4** и **bcrypt==4.1.2** - версии подобраны для совместимости и избежания ошибки "error reading bcrypt version"

## Настройка отправки email

### Переменные окружения для SMTP

Для работы отправки email необходимо настроить следующие переменные в `.env`:

**Обязательные:**
- `MAIL_SERVER` - SMTP сервер (например, `smtp.sendgrid.net`, `smtp.gmail.com`)
- `MAIL_PORT` - Порт SMTP (обычно `587` для TLS или `465` для SSL)
- `MAIL_USERNAME` - Имя пользователя SMTP
- `MAIL_PASSWORD` - Пароль или API ключ SMTP
- `MAIL_FROM` - Email отправителя (должен быть подтверждён у провайдера)

**Опциональные:**
- `MAIL_STARTTLS` - Использовать STARTTLS (обычно `True` для порта 587)
- `MAIL_SSL_TLS` - Использовать SSL/TLS (обычно `False` для порта 587, `True` для 465)

### Тестирование отправки email

Используйте тестовый эндпоинт для проверки настройки SMTP:

```bash
curl -X POST http://localhost:8000/auth/send-test-email \
  -H "Content-Type: application/json" \
  -d '{"email": "your_email@example.com"}'
```

Или через Swagger UI: http://localhost:8000/docs → `/auth/send-test-email`

### Проверка логов

При запуске сервера проверьте логи:
- При старте должно быть сообщение о конфигурации SMTP
- При регистрации должно быть сообщение об отправке письма
- При ошибках будут детальные сообщения об ошибке

### Решение проблем с email

**Письма не отправляются:**
1. Проверьте логи backend - там будут детальные сообщения об ошибках
2. Убедитесь, что все переменные окружения заполнены в `.env`
3. Проверьте, что `MAIL_FROM` подтверждён у вашего SMTP провайдера
4. Для Gmail используйте пароль приложения, а не обычный пароль
5. Для SendGrid убедитесь, что API ключ активен

**Ошибка аутентификации:**
- Проверьте правильность `MAIL_USERNAME` и `MAIL_PASSWORD`
- Для SendGrid `MAIL_USERNAME` должен быть `apikey`
- Для Gmail используйте пароль приложения

**Письма попадают в спам:**
- Убедитесь, что `MAIL_FROM` подтверждён
- Настройте SPF/DKIM записи для вашего домена (для продакшена)

## Решение проблем

### ModuleNotFoundError: No module named 'passlib'

Убедитесь, что виртуальное окружение активировано и зависимости установлены:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Ошибка с bcrypt

Если возникают ошибки типа `AttributeError: module 'bcrypt' has no attribute '__about__'`, убедитесь, что установлены правильные версии:

```bash
pip install passlib[bcrypt]==1.7.4 bcrypt==4.1.2
```

### Проблемы с базой данных

Если используется SQLite, убедитесь, что файл `numerology.db` существует или запустите `python create_db.py`

### Проблемы с отправкой email

См. раздел "Настройка отправки email" выше. Проверьте логи backend для детальной информации об ошибках.

