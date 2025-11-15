from calculations import compute_matrix
from drawing import draw_matrix


def main():
    print("Матрица судьбы\n")
    date_str = input("Введите дату рождения в формате ДД.MM.ГГГГ: ").strip()

    try:
        matrix = compute_matrix(date_str)
    except Exception as e:
        print("Ошибка при разборе даты. Проверь формат (например, 30.07.1987).")
        print("Техническая ошибка:", e)
        return

    print("\nРасчёт завершён.")
    print("Основные точки:", matrix.primary)
    print("Портрет:", matrix.portrait)
    print("Таланты:", matrix.talents)
    print("Материальная карма:", matrix.material_karma)
    print("Кармический хвост:", matrix.karmic_tail)
    print("Квадрат рода:", matrix.rod_square)
    print("Баланс:", matrix.balance)
    print("Идеальный партнёр:", matrix.ideal_partner)
    print("Идеальная профессия:", matrix.ideal_profession)
    print(
        "Предназначение:",
        f"личное {matrix.purpose_personal}, "
        f"социальное {matrix.purpose_social}, "
        f"общее {matrix.purpose_general}",
    )

    filename = f"matrix_{date_str.replace('.', '')}.png"
    draw_matrix(matrix, filename=filename)
    print(f"\nКартинка матрицы сохранена в файле: {filename}")


if __name__ == "__main__":
    main()