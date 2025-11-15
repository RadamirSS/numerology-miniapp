from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------

def arcana_reduce(n: int) -> int:
    """
    Сведение к аркану 1..22.
    Пока число > 22 — складываем цифры.
    """
    while n > 22:
        n = sum(int(d) for d in str(n))
    return n


def digit_reduce(n: int) -> int:
    """
    Обычная нумерология: оставляем число от 1 до 9.
    22 -> 4, 11 -> 2 и т.д.
    """
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


# ---------- СТРУКТУРЫ ДАННЫХ ----------

@dataclass
class PrimaryPoints:
    A: int  # день
    B: int  # месяц
    C: int  # год (сумма цифр)
    D: int  # сумма A+B+C
    center: int  # зона комфорта


@dataclass
class TripleZone:
    first: int
    second: int
    third: int


@dataclass
class MatrixDestiny:
    primary: PrimaryPoints
    portrait: TripleZone
    talents: TripleZone
    material_karma: TripleZone
    karmic_tail: TripleZone
    rod_square: Dict[str, int]
    balance: int
    ideal_partner: int
    ideal_profession: int
    purpose_personal: int
    purpose_social: int
    purpose_general: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary": asdict(self.primary),
            "portrait": asdict(self.portrait),
            "talents": asdict(self.talents),
            "material_karma": asdict(self.material_karma),
            "karmic_tail": asdict(self.karmic_tail),
            "rod_square": self.rod_square,
            "balance": self.balance,
            "ideal_partner": self.ideal_partner,
            "ideal_profession": self.ideal_profession,
            "purpose": {
                "personal": self.purpose_personal,
                "social": self.purpose_social,
                "general": self.purpose_general,
            },
        }


# ---------- ОСНОВНОЙ РАСЧЁТ ----------

def compute_matrix(date_str: str) -> MatrixDestiny:
    """
    date_str: строка формата 'DD.MM.YYYY', например '30.07.1987'
    """
    # базовая проверка формата
    d = datetime.strptime(date_str, "%d.%m.%Y")
    day, month, year = d.day, d.month, d.year

    # 1. Базовые точки ромба (личный квадрат)
    A = arcana_reduce(day)                         # лево
    B = arcana_reduce(month)                       # верх
    C = arcana_reduce(sum(int(c) for c in str(year)))  # право
    D = arcana_reduce(A + B + C)                   # низ
    center = arcana_reduce(A + B + C + D)          # центр

    primary = PrimaryPoints(A=A, B=B, C=C, D=D, center=center)

    # 2. Портрет (от A к центру)
    portrait_3 = arcana_reduce(A + center)
    portrait_2 = arcana_reduce(A + portrait_3)
    portrait = TripleZone(first=A, second=portrait_2, third=portrait_3)

    # 3. Таланты (от B к центру)
    talents_3 = arcana_reduce(B + center)
    talents_2 = arcana_reduce(B + talents_3)
    talents = TripleZone(first=B, second=talents_2, third=talents_3)

    # 4. Материальная карма (от C к центру)
    mk_3 = arcana_reduce(C + center)
    mk_2 = arcana_reduce(C + mk_3)
    material_karma = TripleZone(first=mk_3, second=mk_2, third=C)

    # 5. Кармический хвост (от D к центру)
    kt_3 = arcana_reduce(D + center)
    kt_2 = arcana_reduce(D + kt_3)
    karmic_tail = TripleZone(first=kt_3, second=kt_2, third=D)

    # 6. Квадрат рода
    E = arcana_reduce(A + B)  # верхний левый
    F = arcana_reduce(B + C)  # верхний правый
    I = arcana_reduce(C + D)  # нижний правый
    H = arcana_reduce(D + A)  # нижний левый
    rod_square = {"E": E, "F": F, "I": I, "H": H}

    # 7. Баланс, партнёр, профессия
    balance = arcana_reduce(mk_3 + kt_3)
    ideal_partner = arcana_reduce(kt_3 + balance)
    ideal_profession = arcana_reduce(mk_3 + balance)

    # 8. Предназначения
    personal_raw = (
        digit_reduce(A)
        + digit_reduce(B)
        + digit_reduce(C)
        + digit_reduce(D)
    )
    purpose_personal = (
        personal_raw if personal_raw <= 22 else arcana_reduce(personal_raw)
    )

    social_raw = (
        digit_reduce(E)
        + digit_reduce(F)
        + digit_reduce(I)
        + digit_reduce(H)
    )
    purpose_social = (
        social_raw if social_raw <= 22 else arcana_reduce(social_raw)
    )

    purpose_general = arcana_reduce(purpose_personal + purpose_social)

    return MatrixDestiny(
        primary=primary,
        portrait=portrait,
        talents=talents,
        material_karma=material_karma,
        karmic_tail=karmic_tail,
        rod_square=rod_square,
        balance=balance,
        ideal_partner=ideal_partner,
        ideal_profession=ideal_profession,
        purpose_personal=purpose_personal,
        purpose_social=purpose_social,
        purpose_general=purpose_general,
    )