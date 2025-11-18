"""
Скрипт для добавления поля avatar_url в существующую базу данных.
Запускать только если база уже существует и поле avatar_url отсутствует.
"""
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./numerology.db")

# Если используется SQLite
if DATABASE_URL.startswith("sqlite"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    
    if os.path.exists(db_path):
        print(f"Проверяем базу данных: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли колонка avatar_url
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "avatar_url" not in columns:
            print("Добавляем колонку avatar_url...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
                conn.commit()
                print("✅ Колонка avatar_url успешно добавлена")
            except Exception as e:
                print(f"❌ Ошибка при добавлении колонки: {e}")
        else:
            print("✅ Колонка avatar_url уже существует")
        
        conn.close()
    else:
        print(f"База данных не найдена: {db_path}")
        print("База будет создана автоматически при следующем запуске приложения")
else:
    print(f"Используется не SQLite база: {DATABASE_URL}")
    print("Для PostgreSQL/MySQL выполните миграцию вручную:")
    print("ALTER TABLE users ADD COLUMN avatar_url TEXT;")

