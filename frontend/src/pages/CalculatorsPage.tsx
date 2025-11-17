import { useEffect, useState } from "react";
import { postJSON } from "../api";
import type { CalcState } from "../App";
import { formatBirthDateInput } from "../utils/format";
import { PythagorasSquare } from "../components/PythagorasSquare";
import { useUserStore } from "../store/userStore";

const CALCS = [
  { id: "money_code", title: "💰 Денежный код" },
  { id: "life_code", title: "✨ Жизненный код" },
  { id: "destiny_path", title: "🧭 Путь предназначения" },
  { id: "birth_decoding", title: "📜 Расшифровка даты рождения" },
  { id: "pythagoras_square", title: "🟩 Квадрат Пифагора" },
  { id: "prognosis", title: "📈 Прогностика" },
];

declare global {
  interface Window {
    Telegram?: any;
  }
}

interface Props {
  state: CalcState;
  setState: React.Dispatch<React.SetStateAction<CalcState>>;
}

// Функция для парсинга квадрата Пифагора из текстового формата
function parsePythagorasMatrix(text: string): (string | null)[][] | null {
  // Ищем блок с таблицей (между ПСИХОМАТРИЦА: и следующим разделом)
  const matrixMatch = text.match(/ПСИХОМАТРИЦА:[\s\S]*?(┌[─┬┐\s│└┴┘]+)/);
  if (!matrixMatch) return null;
  
  const tableText = matrixMatch[1];
  const lines = tableText.split('\n').filter(l => l.trim());
  
  // Парсим строки таблицы (пропускаем границы ┌─┐, ├─┼─┤ и └─┘)
  const rows: (string | null)[][] = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    // Пропускаем разделительные строки (├─┼─┤) и границы (┌─┐, └─┘)
    if (line.includes('│') && !line.match(/^[┌├└]/) && !line.match(/^[┐┤┘]/)) {
      // Разбиваем по │ и извлекаем значения ячеек
      const cells = line.split('│').slice(1, -1).map(c => {
        // Убираем пробелы по краям, но сохраняем все цифры внутри
        const trimmed = c.trim();
        // Если ячейка пустая или содержит только "—", возвращаем null
        if (!trimmed || trimmed === '—' || trimmed === '–' || trimmed === '-') {
          return null;
        }
        // Оставляем только цифры (для случаев типа "333", "99" и т.д.)
        const digits = trimmed.replace(/[^\d]/g, '');
        return digits || null;
      });
      if (cells.length === 3) {
        rows.push(cells);
      }
    }
  }
  
  if (rows.length === 3) {
    // Порядок ячеек в квадрате Пифагора:
    // 1 4 7 (первая строка)
    // 2 5 8 (вторая строка)
    // 3 6 9 (третья строка)
    // rows уже содержит правильный порядок, просто возвращаем как есть
    return rows;
  }
  
  return null;
}

// Компонент для отображения квадрата Пифагора
function PythagorasSquareView({ html }: { html: string }) {
  const matrix = parsePythagorasMatrix(html);
  
  // Разделяем HTML на части: до матрицы, матрица, после матрицы
  const parts = html.split(/ПСИХОМАТРИЦА:/);
  const beforeMatrix = parts[0];
  const afterMatrixPart = parts[1] || '';
  const matrixEndMatch = afterMatrixPart.match(/└[─┴┘\s│]+/);
  const matrixEndIndex = matrixEndMatch ? afterMatrixPart.indexOf(matrixEndMatch[0]) + matrixEndMatch[0].length : 0;
  const afterMatrix = afterMatrixPart.substring(matrixEndIndex);
  
  // Преобразуем матрицу в массив для компонента PythagorasSquare
  const cells: (string | null)[] = matrix 
    ? matrix.flat().map(cell => {
        // Если ячейка null или пустая, возвращаем null (компонент покажет "–")
        if (!cell || (typeof cell === 'string' && (cell.trim() === '' || cell === '—' || cell === '–' || cell === '-'))) {
          return null;
        }
        // Возвращаем значение как есть (уже очищено от нецифровых символов в парсере)
        return cell;
      })
    : [];
  
  return (
    <>
      {/* Текст до матрицы */}
      {beforeMatrix && (
        <div dangerouslySetInnerHTML={{ __html: beforeMatrix }} />
      )}
      
      {/* Красивая сетка матрицы */}
      {matrix && cells.length === 9 && (
        <PythagorasSquare cells={cells} />
      )}
      
      {/* Если не удалось распарсить матрицу, показываем весь блок как есть */}
      {!matrix && (
        <div style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', fontSize: '12px', background: 'transparent' }}>
          {html.includes('ПСИХОМАТРИЦА:') ? (
            <>
              <div dangerouslySetInnerHTML={{ __html: beforeMatrix }} />
              <div style={{ margin: '16px 0', padding: '12px', background: 'transparent' }}>
                {afterMatrixPart.substring(0, matrixEndIndex || afterMatrixPart.length)}
              </div>
              {afterMatrix && <div dangerouslySetInnerHTML={{ __html: afterMatrix }} />}
            </>
          ) : (
            <div dangerouslySetInnerHTML={{ __html: html }} />
          )}
        </div>
      )}
      
      {/* Текст после матрицы */}
      {afterMatrix && matrix && (
        <div dangerouslySetInnerHTML={{ __html: afterMatrix }} />
      )}
    </>
  );
}

// Функция для рендеринга интерпретации с разбивкой на абзацы
function renderInterpretation(textOrHtml: string, isPythagoras: boolean = false) {
  if (isPythagoras) {
    // Для квадрата Пифагора используем специальный компонент
    return <PythagorasSquareView html={textOrHtml} />;
  }
  
  // Проверяем, есть ли HTML-теги
  const hasHtmlTags = /<[a-z][\s\S]*>/i.test(textOrHtml);
  
  if (hasHtmlTags) {
    // Если есть HTML, используем dangerouslySetInnerHTML
    return <div dangerouslySetInnerHTML={{ __html: textOrHtml }} />;
  }
  
  // Если это обычный текст, разбиваем на абзацы
  const paragraphs = textOrHtml.split(/\n\n+/).filter(p => p.trim());
  
  return (
    <>
      {paragraphs.map((paragraph, idx) => (
        <p key={idx} className="interpretation-paragraph">
          {paragraph.split('\n').map((line, lineIdx, lines) => (
            <span key={lineIdx}>
              {line}
              {lineIdx < lines.length - 1 && <br />}
            </span>
          ))}
        </p>
      ))}
    </>
  );
}

export default function CalculatorsPage({ state, setState }: Props) {
  const { profile } = useUserStore();
  
  // Проверка доступа по тарифу
  const hasAccess = profile?.tariff === 'pro';
  
  // Выбранный калькулятор (ещё не подтверждён кнопкой)
  const [selectedCalculatorId, setSelectedCalculatorId] = useState<string>(
    state.currentCalc || "money_code"
  );
  // Активный калькулятор (по которому был выполнен расчёт)
  const activeCalculatorId = state.currentCalc;

  // Автоматически подставляем дату из профиля, если она есть и поле пустое
  useEffect(() => {
    if (profile?.birth_date && !state.date) {
      setState((prev) => ({ ...prev, date: profile.birth_date }));
    }
  }, [profile?.birth_date, state.date]);

  function handleDateChange(value: string) {
    const formatted = formatBirthDateInput(value);
    setState((prev) => ({ ...prev, date: formatted }));
  }

  // Обработчик выбора калькулятора - только меняет выбор, не выполняет расчёт
  function handleCalculatorChange(calculatorId: string) {
    setSelectedCalculatorId(calculatorId);
    // НЕ вызываем расчёт здесь, не меняем state.currentCalc
  }

  // Обработчик кнопки "Рассчитать по дате" - единственная точка запуска расчёта
  async function handleCalculate(birth_date: string) {
    if (!birth_date || birth_date.length < 10) {
      // Можно показать подсказку пользователю
      return;
    }

    if (!selectedCalculatorId) {
      // Можно показать подсказку пользователю
      return;
    }

    setState((prev) => ({
      ...prev,
      loading: true,
      error: null,
    }));

    try {
      const resp = await postJSON(`/calculators/${selectedCalculatorId}`, {
        birth_date,
      });
      
      // При успешном ответе:
      // 1. Сохраняем результат
      // 2. Устанавливаем activeCalculatorId = selectedCalculatorId
      setState((prev) => ({
        ...prev,
        html: resp.result_html,
        currentCalc: selectedCalculatorId, // Теперь это активный калькулятор
        loading: false,
      }));
    } catch (e: any) {
      // При ошибке показываем сообщение, но НЕ трогаем старый результат
      setState((prev) => ({
        ...prev,
        loading: false,
        error: e?.message || "Ошибка при расчёте",
      }));
      // activeCalculatorId и result остаются прежними
    }
  }

  // Старая функция runCalc оставляем для совместимости с кнопкой "Пользователь"
  async function runCalc(birth_date: string) {
    await handleCalculate(birth_date);
  }

  // Функция для перехода к выбору тарифа
  function handleGoToTariffs() {
    // Отправляем событие для переключения на вкладку профиля
    window.dispatchEvent(new CustomEvent('switchTab', { detail: 'profile' }));
    // Небольшая задержка для открытия модалки тарифов
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('openTariffModal'));
    }, 300);
  }

  // Если нет доступа, показываем блок с сообщением
  if (!hasAccess) {
    return (
      <div className="card">
        <h2>Калькуляторы</h2>
        <div
          style={{
            marginTop: 24,
            padding: 24,
            background: "rgba(1, 12, 10, 0.6)",
            borderRadius: 12,
            border: "1px solid var(--border-soft)",
            textAlign: "center",
          }}
        >
          <p style={{ fontSize: 16, color: "var(--text-main)", marginBottom: 16 }}>
            Раздел «Калькуляторы» доступен в тарифе <strong>Профессиональный</strong>.
          </p>
          <p style={{ fontSize: 14, color: "var(--text-muted)", marginBottom: 20 }}>
            Выберите тариф в личном кабинете.
          </p>
          <button
            onClick={handleGoToTariffs}
            className="btn-primary"
            style={{ width: "auto", minWidth: "200px" }}
          >
            Перейти к тарифам
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Калькуляторы</h2>

      <select
        value={selectedCalculatorId}
        onChange={(e) => handleCalculatorChange(e.target.value)}
      >
        {CALCS.map((c) => (
          <option key={c.id} value={c.id}>
            {c.title}
          </option>
        ))}
      </select>

      <input
        placeholder="Дата рождения (дд.мм.гггг)"
        value={state.date}
        onChange={(e) => handleDateChange(e.target.value)}
      />
      <button 
        className="primary-button"
        onClick={() => handleCalculate(state.date)}
        disabled={state.loading || !state.date || state.date.length < 10 || !selectedCalculatorId}
      >
        {state.loading ? "Считаем..." : "Рассчитать по дате"}
      </button>

      {profile?.birth_date && profile.birth_date !== state.date && (
        <button
          className="primary-button"
          style={{ marginTop: 8 }}
          onClick={() => {
            setState((prev) => ({ ...prev, date: profile.birth_date }));
            runCalc(profile.birth_date);
          }}
          disabled={state.loading}
        >
          Использовать мою дату ({profile.birth_date})
        </button>
      )}

      {state.error && (
        <p style={{ marginTop: 8, color: "#f66", fontSize: 13 }}>
          {state.error}
        </p>
      )}

      {state.html && activeCalculatorId && (
        <div className="interpretation-container">
          {activeCalculatorId === "pythagoras_square" ? (
            renderInterpretation(state.html, true)
          ) : (
            renderInterpretation(state.html, false)
          )}
        </div>
      )}
    </div>
  );
}