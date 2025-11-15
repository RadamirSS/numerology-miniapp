from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


# Базовая директория проекта (папка numerology_bot/xxx)
BASE_DIR = Path(__file__).resolve().parents[2]
INTERPRETATIONS_DIR = BASE_DIR / "interpretations"


@lru_cache(maxsize=None)
def _load_json(filename: str) -> dict:
    """
    Загружаем JSON из папки interpretations один раз и кешируем.
    """
    path = INTERPRETATIONS_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _calc_birth_energy(day: int) -> int:
    """
    Энергия дня рождения:
    - если день 1–22 — берём его как есть
    - если > 22 — суммируем цифры (23 → 2+3 = 5 и т.п.)
    """
    if 1 <= day <= 22:
        return day
    return sum(int(d) for d in str(day))


def calculate(birth_date: str) -> str:
    """
    Основной калькулятор «Расшифровка по дате рождения».

    birth_date ожидается в формате 'ДД.ММ.ГГГГ',
    как и сохраняется в состоянии бота.
    """
    day_str, month_str, *_ = birth_date.strip().split(".")
    day = int(day_str)
    month = int(month_str)

    # Загружаем интерпретации
    birth_day_data = _load_json("birth_day.json")
    last_day_data = _load_json("last_day.json")
    birth_month_data = _load_json("birth_month.json")

    lines: list[str] = []

    # Заголовок
    lines.append("🔢 Расшифровка по дате рождения")
    lines.append("")
    lines.append(f"Дата рождения: {birth_date}")
    lines.append("")

    # 1. Энергия дня рождения (1–22, либо сумма цифр дня, если > 22)
    energy_num = _calc_birth_energy(day)
    energy_text = birth_day_data.get(str(energy_num))
    if energy_text:
        lines.append("Энергия дня рождения")
        lines.append("-" * 30)
        lines.append(energy_text.strip())
        lines.append("")

    # 2. Интерпретация по дню рождения (1–31, + общий вступительный текст)
    day_intro = last_day_data.get("intro")
    day_text = last_day_data.get(str(day))

    if day_intro or day_text:
        lines.append("Информация по дню рождения")
        lines.append("-" * 30)

        if day_intro:
            lines.append(day_intro.strip())
            lines.append("")

        if day_text:
            lines.append(day_text.strip())
            lines.append("")

    # 3. Интерпретация по месяцу рождения (1–12, + общий вступительный текст)
    month_intro = birth_month_data.get("intro")
    month_text = birth_month_data.get(str(month))

    if month_intro or month_text:
        lines.append("Информация по месяцу рождения")
        lines.append("-" * 30)

        if month_intro:
            lines.append(month_intro.strip())
            lines.append("")

        if month_text:
            lines.append(month_text.strip())
            lines.append("")

    return "\n".join(lines).strip()
