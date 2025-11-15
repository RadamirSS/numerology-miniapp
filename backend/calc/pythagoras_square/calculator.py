from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any

# =====================================================
# ЗАГРУЗКА ИНТЕРПРЕТАЦИЙ ИЗ JSON
# =====================================================

_INTERPRETATIONS_CACHE: Dict[str, Any] | None = None


def _load_interpretations() -> Dict[str, Any]:
    """
    Загружаем interpretations/pifagor.json один раз и кешируем.
    Путь считается от корня проекта: ../.. от этого файла → numerology_bot/.
    При необходимости можно подправить количество parents.
    """
    global _INTERPRETATIONS_CACHE
    if _INTERPRETATIONS_CACHE is not None:
        return _INTERPRETATIONS_CACHE

    # calculators/pythagoras_square/calculator.py
    base_dir = Path(__file__).resolve().parents[2]
    json_path = base_dir / "interpretations" / "pifagor.json"

    with json_path.open("r", encoding="utf-8") as f:
        _INTERPRETATIONS_CACHE = json.load(f)

    return _INTERPRETATIONS_CACHE


@dataclass
class PythagorasResult:
    birth_date: str
    digits_for_matrix: List[int]
    counts: Dict[int, int]
    third_zone: int
    third_zone_reduced: int
    fourth_zone: int
    fourth_zone_reduced: int

    row_147: int
    row_258: int
    row_369: int
    diag_357: int
    diag_159: int


# =====================================================
# ПУБЛИЧНАЯ ФУНКЦИЯ ДЛЯ БОТА
# =====================================================

def calculate(birth_date: str) -> str:
    """
    Главная функция, которую вызывает бот.

    На вход получает строку даты в формате ДД.MM.ГГГГ (или D.M.YYYY),
    на выход отдаёт готовый текст для PDF.
    """
    try:
        result = _calculate_internal(birth_date)
    except Exception:
        return (
            "🟩 <b>Квадрат Пифагора</b>\n\n"
            f"Дата: <b>{birth_date}</b>\n\n"
            "Произошла ошибка при расчёте квадрата. "
            "Проверь формат даты (дд.мм.гггг) и попробуй ещё раз."
        )

    parts: List[str] = []

    # Заголовок
    parts.append("🟩 <b>Квадрат Пифагора (психоматрица)</b>")
    parts.append(f"Дата рождения: <b>{result.birth_date}</b>\n")

    # Формула и зоны
    parts.append(_format_formula_block(result))

    # Психоматрица
    parts.append("ПСИХОМАТРИЦА:")
    parts.append(_render_matrix(result.counts))

    # Сводка по цифрам
    parts.append(_format_counts_summary(result.counts))

    # Интерпретации цифр
    parts.append(_interpret_digits_block(result.counts))

    # Строки и диагонали
    parts.append(_interpret_rows_and_diagonals_block(result))

    # Психотип
    parts.append(_interpret_psychotype_block(result))

    # Переливание энергий
    parts.append(_pereliv_block())

    return "\n\n".join(parts)


# =====================================================
# РАСЧЁТ ЦИФР И ЗОН
# =====================================================

def _calculate_internal(birth_date: str) -> PythagorasResult:
    # Все цифры даты для суммы
    raw_digits = [int(ch) for ch in birth_date if ch.isdigit()]
    if len(raw_digits) < 3:
        raise ValueError("Недостаточно цифр в дате")

    # --------- ВАЖНО: корректный расчёт первой цифры дня ---------
    # Поддерживаем форматы вроде "03.11.1990", "3.11.1990", "03-11-1990"
    m = re.match(r"\s*(\d{1,2})[.\-\/]", birth_date)
    if not m:
        raise ValueError("Неверный формат даты (ожидается дд.мм.гггг)")

    day = int(m.group(1))  # "03" → 3, "18" → 18
    if not (1 <= day <= 31):
        raise ValueError("Неверный день в дате рождения")

    # Логика:
    #  03 → 3 (первая значащая цифра дня)
    #  18 → 1 (первая цифра числа дня)
    if day < 10:
        day_first_digit = day
    else:
        day_first_digit = day // 10
    # --------------------------------------------------------------

    # Сумма цифр даты
    sum_digits = sum(raw_digits)

    # 3-я зона: сумма и свёртка до 12
    third_zone = sum_digits
    third_zone_reduced = _reduce_to_12(third_zone)

    # 4-я зона: сумма − 2 * первая цифра дня (уже корректно: 03 → 3)
    fourth_zone = third_zone - 2 * day_first_digit
    if fourth_zone <= 0:
        fourth_zone = abs(fourth_zone)
    fourth_zone_reduced = _reduce_to_12(fourth_zone)

    # Цифры для матрицы (без нулей)
    digits_for_matrix: List[int] = []
    for ch in birth_date:
        if ch.isdigit() and ch != "0":
            digits_for_matrix.append(int(ch))

    for value in (third_zone, third_zone_reduced, fourth_zone, fourth_zone_reduced):
        for ch in str(value):
            if ch != "0":
                digits_for_matrix.append(int(ch))

    # Подсчёт 1–9
    counts: Dict[int, int] = {d: 0 for d in range(1, 10)}
    for d in digits_for_matrix:
        if d in counts:
            counts[d] += 1

    # Строки и диагонали
    row_147 = counts[1] + counts[4] + counts[7]
    row_258 = counts[2] + counts[5] + counts[8]
    row_369 = counts[3] + counts[6] + counts[9]
    diag_357 = counts[3] + counts[5] + counts[7]
    diag_159 = counts[1] + counts[5] + counts[9]

    return PythagorasResult(
        birth_date=birth_date,
        digits_for_matrix=digits_for_matrix,
        counts=counts,
        third_zone=third_zone,
        third_zone_reduced=third_zone_reduced,
        fourth_zone=fourth_zone,
        fourth_zone_reduced=fourth_zone_reduced,
        row_147=row_147,
        row_258=row_258,
        row_369=row_369,
        diag_357=diag_357,
        diag_159=diag_159,
    )


def _reduce_to_12(n: int) -> int:
    n = abs(int(n))
    while n > 12:
        s = 0
        t = n
        while t > 0:
            s += t % 10
            t //= 10
        n = s
    return n


# =====================================================
# ОФОРМЛЕНИЕ ВЫВОДА
# =====================================================

def _format_formula_block(result: PythagorasResult) -> str:
    return (
        "<b>РАЗДЕЛ 1. Формула и расчёт</b>\n\n"
        f"Сумма цифр даты рождения: {result.third_zone}\n"
        f"Третья зона (путь предназначения): {result.third_zone}/{result.third_zone_reduced}\n"
        f"Четвёртая зона (кармическая): {result.fourth_zone}/{result.fourth_zone_reduced}\n\n"
        "До числа 12 включительно значения не сворачиваются.\n"
        "Для построения психоматрицы учитываются все цифры даты рождения,\n"
        "а также цифры третьей и четвёртой зон (включая их свёртки).\n"
    )


def _render_matrix(counts: Dict[int, int]) -> str:
    def cell(d: int) -> str:
        n = counts.get(d, 0)
        if n <= 0:
            return "—"
        return str(d) * n

    rows = [
        [cell(1), cell(4), cell(7)],
        [cell(2), cell(5), cell(8)],
        [cell(3), cell(6), cell(9)],
    ]

    col_widths = [max(len(rows[r][c]) for r in range(3)) for c in range(3)]

    def draw_row(row_vals: List[str]) -> str:
        parts = []
        for i, val in enumerate(row_vals):
            width = col_widths[i]
            parts.append(" " + val.ljust(width) + " ")
        return "│" + "│".join(parts) + "│"

    top = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
    mid = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
    bot = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"

    lines = [top, draw_row(rows[0]), mid, draw_row(rows[1]), mid, draw_row(rows[2]), bot]
    return "\n".join(lines)


def _format_counts_summary(counts: Dict[int, int]) -> str:
    lines = ["<b>Сводка по цифрам (1–9):</b>"]
    for d in range(1, 10):
        lines.append(f"{d}: {counts.get(d, 0)}")
    return "\n".join(lines)


# =====================================================
# ИНТЕРПРЕТАЦИИ ЧЕРЕЗ JSON
# =====================================================

def _interpret_digits_block(counts: Dict[int, int]) -> str:
    parts: List[str] = []
    parts.append("<b>РАЗДЕЛ 2. Трактовки цифр (1–9)</b>")

    for digit in range(1, 10):
        parts.append(_interpret_single_digit(digit, counts[digit]))

    return "\n\n".join(parts)


def _interpret_single_digit(digit: int, count: int) -> str:
    data = _load_interpretations()["digits"][str(digit)]
    header = data.get("header", "")

    # Маппинг количества → ключ в JSON
    if digit == 1:
        if count <= 0:
            key = "0"
        elif count == 1:
            key = "1"
        elif count == 2:
            key = "2"
        elif count == 3:
            key = "3"
        elif count == 4:
            key = "4"
        elif count == 5:
            key = "5"
        elif count == 6:
            key = "6"
        elif count == 7:
            key = "7"
        else:
            key = "8+"
    elif digit == 2:
        if count <= 0:
            key = "0"
        elif count == 1:
            key = "1"
        elif count == 2:
            key = "2"
        elif count == 3:
            key = "3"
        elif count == 4:
            key = "4"
        elif count == 5:
            key = "5"
        else:
            key = "6+"
    else:
        # для 3–9: 0 / 1 / 2 / 3 / 4+
        if count <= 0:
            key = "0"
        elif count == 1:
            key = "1"
        elif count == 2:
            key = "2"
        elif count == 3:
            key = "3"
        else:
            key = "4+"

    text = data.get(key, "")
    return (header + "\n\n" + text).strip()


def _interpret_rows_and_diagonals_block(result: PythagorasResult) -> str:
    interp = _load_interpretations()
    parts: List[str] = []
    parts.append("<b>РАЗДЕЛ 3. Интерпретация строк и диагоналей</b>")

    # Строка 1–4–7
    n = result.row_147
    if n == 0:
        key = "0"
    elif n == 1:
        key = "1"
    elif n == 2:
        key = "2"
    elif n == 3:
        key = "3"
    elif n == 4:
        key = "4"
    elif n == 5:
        key = "5"
    else:
        key = "6+"
    txt_147 = interp["rows"]["147"][key]
    parts.append(f"Строка 1–4–7 (цели, достижения): {n} цифр.\n{txt_147}")

    # Строка 2–5–8
    n = result.row_258
    if n == 0:
        key = "0"
    elif n in (1, 2):
        key = "1-2"
    elif n == 3:
        key = "3"
    elif n == 4:
        key = "4"
    elif n == 5:
        key = "5"
    else:
        key = "6+"
    txt_258 = interp["rows"]["258"][key]
    parts.append(f"Строка 2–5–8 (семья, партнёрство): {n} цифр.\n{txt_258}")

    # Строка 3–6–9
    n = result.row_369
    if n == 0:
        key = "0"
    elif n in (1, 2):
        key = "1-2"
    elif n == 3:
        key = "3"
    elif n in (4, 5):
        key = "4-5"
    else:
        key = "6+"
    txt_369 = interp["rows"]["369"][key]
    parts.append(f"Строка 3–6–9 (стабильность, привычки): {n} цифр.\n{txt_369}")

    # Диагональ 3–5–7
    n = result.diag_357
    if n == 0:
        key = "0"
    elif n == 1:
        key = "1"
    elif n == 2:
        key = "2"
    elif 3 <= n <= 5:
        key = "3-5"
    else:
        key = "6+"
    txt_357 = interp["diagonals"]["357"][key]
    # Доп. текст, если пусто и много двоек
    extra = ""
    if n == 0 and result.counts[2] >= 3:
        extra = " " + interp["diagonals"]["357"].get("extra_2_many", "")
    parts.append(f"Диагональ 3–5–7 (темперамент): {n} цифр.\n{txt_357}{extra}")

    # Диагональ 1–5–9
    n = result.diag_159
    if n <= 3:
        key = "0-3"
    elif 4 <= n <= 5:
        key = "4-5"
    else:
        key = "6+"
    d159 = interp["diagonals"]["159"]
    base = d159.get("base", "")
    spec = d159.get(key, "")
    parts.append(
        f"Диагональ 1–5–9 (духовность, общественная значимость): {n} цифр.\n"
        f"{base}\n\n{spec}"
    )

    return "\n\n".join(parts)


def _interpret_psychotype_block(result: PythagorasResult) -> str:
    interp = _load_interpretations()["psychotype"]
    n1 = result.counts[1]
    n2 = result.counts[2]

    if n1 > n2:
        txt = interp["1_gt_2"]
    elif n2 > n1:
        txt = interp["2_gt_1"]
    else:
        txt = interp["equal"]

    return (
        "<b>РАЗДЕЛ 4. Психотип</b>\n\n"
        f"Единиц: {n1}, двоек: {n2}.\n\n"
        f"{txt}"
    )


def _pereliv_block() -> str:
    interp = _load_interpretations()["pereliv"]["text"]
    return "<b>ПЕРЕЛИВАНИЕ ЭНЕРГИЙ</b>\n\n" + interp
