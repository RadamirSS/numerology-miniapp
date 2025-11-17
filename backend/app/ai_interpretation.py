"""
AI интерпретация на основе профиля пользователя и индексированных книг.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import get_db
from .openai_client import get_embedding, generate_ai_interpretation
from calc.pythagoras_square.calculator import _calculate_internal as calc_pythagoras
from calculations import compute_matrix

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

# Глобальные переменные для чанков и embeddings
CHUNKS: List[Dict] = []
EMBEDDINGS: Optional[np.ndarray] = None


def load_chunks():
    """Загрузить чанки и embeddings при старте модуля."""
    global CHUNKS, EMBEDDINGS
    
    base_dir = Path(__file__).parent
    chunks_file = base_dir / "data" / "ai_knowledge" / "chunks.json"
    
    if not chunks_file.exists():
        logger.warning(f"Файл {chunks_file} не найден. AI база знаний не инициализирована.")
        logger.warning("Запустите скрипт индексации: python -m scripts.index_books")
        CHUNKS = []
        EMBEDDINGS = None
        return
    
    try:
        with open(chunks_file, "r", encoding="utf-8") as f:
            CHUNKS = json.load(f)
        
        if not CHUNKS:
            logger.warning("Файл chunks.json пуст.")
            EMBEDDINGS = None
            return
        
        # Собираем матрицу embeddings
        embeddings_list = []
        for chunk in CHUNKS:
            if "embedding" in chunk:
                embeddings_list.append(chunk["embedding"])
            else:
                logger.warning(f"Чанк {chunk.get('id')} не содержит embedding")
        
        if embeddings_list:
            EMBEDDINGS = np.array(embeddings_list)
            logger.info(f"Загружено {len(CHUNKS)} чанков, размерность embeddings: {EMBEDDINGS.shape}")
        else:
            EMBEDDINGS = None
            logger.warning("Не найдено embeddings в чанках")
            
    except Exception as e:
        logger.error(f"Ошибка при загрузке chunks.json: {e}")
        CHUNKS = []
        EMBEDDINGS = None


def check_knowledge_base():
    """Проверить, что база знаний инициализирована."""
    if not CHUNKS or EMBEDDINGS is None:
        raise HTTPException(
            status_code=503,
            detail="AI база знаний не инициализирована. Сначала запустите скрипт индексации книг."
        )


def normalize_birth_date(date_str: str) -> str:
    """
    Нормализовать дату рождения к формату DD.MM.YYYY.
    
    Поддерживает форматы:
    - DD.MM.YYYY
    - YYYY-MM-DD
    - DD-MM-YYYY
    """
    # Убираем пробелы
    date_str = date_str.strip()
    
    # Если формат YYYY-MM-DD, конвертируем в DD.MM.YYYY
    if "-" in date_str and len(date_str.split("-")[0]) == 4:
        parts = date_str.split("-")
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
    
    # Если формат DD-MM-YYYY, конвертируем в DD.MM.YYYY
    if "-" in date_str and len(date_str.split("-")[0]) <= 2:
        return date_str.replace("-", ".")
    
    # Если уже в формате DD.MM.YYYY, возвращаем как есть
    if "." in date_str:
        return date_str
    
    return date_str


def build_user_profile(birth_date: str, db: Optional[Session] = None) -> Dict:
    """
    Построить профиль пользователя на основе даты рождения.
    
    Использует существующие калькуляторы для получения всех показателей.
    """
    # Нормализуем дату
    normalized_date = normalize_birth_date(birth_date)
    
    profile = {
        "birth_date": normalized_date,
    }
    
    try:
        # Матрица Пифагора
        try:
            pifagor_result = calc_pythagoras(normalized_date)
            profile["pifagor"] = {
                "counts": pifagor_result.counts,
                "third_zone": pifagor_result.third_zone,
                "third_zone_reduced": pifagor_result.third_zone_reduced,
                "fourth_zone": pifagor_result.fourth_zone,
                "fourth_zone_reduced": pifagor_result.fourth_zone_reduced,
                "row_147": pifagor_result.row_147,
                "row_258": pifagor_result.row_258,
                "row_369": pifagor_result.row_369,
                "diag_357": pifagor_result.diag_357,
                "diag_159": pifagor_result.diag_159,
            }
        except Exception as e:
            logger.warning(f"Ошибка при расчёте матрицы Пифагора: {e}")
            profile["pifagor"] = {}
        
        # Матрица судьбы
        try:
            matrix = compute_matrix(normalized_date)
            profile["matrix"] = {
                "primary": {
                    "A": matrix.primary.A,
                    "B": matrix.primary.B,
                    "C": matrix.primary.C,
                    "D": matrix.primary.D,
                    "center": matrix.primary.center,
                },
                "portrait": {
                    "first": matrix.portrait.first,
                    "second": matrix.portrait.second,
                    "third": matrix.portrait.third,
                },
                "talents": {
                    "first": matrix.talents.first,
                    "second": matrix.talents.second,
                    "third": matrix.talents.third,
                },
            }
        except Exception as e:
            logger.warning(f"Ошибка при расчёте матрицы судьбы: {e}")
            profile["matrix"] = {}
        
        # Простые расчёты жизненного пути
        try:
            from datetime import datetime
            d = datetime.strptime(normalized_date, "%d.%m.%Y")
            day, month, year = d.day, d.month, d.year
            
            # Жизненный путь: сумма всех цифр даты до одной цифры
            def reduce_to_single_digit(n):
                while n > 9 and n not in [11, 22, 33]:
                    n = sum(int(d) for d in str(n))
                return n
            
            life_path = reduce_to_single_digit(day + month + sum(int(d) for d in str(year)))
            profile["life_path"] = life_path
            
            # Число души (сумма гласных в имени - упрощённо, используем день)
            profile["soul_number"] = reduce_to_single_digit(day)
            
            # Число личности (сумма согласных - упрощённо, используем месяц)
            profile["personality_number"] = reduce_to_single_digit(month)
            
        except Exception as e:
            logger.warning(f"Ошибка при расчёте базовых чисел: {e}")
        
    except Exception as e:
        logger.error(f"Ошибка при построении профиля: {e}")
    
    return profile


def build_query_text_from_profile(profile: Dict) -> str:
    """
    Сформировать текстовый запрос для поиска по книгам на основе профиля.
    """
    text = f"Нумерологический профиль. Дата рождения: {profile.get('birth_date', 'не указана')}. "
    
    if "life_path" in profile:
        text += f"Жизненный путь: {profile['life_path']}. "
    
    if "soul_number" in profile:
        text += f"Число души: {profile['soul_number']}. "
    
    if "personality_number" in profile:
        text += f"Число личности: {profile['personality_number']}. "
    
    if "pifagor" in profile and profile["pifagor"]:
        pifagor = profile["pifagor"]
        text += "Матрица Пифагора: "
        if "counts" in pifagor:
            counts = pifagor["counts"]
            present_digits = [str(d) for d, c in counts.items() if c > 0]
            absent_digits = [str(d) for d, c in counts.items() if c == 0]
            if present_digits:
                text += f"присутствуют цифры {', '.join(present_digits)}. "
            if absent_digits:
                text += f"отсутствуют цифры {', '.join(absent_digits)}. "
        
        if "row_147" in pifagor:
            text += f"Линия характера: {pifagor['row_147']}. "
        if "row_258" in pifagor:
            text += f"Линия энергии: {pifagor['row_258']}. "
        if "row_369" in pifagor:
            text += f"Линия таланта: {pifagor['row_369']}. "
    
    if "matrix" in profile and profile["matrix"]:
        matrix = profile["matrix"]
        if "primary" in matrix:
            primary = matrix["primary"]
            text += f"Матрица судьбы: точки {primary.get('A')}, {primary.get('B')}, {primary.get('C')}, {primary.get('D')}, центр {primary.get('center')}. "
    
    return text


def get_top_chunks(query_text: str, k: int = 10) -> List[Dict]:
    """
    Найти top-k наиболее релевантных чанков по косинусному сходству.
    
    Args:
        query_text: Текст запроса
        k: Количество чанков для возврата
        
    Returns:
        Список словарей с чанками
    """
    check_knowledge_base()
    
    # Получаем embedding запроса
    try:
        query_embedding = np.array(get_embedding(query_text))
    except Exception as e:
        logger.error(f"Ошибка при получении embedding запроса: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при обработке запроса")
    
    # Нормализуем векторы для косинусного сходства
    query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
    embeddings_norm = EMBEDDINGS / (np.linalg.norm(EMBEDDINGS, axis=1, keepdims=True) + 1e-10)
    
    # Вычисляем косинусное сходство
    similarities = np.dot(embeddings_norm, query_norm)
    
    # Получаем индексы top-k
    top_indices = np.argsort(similarities)[::-1][:k]
    
    # Возвращаем соответствующие чанки
    return [CHUNKS[i] for i in top_indices]


class AIInterpretationRequest(BaseModel):
    birth_date: str
    user_id: Optional[int] = None


@router.post("/interpretation")
async def ai_interpretation(payload: AIInterpretationRequest, db: Session = Depends(get_db)):
    """
    Генерация AI интерпретации на основе профиля пользователя.
    """
    try:
        # 1. Проверяем базу знаний
        check_knowledge_base()
        
        # 2. Нормализуем дату
        normalized_date = normalize_birth_date(payload.birth_date)
        logger.info(f"Обработка запроса для даты: {normalized_date}")
        
        # 3. Строим профиль
        profile = build_user_profile(normalized_date, db)
        logger.info(f"Построен профиль: {list(profile.keys())}")
        
        # 4. Формируем запрос для поиска
        query_text = build_query_text_from_profile(profile)
        
        # 5. Находим релевантные чанки
        top_chunks = get_top_chunks(query_text, k=10)
        logger.info(f"Найдено {len(top_chunks)} релевантных чанков")
        
        # 6. Генерируем интерпретацию
        try:
            report = generate_ai_interpretation(profile, top_chunks)
            logger.info("Интерпретация успешно сгенерирована")
        except Exception as e:
            logger.error(f"Ошибка при генерации интерпретации: {e}")
            raise HTTPException(
                status_code=502,
                detail="Ошибка генерации AI интерпретации. Проверьте настройки OpenAI API."
            )
        
        # 7. Возвращаем результат
        return {
            "status": "ok",
            "profile": profile,
            "report": report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка при генерации интерпретации"
        )


# Загружаем чанки при импорте модуля
load_chunks()

