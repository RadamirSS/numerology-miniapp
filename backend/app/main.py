from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from . import calculators, matrix_api, auth, users, ai_interpretation

app = FastAPI(title="Numerology Mini App API")

# CORS — для фронта на localhost:5173 и мини-аппа
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # при желании потом сузим
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(calculators.router)
app.include_router(matrix_api.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ai_interpretation.router)

# Статика для картинок матрицы
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")