import { useEffect, useState } from "react";
import { postJSON, getJSON } from "../api";
import type { MatrixState } from "../App";
import { formatBirthDateInput } from "../utils/format";

declare global {
  interface Window {
    Telegram?: any;
  }
}

interface Props {
  state: MatrixState;
  setState: React.Dispatch<React.SetStateAction<MatrixState>>;
}

export default function MatrixPage({ state, setState }: Props) {
  const [userBirthDate, setUserBirthDate] = useState<string | null>(null);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    const id = tg?.initDataUnsafe?.user?.id;
    if (!id) return;

    getJSON(`/users/by-telegram/${id}`)
      .then((u) => setUserBirthDate(u.birth_date))
      .catch(() => {
        setUserBirthDate(null);
      });
  }, []);

  function handleDateChange(value: string) {
    const formatted = formatBirthDateInput(value);
    setState((prev) => ({ ...prev, date: formatted }));
  }

  async function runMatrix(birth_date: string) {
    if (!birth_date || birth_date.length < 10) return;

    setState((prev) => ({
      ...prev,
      loading: true,
      error: null,
    }));

    try {
      const resp = await postJSON("/matrix/image", { birth_date });
      const imageUrl = resp.image_url || resp.imagePath || resp.image_path;
      const digitInterpretations = resp.digit_interpretations || null;
      
      setState((prev) => ({
        ...prev,
        imageUrl,
        digitInterpretations,
        loading: false,
      }));
    } catch (e: any) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: e?.message || "Ошибка при расчёте матрицы",
      }));
    }
  }

  return (
    <div className="card">
      <h2>Матрица судьбы</h2>
      <input
        placeholder="Дата рождения (дд.мм.гггг)"
        value={state.date}
        onChange={(e) => handleDateChange(e.target.value)}
      />
      <button 
        className="primary-button"
        onClick={() => runMatrix(state.date)}
        disabled={state.loading || !state.date || state.date.length < 10}
      >
        {state.loading ? "Считаем..." : "Рассчитать по дате"}
      </button>

      {userBirthDate && (
        <button
          className="primary-button"
          style={{ marginTop: 8 }}
          onClick={() => runMatrix(userBirthDate)}
          disabled={state.loading}
        >
          Пользователь ({userBirthDate})
        </button>
      )}

      {state.error && (
        <p style={{ marginTop: 8, color: "#f66", fontSize: 13 }}>
          {state.error}
        </p>
      )}

      {state.imageUrl && (
        <div style={{ marginTop: 16 }}>
          <img
            src={state.imageUrl}
            style={{ width: "100%", borderRadius: 16 }}
          />
        </div>
      )}

      {/* Блок интерпретации цифр матрицы */}
      {state.digitInterpretations && (
        <section className="matrix-digit-interpretations">
          <h2 className="section-title" style={{ marginTop: 24, marginBottom: 16 }}>
            Интерпретация цифр матрицы
          </h2>
          <div className="matrix-digit-interpretations__list">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((digit) => {
              const key = String(digit);
              const text =
                state.digitInterpretations?.[key] ??
                `Интерпретация цифры ${digit} (заглушка)`;

              return (
                <div
                  key={digit}
                  className="matrix-digit-interpretations__item"
                >
                  <div className="matrix-digit-interpretations__digit">
                    Цифра {digit}
                  </div>
                  <div className="matrix-digit-interpretations__text">
                    {text}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}