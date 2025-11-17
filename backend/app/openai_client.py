"""
OpenAI клиент для работы с embeddings и генерацией текста.
"""
import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Инициализация клиента OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # Опционально, для совместимости с другими провайдерами
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL if OPENAI_BASE_URL else None,
)


def get_embedding(text: str) -> List[float]:
    """
    Получить embedding для текста.
    
    Args:
        text: Текст для векторизации
        
    Returns:
        Список чисел (вектор embedding)
        
    Raises:
        Exception: При ошибках API OpenAI
    """
    # Обрезаем текст до разумной длины (2000-3000 символов)
    max_length = 3000
    if len(text) > max_length:
        text = text[:max_length]
    
    # Нормализуем текст (убираем лишние пробелы)
    text = " ".join(text.split())
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Ошибка получения embedding: {str(e)}")


def generate_ai_interpretation(profile: dict, chunks: List[dict]) -> str:
    """
    Сгенерировать AI интерпретацию на основе профиля пользователя и релевантных чанков.
    
    Args:
        profile: Словарь с профилем пользователя (дата рождения, расчёты и т.д.)
        chunks: Список словарей с чанками из книг
        
    Returns:
        Строка с текстом интерпретации
        
    Raises:
        Exception: При ошибках API OpenAI
    """
    # System prompt
    system_prompt = """Ты профессиональный нумеролог с глубокими знаниями в области нумерологии. 
Твоя задача — создать связный и понятный отчёт на основе предоставленного профиля человека и релевантных отрывков из книг по нумерологии.

Важно:
- Опирайся ТОЛЬКО на предоставленные отрывки из книг (ИСТОЧНИКИ)
- Не придумывай информацию, которой нет в источниках
- Создавай связный текст, а не просто перечисление фактов
- Пиши на русском языке
- Структурируй отчёт логично: сначала общая характеристика, затем детали по ключевым аспектам"""

    # Формируем описание профиля
    profile_text = "ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:\n\n"
    profile_text += f"Дата рождения: {profile.get('birth_date', 'не указана')}\n"
    
    # Добавляем основные показатели
    if 'life_path' in profile:
        profile_text += f"Жизненный путь: {profile['life_path']}\n"
    if 'soul_number' in profile:
        profile_text += f"Число души: {profile['soul_number']}\n"
    if 'personality_number' in profile:
        profile_text += f"Число личности: {profile['personality_number']}\n"
    
    # Добавляем данные из матрицы Пифагора
    if 'pifagor' in profile:
        pifagor = profile['pifagor']
        profile_text += "\nМатрица Пифагора:\n"
        if 'counts' in pifagor:
            counts = pifagor['counts']
            profile_text += "Цифры в матрице: "
            for digit, count in sorted(counts.items()):
                if count > 0:
                    profile_text += f"{digit} ({count}x) "
            profile_text += "\n"
    
    # Добавляем другие показатели
    for key, value in profile.items():
        if key not in ['birth_date', 'life_path', 'soul_number', 'personality_number', 'pifagor']:
            if isinstance(value, dict):
                profile_text += f"\n{key}: {str(value)}\n"
            else:
                profile_text += f"{key}: {value}\n"
    
    # Формируем список источников
    sources_text = "\n\nИСТОЧНИКИ (отрывки из книг):\n\n"
    for i, chunk in enumerate(chunks, 1):
        book_name = chunk.get('book', 'Неизвестная книга')
        page = chunk.get('page', '?')
        text = chunk.get('text', '')
        sources_text += f"[{i}] Книга: {book_name}, страница {page}\n"
        sources_text += f"{text}\n\n"
    
    user_prompt = profile_text + sources_text
    user_prompt += "\n\nСоздай связный отчёт на основе предоставленного профиля и источников."
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Ошибка генерации интерпретации: {str(e)}")



