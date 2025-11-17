from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict


_INTERPRETATIONS_CACHE: Dict[str, Any] | None = None


def _load_interpretations() -> Dict[str, Any]:
    """
    Загружаем 3-ю и 4-ю зоны один раз и кешируем.
    Путь считается от корня проекта: ../.. от этого файла → корень бота.
    """
    global _INTERPRETATIONS_CACHE
    if _INTERPRETATIONS_CACHE is not None:
        return _INTERPRETATIONS_CACHE

    base_dir = Path(__file__).resolve().parents[2]
    interpretations_dir = base_dir / "interpretations"

    with open(interpretations_dir / "3_zone.json", "r", encoding="utf-8") as f:
        zone3 = json.load(f)

    with open(interpretations_dir / "4_zone.json", "r", encoding="utf-8") as f:
        zone4_default = json.load(f)

    # Может быть пустым/ещё не заполненным — это нормально
    zone4_2000_path = interpretations_dir / "4_zone_2000.json"
    if zone4_2000_path.exists():
        with open(zone4_2000_path, "r", encoding="utf-8") as f:
            zone4_2000 = json.load(f)
    else:
        zone4_2000 = {}

    _INTERPRETATIONS_CACHE = {
        "3": zone3,
        "4_default": zone4_default,
        "4_2000": zone4_2000,
    }
    return _INTERPRETATIONS_CACHE


def _parse_birth_date(birth_date: str) -> tuple[int, int, int]:
    """
    Принимаем строку формата ДД.MM.ГГГГ (или D.M.YYYY)
    и возвращаем (day, month, year).
    """
    match = re.fullmatch(r"\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*", birth_date)
    if not match:
        raise ValueError("Неверный формат даты рождения. Ожидается ДД.ММ.ГГГГ")

    day, month, year = map(int, match.groups())
    return day, month, year


def _sum_digits(n: int) -> int:
    return sum(int(d) for d in str(abs(n)) if d.isdigit())


def _reduce_to_one_digit(n: int) -> int:
    """
    Сводим число к однозначному (1–9), суммируя цифры, пока > 9.
    """
    n = abs(n)
    while n > 9:
        n = _sum_digits(n)
    return n


def _calculate_zone3(day: int, month: int, year: int, zone3: Dict[str, Any]) -> tuple[int, int, str, str]:
    """
    Расчёт для 3_zone.json (Число жизненного пути).

    1) Число 1 — сумма всех цифр даты рождения.
    2) Число 2 — сумма цифр числа 1 (сводим к однозначному).
    Интерпретацию берём по цифре 2.
    """
    # формируем строку из даты в виде ДДММГГГГ и суммируем все цифры
    date_digits = f"{day:02d}{month:02d}{year:04d}"
    num1 = sum(int(d) for d in date_digits)

    num2 = _reduce_to_one_digit(num1)
    key = str(num2)

    if key not in zone3:
        raise KeyError(f"В 3_zone.json нет интерпретации для числа {num2}")

    title = zone3[key].get("title", "").strip()
    description = zone3[key].get("description", "").strip()

    return num1, num2, title, description


def _first_nonzero_day_digit(day: int) -> int:
    """
    Берём первую цифру дня, при этом если день начинается с 0
    (например, 01, 02, 03), используем вторую цифру.
    """
    day_str = f"{day:02d}"
    if day_str[0] != "0":
        return int(day_str[0])
    # если первый ноль — берём вторую цифру
    return int(day_str[1])


def _calculate_zone4(
    day: int,
    month: int,
    year: int,
    zone4_default: Dict[str, Any],
    zone4_2000: Dict[str, Any],
) -> tuple[int | None, int | None, str | None, str | None, str | None]:
    """
    Расчёт для 4_zone.json / 4_zone_2000.json.

    1) Число 1 — сумма всех цифр даты рождения (то же, что и в зоне 3).
    2) Берём первую цифру даты рождения (дня). Если день начинается на 0 — берём вторую.
       Умножаем её на 2.
    3) Число 3 = число 1 - (первая_цифра_дня * 2).
    4) Число 4 = сумма цифр числа 3, сведённая к однозначному.
    Интерпретацию (base) берём по числу 4.
    Shades берём по ключу \"ЧИСЛО_3/ЧИСЛО_4\" из словаря shades.
    Для людей до 2000 года включительно — берём 4_zone.json,
    для 2000 и дальше — 4_zone_2000.json.
    """
    # Число 1 (как в зоне 3)
    date_digits = f"{day:02d}{month:02d}{year:04d}"
    num1 = sum(int(d) for d in date_digits)

    first_digit = _first_nonzero_day_digit(day)
    num3 = num1 - first_digit * 2

    if num3 <= 0:
        # Не очень типичный, но возможный кейс — просто не даём интерпретацию
        return None, None, None, None, None

    num4 = _reduce_to_one_digit(num3)

    # Выбор набора интерпретаций по году рождения
    if year < 2000:
        zone4 = zone4_default
    else:
        zone4 = zone4_2000

    base_title = base_description = shade_title = shade_description = None
    base_key = str(num4)

    if isinstance(zone4, dict) and base_key in zone4:
        base_block = zone4[base_key].get("base") or {}
        base_title = base_block.get("title", "").strip() or None
        base_description = base_block.get("description", "").strip() or None

        shade_key = f"{num3}/{num4}"
        shades = zone4[base_key].get("shades") or {}
        shade_block = shades.get(shade_key)
        if shade_block:
            shade_title = shade_block.get("title", "").strip() or None
            shade_description = shade_block.get("description", "").strip() or None

    return num3, num4, base_title, base_description, shade_description


def _calculate_internal(birth_date: str) -> str:
    """
    Основная логика калькулятора пути предназначения.
    Использует 3_zone.json и 4_zone.json / 4_zone_2000.json.
    """
    day, month, year = _parse_birth_date(birth_date)
    data = _load_interpretations()

    zone3 = data["3"]
    zone4_default = data["4_default"]
    zone4_2000 = data["4_2000"]

    # ---- 3 зона (число жизненного пути) ----
    num1, num2, title3, desc3 = _calculate_zone3(day, month, year, zone3)

    # ---- 4 зона ----
    num3, num4, base_title4, base_desc4, shade_desc4 = _calculate_zone4(
        day, month, year, zone4_default, zone4_2000
    )

    parts: list[str] = []

    # Заголовок
    parts.append("🧭 <b>Путь предназначения</b>\n\n")
    parts.append(f"Дата: <b>{birth_date}</b>\n\n")

    # --------- Блок 3-й зоны ---------
    parts.append(f"<b>{title3}</b>\n")
    parts.append(f"<b>{num1}/{num2}</b>\n\n")
    parts.append(desc3.strip() + "\n\n")

    # --------- Блок 4-й зоны ---------
    if num3 is not None and num4 is not None and base_title4 and base_desc4:
        parts.append(f"<b>{base_title4}</b>\n")
        parts.append(f"<b>{num3}/{num4}</b>\n\n")
        parts.append(base_desc4.strip() + "\n\n")

        if shade_desc4:
            parts.append(shade_desc4.strip() + "\n\n")
    else:
        # Если для года 2000+ ещё нет интерпретаций
        if year >= 2000:
            parts.append(
                "<b>4-я зона</b>\n\n"
                "Интерпретации для 4-й зоны для людей, рождённых в 2000 году и позже, "
                "ещё не добавлены. Ключ для зоны: "
            )
            # если числа посчитались, показываем ключ
            if num3 is not None and num4 is not None:
                parts.append(f"<b>{num3}/{num4}</b>\n\n")
            else:
                parts.append("\n\n")

    return "".join(parts).strip()


def calculate(birth_date: str) -> str:
    """
    Публичная функция, которую вызывает бот.
    На вход получает строку даты рождения в формате ДД.ММ.ГГГГ,
    на выход — готовый текст с 3-й зоной и 4-й зоной пути предназначения.
    """
    try:
        return _calculate_internal(birth_date)
    except Exception:
        return (
            "🧭 <b>Путь предназначения</b>\n\n"
            f"Дата: <b>{birth_date}</b>\n\n"
            "Произошла ошибка при расчёте. "
            "Проверь формат даты (дд.мм.гггг) и попробуй ещё раз."
        )
