from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from calculations import compute_matrix
from drawing import draw_matrix

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "")

router = APIRouter(prefix="/matrix", tags=["matrix"])

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)


class MatrixRequest(BaseModel):
    birth_date: str  # 'dd.mm.yyyy'


@router.post("/data")
def get_matrix_data(payload: MatrixRequest):
    try:
        m = compute_matrix(payload.birth_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    result = m.to_dict()
    
    # Добавляем интерпретации цифр (пока заглушки)
    digit_interpretations = {
        str(d): f"Интерпретация цифры {d} (заглушка)"
        for d in range(1, 10)
    }
    result["digit_interpretations"] = digit_interpretations
    
    return result


@router.post("/image")
def get_matrix_image(payload: MatrixRequest):
    try:
        safe_date = payload.birth_date.replace(".", "_")
        filename = f"matrix_{safe_date}.png"
        filepath = os.path.join(STATIC_DIR, filename)

        # Проверяем, существует ли уже кэшированный файл
        if os.path.exists(filepath):
            # Файл уже существует, возвращаем его URL без пересчёта
            if BASE_URL:
                url = f"{BASE_URL.rstrip('/')}/static/{filename}"
            else:
                # локально фронт ходит на http://localhost:8000
                url = f"http://localhost:8000/static/{filename}"

            # Добавляем интерпретации цифр в ответ (пока заглушки)
            digit_interpretations = {
                str(d): f"Интерпретация цифры {d} (заглушка)"
                for d in range(1, 10)
            }

            return {
                "image_url": url,
                "digit_interpretations": digit_interpretations
            }

        # Файла нет, нужно вычислить и нарисовать матрицу
        m = compute_matrix(payload.birth_date)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # Определяем путь к фоновому изображению
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        background_path = os.path.join(backend_dir, "man.png")
        
        # ВАЖНО: передаём filename как именованный аргумент
        draw_matrix(m, filename=filepath, background_path=background_path)

        # Формируем URL для фронта
        if BASE_URL:
            url = f"{BASE_URL.rstrip('/')}/static/{filename}"
        else:
            # локально фронт ходит на http://localhost:8000
            url = f"http://localhost:8000/static/{filename}"

        # Добавляем интерпретации цифр в ответ (пока заглушки)
        digit_interpretations = {
            str(d): f"Интерпретация цифры {d} (заглушка)"
            for d in range(1, 10)
        }

        return {
            "image_url": url,
            "digit_interpretations": digit_interpretations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании изображения: {str(e)}")