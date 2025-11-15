from __future__ import annotations

from typing import Union
from math import sin, cos, pi
import os

import matplotlib
matplotlib.use("Agg")  # ВАЖНО: headless режим, не вызывает GUI

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from calculations import MatrixDestiny


# ---------- ФОН: КРУГ С ГОДАМИ И ВЕРХНЕЙ ДУГОЙ ----------

def _draw_background(ax):
    """
    Рисует фон-геометрию (круг, деления, дуга, корона).
    """

    # радиус основного круга матрицы
    R_MAIN = 4.0

    # большой круг
    main_circle = plt.Circle(
        (0, 0),
        R_MAIN,
        fill=False,
        linewidth=2,
        linestyle="solid",
        edgecolor="#1a8f5c",
        alpha=0.9,
        zorder=1,
    )
    ax.add_patch(main_circle)

    # окружность для делений возрастов
    R_TICK_IN = R_MAIN - 0.25
    R_TICK_OUT = R_MAIN + 0.15

    def age_to_angle(age: float) -> float:
        return pi * (1 + (20 - age) / 40.0)

    for age in range(0, 71):
        ang = age_to_angle(age)
        x_in = R_TICK_IN * cos(ang)
        y_in = R_TICK_IN * sin(ang)
        x_out = R_TICK_OUT * cos(ang)
        y_out = R_TICK_OUT * sin(ang)

        if age % 10 == 0:
            lw = 1.6
            alpha = 0.9
        elif age % 5 == 0:
            lw = 1.2
            alpha = 0.6
        else:
            lw = 0.8
            alpha = 0.3

        ax.plot(
            [x_in, x_out],
            [y_in, y_out],
            color="#8088aa",
            linewidth=lw,
            alpha=alpha,
            zorder=1,
        )

        if age % 10 == 0:
            label_r = R_TICK_OUT + 0.25
            lx = label_r * cos(ang)
            ly = label_r * sin(ang)
            ax.text(
                lx,
                ly,
                str(age),
                ha="center",
                va="center",
                fontsize=8,
                color="#cfd8ff",
                zorder=1,
            )

    # подписи лет
    for age in (0, 10, 20, 30, 40, 50, 60, 70):
        ang = age_to_angle(age)
        r = R_TICK_OUT + 0.55
        x = r * cos(ang)
        y = r * sin(ang)
        ax.text(
            x,
            y,
            f"{age} лет",
            ha="center",
            va="center",
            fontsize=7,
            color="#9fa8da",
            zorder=1,
        )

    # верхняя дуга
    R_TOP = 6.4
    CENTER_TOP_Y = -0.8

    angles = [i * pi / 180 for i in range(40, 140)]
    xs = [R_TOP * cos(a) for a in angles]
    ys = [CENTER_TOP_Y + R_TOP * sin(a) for a in angles]

    ax.plot(xs, ys, color="#1d7b4a", linewidth=1.4, alpha=0.7, zorder=1)

    # центральная линия к короне
    ax.plot(
        [0, 0],
        [R_MAIN, CENTER_TOP_Y + R_TOP - 0.9],
        color="#f2c94c",
        linewidth=1.2,
        alpha=0.7,
        zorder=1,
    )

    # корона: две окружности
    TOP_NODE_Y = CENTER_TOP_Y + R_TOP
    top_circle_outer = plt.Circle(
        (0, TOP_NODE_Y),
        1.0,
        fill=False,
        linewidth=2,
        edgecolor="#f2c94c",
        alpha=0.9,
        zorder=1,
    )
    top_circle_inner = plt.Circle(
        (0, TOP_NODE_Y),
        0.7,
        fill=False,
        linewidth=2,
        edgecolor="#f2c94c",
        alpha=0.5,
        zorder=1,
    )
    ax.add_patch(top_circle_outer)
    ax.add_patch(top_circle_inner)


# ---------- РИСОВАНИЕ МАТРИЦЫ ----------

def draw_matrix(
    matrix: MatrixDestiny,
    filename: str = "destiny_matrix.png",
    dpi: int = 200,
    background_path: str = "man.png",
) -> None:

    # --- ФИКС DPI ---
    try:
        dpi_value = float(dpi)
    except Exception:
        dpi_value = 300.0  # хардкод, чтобы не было ошибок

    m = matrix

    # создаём фигуру
    fig, ax = plt.subplots(figsize=(8, 8), dpi=dpi_value)
    ax.set_aspect("equal")
    ax.axis("off")

    # общий фон
    fig.patch.set_facecolor("#02110d")
    ax.set_facecolor("#02110d")

    # подложка-человек
    if background_path and os.path.exists(background_path):
        try:
            img = mpimg.imread(background_path)
            ax.imshow(
                img,
                extent=(-5.5, 5.5, -5.5, 5.5),
                zorder=0,
                aspect="auto",
                alpha=0.9,
            )
        except Exception as e:
            print(f"Ошибка загрузки '{background_path}': {e}")

    # геометрия
    _draw_background(ax)

    # -------- функции рисования --------

    def node(
        x: float,
        y: float,
        value: Union[int, str],
        radius: float = 0.3,
        facecolor: str = "#02231d",
        edgecolor: str = "#f2c94c",
        fontsize: int = 14,
        weight: str = "bold",
    ):
        circle = plt.Circle(
            (x, y),
            radius,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=2,
            zorder=2,
        )
        ax.add_patch(circle)
        ax.text(
            x,
            y,
            str(value),
            ha="center",
            va="center",
            fontsize=fontsize,
            color="white",
            weight=weight,
            zorder=3,
        )

    def line(x1, y1, x2, y2, alpha: float = 0.5):
        ax.plot(
            [x1, x2],
            [y1, y2],
            linestyle="solid",
            linewidth=1.5,
            color="#1d7b4a",
            alpha=alpha,
            zorder=2,
        )

    # -------- координаты --------

    A = (-2.3, 0.0)
    B = (0.0, 2.7)
    C = (2.3, 0.0)
    D = (0.0, -2.7)
    CENTER = (0.0, 0.0)

    E = (-2.3, 2.7)
    F = (2.3, 2.7)
    H = (-2.3, -2.7)
    I_ = (2.3, -2.7)

    P1 = A
    P2 = (-1.6, 0.0)
    P3 = (-0.7, 0.0)

    T1 = C
    T2 = (1.6, 0.0)
    T3 = (0.7, 0.0)

    MK1 = (1.7, -0.9)
    MK2 = (1.2, -1.8)
    MK3 = C

    KT1 = (-1.7, -0.9)
    KT2 = (-1.2, -1.8)
    KT3 = D

    # -------- линии --------

    line(*A, *B)
    line(*B, *C)
    line(*C, *D)
    line(*D, *A)

    line(*E, *F)
    line(*F, *I_)
    line(*I_, *H)
    line(*H, *E)

    line(-3.5, 0, 3.5, 0, alpha=0.25)
    line(0, -3.5, 0, 3.5, alpha=0.25)

    # -------- узлы --------

    node(*CENTER, m.primary.center, radius=0.35, facecolor="#b29825", edgecolor="#ffe082", fontsize=16)

    node(*A, m.primary.A, radius=0.35, facecolor="#4b3b8b")
    node(*B, m.primary.B, radius=0.35, facecolor="#1a8f5c")
    node(*C, m.primary.C, radius=0.35, facecolor="#b3433a")
    node(*D, m.primary.D, radius=0.35, facecolor="#992a3b")

    node(*E, m.rod_square["E"], radius=0.32, facecolor="#1d7b4a")
    node(*F, m.rod_square["F"], radius=0.32, facecolor="#1d7b4a")
    node(*H, m.rod_square["H"], radius=0.32, facecolor="#1d7b4a")
    node(*I_, m.rod_square["I"], radius=0.32, facecolor="#1d7b4a")

    node(*P1, m.portrait.first, radius=0.33, facecolor="#6c2c8a")
    node(*P2, m.portrait.second, radius=0.28, facecolor="#1d7b4a")
    node(*P3, m.portrait.third, radius=0.28, facecolor="#1a8f5c")

    node(*T1, m.talents.first, radius=0.33, facecolor="#206b3a")
    node(*T2, m.talents.second, radius=0.28, facecolor="#1d7b4a")
    node(*T3, m.talents.third, radius=0.28, facecolor="#1a8f5c")

    node(*MK1, m.material_karma.first, radius=0.28, facecolor="#c46b2a")
    node(*MK2, m.material_karma.second, radius=0.28, facecolor="#c46b2a")

    node(*KT1, m.karmic_tail.first, radius=0.28, facecolor="#c45782")
    node(*KT2, m.karmic_tail.second, radius=0.28, facecolor="#c45782")

    # корона — общее предназначение
    TOP_NODE_Y = 6.4 - 0.8
    ax.text(
        0,
        TOP_NODE_Y,
        str(m.purpose_general),
        ha="center",
        va="center",
        fontsize=16,
        color="#ffffff",
        weight="bold",
        zorder=2,
    )

    ax.text(
        0,
        4.6,
        f"Баланс: {m.balance}\n"
        f"Личное пред.: {m.purpose_personal}\n"
        f"Соц. пред.: {m.purpose_social}\n"
        f"Общее пред.: {m.purpose_general}",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#cfd8ff",
        zorder=2,
    )

    ax.text(
        -4.3,
        -4.4,
        f"Партнёр: {m.ideal_partner}",
        ha="left",
        va="top",
        fontsize=10,
        color="#ffcdd2",
        zorder=2,
    )
    ax.text(
        4.3,
        -4.4,
        f"Профессия: {m.ideal_profession}",
        ha="right",
        va="top",
        fontsize=10,
        color="#ffe0b2",
        zorder=2,
    )

    ax.set_xlim(-5.5, 5.5)
    ax.set_ylim(-5.5, 5.5)

    fig.tight_layout()
    fig.savefig(filename, facecolor=fig.get_facecolor())
    plt.close(fig)