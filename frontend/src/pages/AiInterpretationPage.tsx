import { useEffect } from "react";
import jsPDF from "jspdf";
import { postJSON, getJSON } from "../api";
import { formatBirthDateInput } from "../utils/format";
import type { AiState } from "../App";

declare global {
  interface Window {
    Telegram?: any;
  }
}

interface Props {
  state: AiState;
  setState: React.Dispatch<React.SetStateAction<AiState>>;
}

export default function AiInterpretationPage({ state, setState }: Props) {

  // Пытаемся подтянуть дату рождения пользователя из Telegram (только если не заполнена)
  useEffect(() => {
    if (state.birthDate) return; // Если дата уже есть, не перезаписываем
    
    const tg = window.Telegram?.WebApp;
    const id = tg?.initDataUnsafe?.user?.id;
    if (!id) return;
    
    getJSON(`/users/by-telegram/${id}`)
      .then((u) => {
        if (u.birth_date) {
          setState((prev) => ({ ...prev, birthDate: u.birth_date }));
        }
      })
      .catch(() => {
        // Игнорируем ошибки
      });
  }, [state.birthDate, setState]);

  function handleDateChange(value: string) {
    const formatted = formatBirthDateInput(value);
    setState((prev) => ({ ...prev, birthDate: formatted }));
  }

  async function handleGenerate() {
    if (!state.birthDate || state.birthDate.length < 10) {
      setState((prev) => ({ ...prev, error: "Введите дату рождения в формате ДД.ММ.ГГГГ" }));
      return;
    }

    setState((prev) => ({
      ...prev,
      loading: true,
      error: null,
      report: null,
      profile: null,
    }));

    try {
      const response = await postJSON("/ai/interpretation", {
        birth_date: state.birthDate,
      });

      if (response.status === "ok") {
        setState((prev) => ({
          ...prev,
          profile: response.profile,
          report: response.report,
          loading: false,
        }));
      } else {
        setState((prev) => ({
          ...prev,
          error: "Не удалось сгенерировать отчёт",
          loading: false,
        }));
      }
    } catch (err: any) {
      // Обработка различных типов ошибок
      let errorMessage = "Произошла ошибка при генерации отчёта. Попробуйте позже.";
      if (err.message?.includes("503") || err.message?.includes("не инициализирована")) {
        errorMessage = "AI база знаний ещё не инициализирована. Попросите администратора запустить индексацию книг.";
      } else if (err.message?.includes("502") || err.message?.includes("OpenAI")) {
        errorMessage = "Ошибка при генерации отчёта. Проверьте настройки OpenAI API.";
      }
      setState((prev) => ({
        ...prev,
        error: errorMessage,
        loading: false,
      }));
    }
  }

  function handleDownloadPdf() {
    if (!state.report) return;

    const doc = new jsPDF({ unit: "pt", format: "a4" });
    doc.setFont("Helvetica", "normal");
    
    // Заголовок
    doc.setFontSize(16);
    doc.text("AI интерпретация по дате рождения", 40, 50);
    
    // Дата рождения
    if (state.birthDate) {
      doc.setFontSize(12);
      doc.text(`Дата рождения: ${state.birthDate}`, 40, 80);
    }
    
    // Текст интерпретации
    doc.setFontSize(12);
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 40;
    const maxWidth = pageWidth - 2 * margin;
    
    const lines = doc.splitTextToSize(state.report, maxWidth);
    let y = 120;
    const lineHeight = 14;
    const pageHeight = doc.internal.pageSize.getHeight();
    
    lines.forEach((line: string) => {
      if (y + lineHeight > pageHeight - 40) {
        doc.addPage();
        y = 40;
      }
      doc.text(line, margin, y);
      y += lineHeight;
    });
    
    // Имя файла
    const filename = state.birthDate
      ? `ai_interpretation_${state.birthDate.replace(/\./g, "_")}.pdf`
      : "ai_interpretation.pdf";
    
    doc.save(filename);
  }

  return (
    <div className="card">
      <h2>AI интерпретация</h2>
      <p style={{ fontSize: 14, color: "var(--text-muted)", marginTop: 8 }}>
        Получите персональный отчёт на основе вашей даты рождения и всех загруженных книг по нумерологии.
      </p>

      <div style={{ marginTop: 20 }}>
        <label style={{ display: "block", marginBottom: 8, fontSize: 14 }}>
          Дата рождения (ДД.ММ.ГГГГ)
        </label>
        <input
          type="text"
          placeholder="02.08.1995"
          value={state.birthDate}
          onChange={(e) => handleDateChange(e.target.value)}
          maxLength={10}
          style={{ marginTop: 0 }}
        />
      </div>

      <button
        onClick={handleGenerate}
        disabled={state.loading || !state.birthDate || state.birthDate.length < 10}
        className="primary-button"
        style={{ marginTop: 16 }}
      >
        {state.loading ? "Генерация отчёта..." : "Сгенерировать отчёт"}
      </button>

      {state.error && (
        <div className="error-message" style={{ marginTop: 16 }}>
          <span className="error-icon">⚠️</span> {state.error}
        </div>
      )}

      {state.loading && (
        <div style={{ marginTop: 16, textAlign: "center", color: "var(--text-muted)" }}>
          <div style={{ fontSize: 14 }}>⏳ Генерация отчёта, пожалуйста подождите...</div>
        </div>
      )}

      {state.report && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ marginBottom: 12 }}>Ваш отчёт</h3>
          <div
            style={{
              background: "rgba(1, 12, 10, 0.9)",
              padding: 16,
              borderRadius: 12,
              border: "1px solid var(--border-soft)",
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
            }}
          >
            {state.report.split("\n\n").map((paragraph, idx) => (
              <p key={idx} style={{ marginBottom: paragraph ? 12 : 0 }}>
                {paragraph}
              </p>
            ))}
          </div>
          {state.report && (
            <button
              className="primary-button"
              onClick={handleDownloadPdf}
              style={{ marginTop: 12 }}
            >
              📥 Скачать PDF
            </button>
          )}
        </div>
      )}

      {state.profile && state.report && (
        <details style={{ marginTop: 16, fontSize: 13, color: "var(--text-muted)" }}>
          <summary style={{ cursor: "pointer", marginBottom: 8 }}>
            Показать профиль (техническая информация)
          </summary>
          <pre
            style={{
              background: "rgba(1, 12, 10, 0.9)",
              padding: 12,
              borderRadius: 8,
              overflow: "auto",
              fontSize: 12,
            }}
          >
            {JSON.stringify(state.profile, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

