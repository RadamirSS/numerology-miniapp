import { useState, useEffect, useRef } from "react";
import "./theme.css";
import MatrixPage from "./pages/MatrixPage";
import CalculatorsPage from "./pages/CalculatorsPage";
import ProfilePage from "./pages/ProfilePage";
import AiInterpretationPage from "./pages/AiInterpretationPage";
import { useUserStore } from "./store/userStore";
import { formatBirthDateInput } from "./utils/format";
import { processAvatarFile } from "./utils/avatar";
import { normalizeImageUrl } from "./api";

type Tab = "matrix" | "calculators" | "ai" | "profile";

export interface MatrixState {
  date: string;
  imageUrl: string | null;
  error: string | null;
  loading: boolean;
  digitInterpretations: Record<string, string> | null; // ключи "1".."9"
}

export interface CalcState {
  date: string;
  currentCalc: string;
  html: string;
  error: string | null;
  loading: boolean;
}

export interface AiState {
  birthDate: string;
  report: string | null;
  profile: any | null;
  loading: boolean;
  error: string | null;
}

declare global {
  interface Window {
    Telegram?: any;
  }
}

function App() {
  const [tab, setTab] = useState<Tab>("matrix");
  const { profile, loadProfileFromTelegram } = useUserStore();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [avatarMenuOpen, setAvatarMenuOpen] = useState(false);
  const [calculateModalOpen, setCalculateModalOpen] = useState(false);
  const [tempBirthDate, setTempBirthDate] = useState("");
  const userMenuRef = useRef<HTMLDivElement>(null);
  const avatarMenuRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [matrixState, setMatrixState] = useState<MatrixState>({
    date: "",
    imageUrl: null,
    error: null,
    loading: false,
    digitInterpretations: null,
  });

  const [calcState, setCalcState] = useState<CalcState>({
    date: "",
    currentCalc: "money_code",
    html: "",
    error: null,
    loading: false,
  });

  const [aiState, setAiState] = useState<AiState>({
    birthDate: "",
    report: null,
    profile: null,
    loading: false,
    error: null,
  });

  // Загрузка профиля при монтировании
  useEffect(() => {
    const tg = (window as any).Telegram?.WebApp;
    if (tg && typeof tg.ready === 'function') {
      tg.ready();
    }
    loadProfileFromTelegram();
  }, []);

  // Закрытие меню при клике вне их
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
      if (avatarMenuRef.current && !avatarMenuRef.current.contains(event.target as Node)) {
        setAvatarMenuOpen(false);
      }
    }
    
    if (userMenuOpen || avatarMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [userMenuOpen, avatarMenuOpen]);

  // Обработка загрузки аватара
  async function handleAvatarSelect(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const base64 = await processAvatarFile(file);
      const { updateProfile } = useUserStore.getState();
      await updateProfile({ avatar_url: base64 });
      setAvatarMenuOpen(false);
    } catch (err: any) {
      alert(err.message || "Ошибка загрузки аватара");
    }
    
    // Очищаем input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  // Получение имени пользователя для отображения
  function getDisplayName(): string {
    if (profile?.name) return profile.name;
    const tg = window.Telegram?.WebApp;
    const tgUser = tg?.initDataUnsafe?.user;
    if (tgUser?.first_name) {
      return tgUser.last_name ? `${tgUser.first_name} ${tgUser.last_name}` : tgUser.first_name;
    }
    return "Гость";
  }

  // Получение URL аватара для отображения
  function getAvatarUrl(): string | null {
    if (profile?.avatar_url) {
      if (profile.avatar_url.startsWith("data:")) return profile.avatar_url;
      return normalizeImageUrl(profile.avatar_url);
    }
    const tg = window.Telegram?.WebApp;
    const tgUser = tg?.initDataUnsafe?.user;
    return tgUser?.photo_url || null;
  }

  // Обработка клика на "Рассчитать меня"
  function handleCalculateMe() {
    setUserMenuOpen(false);
    
    if (profile?.birth_date) {
      // Если дата рождения есть, запускаем расчёт
      runCalculationWithDate(profile.birth_date);
    } else {
      // Если даты нет, открываем модалку для ввода
      setCalculateModalOpen(true);
    }
  }

  // Запуск расчёта с датой рождения
  function runCalculationWithDate(date: string) {
    // Обновляем состояние всех страниц с датой
    setMatrixState((prev) => ({ ...prev, date }));
    setCalcState((prev) => ({ ...prev, date }));
    setAiState((prev) => ({ ...prev, birthDate: date }));
    
    // Переключаемся на первую вкладку (Матрица) и запускаем расчёт
    setTab("matrix");
    
    // Небольшая задержка, чтобы состояние обновилось
    setTimeout(() => {
      // Триггерим расчёт матрицы (можно добавить автоматический запуск)
      // Пока просто устанавливаем дату, пользователь может нажать кнопку
    }, 100);
  }

  // Обработка подтверждения даты рождения в модалке
  async function handleConfirmBirthDate() {
    const formatted = formatBirthDateInput(tempBirthDate);
    
    if (!/^\d{2}\.\d{2}\.\d{4}$/.test(formatted)) {
      alert("Дата рождения должна быть в формате ДД.ММ.ГГГГ");
      return;
    }

    try {
      // Сохраняем дату в профиль
      const { updateProfile } = useUserStore.getState();
      await updateProfile({ birth_date: formatted });
      
      setCalculateModalOpen(false);
      setTempBirthDate("");
      
      // Запускаем расчёт
      runCalculationWithDate(formatted);
    } catch (err: any) {
      alert(err.message || "Ошибка сохранения даты рождения");
    }
  }

  const displayName = getDisplayName();
  const avatarUrl = getAvatarUrl();

  return (
    <div className="app-root">
      {/* Шапка приложения */}
      <div className="app-header">
        <h1 className="app-title">Numerolog Mini App</h1>
        <div style={{ position: "relative", display: "flex", alignItems: "center", gap: 8 }}>
          {/* Аватар с меню - показывается всегда */}
          <div style={{ position: "relative" }}>
            <div
              onClick={() => setAvatarMenuOpen(!avatarMenuOpen)}
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                overflow: "hidden",
                cursor: "pointer",
                border: "2px solid var(--gold)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "rgba(1, 12, 10, 0.9)",
              }}
            >
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt="Аватар"
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                  }}
                />
              ) : (
                <span style={{ fontSize: 16 }}>👤</span>
              )}
            </div>
            
            {/* Меню смены аватара */}
            {avatarMenuOpen && (
              <div
                ref={avatarMenuRef}
                style={{
                  position: "absolute",
                  top: "100%",
                  right: 0,
                  marginTop: 8,
                  backgroundColor: "var(--bg-card)",
                  border: "1px solid var(--gold)",
                  borderRadius: 8,
                  padding: 8,
                  zIndex: 1001,
                  minWidth: 150,
                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.5)",
                }}
              >
                <button
                  onClick={() => {
                    fileInputRef.current?.click();
                    setAvatarMenuOpen(false);
                  }}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "transparent",
                    border: "none",
                    color: "var(--text-main)",
                    cursor: "pointer",
                    textAlign: "left",
                    borderRadius: 4,
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "rgba(242, 201, 76, 0.1)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "transparent";
                  }}
                >
                  Сменить аватар
                </button>
              </div>
            )}
          </div>
          
          <div
            className="app-user-pill"
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}
          >
            <span>{displayName}</span>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: "none" }}
            onChange={handleAvatarSelect}
          />
          
          {/* Меню пользователя */}
          {userMenuOpen && (
            <div
              ref={userMenuRef}
              style={{
                position: "absolute",
                top: "100%",
                right: 0,
                marginTop: 8,
                backgroundColor: "var(--bg-card)",
                border: "1px solid var(--gold)",
                borderRadius: 8,
                padding: 8,
                zIndex: 1000,
                minWidth: 200,
                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.5)",
              }}
            >
              <button
                onClick={handleCalculateMe}
                style={{
                  width: "100%",
                  padding: "12px 16px",
                  background: "linear-gradient(135deg, var(--accent), var(--accent-light))",
                  border: "none",
                  color: "#03120f",
                  cursor: "pointer",
                  borderRadius: 8,
                  fontWeight: 600,
                  fontSize: 14,
                }}
              >
                Рассчитать меня
              </button>
            </div>
          )}
        </div>
      </div>

      <div style={{ padding: 16, paddingBottom: 88 }}>
        {tab === "matrix" && (
          <MatrixPage state={matrixState} setState={setMatrixState} />
        )}
        {tab === "calculators" && (
          <CalculatorsPage state={calcState} setState={setCalcState} />
        )}
        {tab === "ai" && (
          <AiInterpretationPage state={aiState} setState={setAiState} />
        )}
        {tab === "profile" && (
          <ProfilePage />
        )}
      </div>

      <div className="tabbar">
        <button
          className={tab === "matrix" ? "active" : ""}
          onClick={() => setTab("matrix")}
        >
          Матрица
        </button>
        <button
          className={tab === "calculators" ? "active" : ""}
          onClick={() => setTab("calculators")}
        >
          Калькуляторы
        </button>
        <button
          className={tab === "ai" ? "active" : ""}
          onClick={() => setTab("ai")}
        >
          AI интерпретация
        </button>
        <button
          className={tab === "profile" ? "active" : ""}
          onClick={() => setTab("profile")}
        >
          Личный кабинет
        </button>
      </div>

      {/* Модальное окно для ввода даты рождения */}
      {calculateModalOpen && (
        <div className="modal-overlay" onClick={() => setCalculateModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Введите дату рождения</h2>
              <button className="modal-close" onClick={() => setCalculateModalOpen(false)}>×</button>
            </div>
            
            <div style={{ marginTop: 20 }}>
              <label style={{ display: "block", marginBottom: 8, fontSize: 14 }}>
                Дата рождения (ДД.ММ.ГГГГ)
              </label>
              <input
                type="text"
                placeholder="02.08.1995"
                value={tempBirthDate}
                onChange={(e) => {
                  const formatted = formatBirthDateInput(e.target.value);
                  setTempBirthDate(formatted);
                }}
                maxLength={10}
                style={{ marginTop: 0 }}
              />
              <p style={{ marginTop: 8, fontSize: 12, color: "var(--text-muted)" }}>
                Введите дату рождения в формате ДД.ММ.ГГГГ
              </p>
            </div>

            <button
              onClick={handleConfirmBirthDate}
              disabled={!tempBirthDate || tempBirthDate.length < 10}
              className="btn-primary"
              style={{ marginTop: 20, width: "100%" }}
            >
              Подтвердить
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
