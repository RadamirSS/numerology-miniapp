import { useEffect, useState } from "react";
import { postJSON, getJSON } from "../api";
import type { UserInfo } from "../App";
import { formatBirthDateInput, formatNameInput } from "../utils/format";

// URL поддержки из переменных окружения
const SUPPORT_URL = import.meta.env.VITE_SUPPORT_URL;

declare global {
  interface Window {
    Telegram?: any;
  }
}

interface ProfilePageProps {
  currentUser: UserInfo | null;
  setCurrentUser: (user: UserInfo | null) => void;
}

export default function ProfilePage({ currentUser, setCurrentUser }: ProfilePageProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [step, setStep] = useState<"form" | "verify" | "done">("form");
  
  // Telegram данные
  const [telegramId, setTelegramId] = useState<number | null>(null);
  const [telegramUser, setTelegramUser] = useState<any>(null);
  
  // Форма регистрации
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  
  // Форма логина
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  
  // Верификация
  const [code, setCode] = useState("");
  
  // Состояния
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<UserInfo | null>(currentUser);
  const [isTariffModalOpen, setTariffModalOpen] = useState(false);

  // Синхронизация с currentUser из пропсов
  useEffect(() => {
    if (currentUser) {
      setUser(currentUser);
      setStep("done");
    }
  }, [currentUser]);

  // Инициализация Telegram данных при монтировании
  useEffect(() => {
    // Если пользователь уже залогинен, не загружаем по Telegram ID
    if (currentUser) {
      return;
    }
    
    const tg = window.Telegram?.WebApp;
    if (tg?.initDataUnsafe?.user) {
      const tgUser = tg.initDataUnsafe.user;
      const id = tgUser.id;
      setTelegramId(id);
      setTelegramUser(tgUser);
      
      // Пытаемся загрузить пользователя по Telegram ID
      loadUserByTelegram(id);
    }
  }, [currentUser]);

  async function loadUserByTelegram(id: number) {
    try {
      const data = await getJSON(`/users/by-telegram/${id}`);
      setUser(data);
      setCurrentUser(data);
      setStep("done");
    } catch {
      // Пользователь не найден - это нормально
    }
  }

  // Валидация email
  function validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  // Валидация телефона
  function validatePhone(phone: string): boolean {
    if (!phone) return true; // телефон необязателен
    const digits = phone.replace(/\D/g, "");
    return digits.length >= 7 && digits.length <= 15;
  }

  // Форматирование телефона (только цифры)
  function formatPhoneInput(raw: string): string {
    return raw.replace(/\D/g, "").slice(0, 15);
  }

  // Обработка логина
  async function handleLogin() {
    setError(null);
    setLoading(true);
    
    try {
      if (!loginEmail || !loginPassword) {
        throw new Error("Заполните все поля");
      }

      if (!validateEmail(loginEmail)) {
        throw new Error("Неверный формат email");
      }
      
      const response = await postJSON("/auth/login", {
        email: loginEmail,
        password: loginPassword,
      });
      
      if (response.status === "ok" && response.user) {
        setUser(response.user);
        setCurrentUser(response.user);
        setStep("done");
        setLoginEmail("");
        setLoginPassword("");
      }
    } catch (err: any) {
      // Очистка полей при неверном логине
      setLoginEmail("");
      setLoginPassword("");
      setError("⚠️ Неверный e-mail или пароль");
    } finally {
      setLoading(false);
    }
  }

  // Обработка регистрации
  async function handleRegister() {
    setError(null);
    setLoading(true);
    
    try {
      // Валидация
      if (!name || !name.trim()) {
        throw new Error("Имя обязательно");
      }

      if (!email || !email.trim()) {
        throw new Error("Email обязателен");
      }

      if (!validateEmail(email)) {
        throw new Error("Неверный формат email");
      }

      if (phone && !validatePhone(phone)) {
        throw new Error("Телефон должен содержать от 7 до 15 цифр");
      }
      
      if (!birthDate || !/^\d{2}\.\d{2}\.\d{4}$/.test(birthDate)) {
        throw new Error("Дата рождения должна быть в формате дд.мм.гггг");
      }
      
      if (password.length < 6) {
        throw new Error("Пароль должен быть не короче 6 символов");
      }
      
      if (password !== passwordConfirm) {
        throw new Error("Пароли не совпадают");
      }
      
      // Формирование payload с отформатированным именем
      const formattedName = formatNameInput(name);
      const payload: any = {
        name: formattedName,
        email: email.trim().toLowerCase(),
        phone: phone ? phone.replace(/\D/g, "") : null,
        birth_date: birthDate,
        // Тариф не выбирается при регистрации - будет установлен по умолчанию на бэке
        tariff: null,
        password,
        password_confirm: passwordConfirm,
      };
      
      // Добавление Telegram данных, если есть
      if (telegramId) {
        payload.telegram_id = telegramId;
        if (telegramUser) {
          payload.telegram_username = telegramUser.username || null;
          payload.telegram_first_name = telegramUser.first_name || null;
          payload.telegram_last_name = telegramUser.last_name || null;
          payload.telegram_raw = telegramUser;
        }
      }
      
      const response = await postJSON("/auth/register", payload);
      
      if (response.status === "ok" && response.user) {
        setUser(response.user);
        setStep("verify");
      }
    } catch (err: any) {
      setError(err.message || "Ошибка регистрации");
    } finally {
      setLoading(false);
    }
  }

  // Обработка верификации email
  async function handleVerify() {
    setError(null);
    setLoading(true);
    
    try {
      if (!code || code.length !== 6) {
        throw new Error("Введите 6-значный код");
      }
      
      const response = await postJSON("/auth/verify-email", {
        email: user?.email || email,
        code,
      });
      
      if (response.status === "ok" && response.user) {
        setUser(response.user);
        setCurrentUser(response.user);
        setStep("done");
        setCode("");
      }
    } catch (err: any) {
      setError(err.message || "Неверный код");
    } finally {
      setLoading(false);
    }
  }

  // Выход
  function handleLogout() {
    setUser(null);
    setCurrentUser(null);
    setMode("login");
    setStep("form");
    setError(null);
    // Очистка полей
    setName("");
    setEmail("");
    setPhone("");
    setBirthDate("");
    setPassword("");
    setPasswordConfirm("");
    setTariffModalOpen(false);
    setLoginEmail("");
    setLoginPassword("");
    setCode("");
  }

  // Переключение режима
  function switchMode(newMode: "login" | "register") {
    setMode(newMode);
    setStep("form");
    setError(null);
  }

  // Обработка "Забыли пароль?"
  function handleForgotPassword() {
    alert("Функция восстановления пароля появится позже…");
  }

  // Обработка клика на поддержку
  function handleSupportClick() {
    if (!SUPPORT_URL) return;
    window.open(SUPPORT_URL, "_blank");
  }

  // Открытие модального окна выбора тарифа
  function openTariffModal() {
    setTariffModalOpen(true);
  }

  // Закрытие модального окна
  function closeTariffModal() {
    setTariffModalOpen(false);
  }

  // Обработка выбора тарифа
  function handleSelectTariff(tariffId: string) {
    // TODO: позже здесь будет переход к оплате
    console.log("Selected tariff:", tariffId);
    // Можно сразу закрывать модалку:
    setTariffModalOpen(false);
  }

  // Получение названия тарифа для отображения
  function getTariffDisplayName(tariff: string | null): string {
    if (!tariff) return "Не выбран";
    const names: Record<string, string> = {
      free: "Бесплатный",
      basic: "Базовый",
      pro: "Профессиональный",
    };
    return names[tariff] || tariff;
  }

  // Если пользователь залогинен
  if (step === "done" && user) {
    return (
      <>
        <div className="card">
          <h2>Ваш профиль</h2>
          
          <div style={{ marginTop: 16 }}>
            <p><strong>Имя:</strong> {user.name}</p>
            <p>
              <strong>Email:</strong> {user.email}{" "}
              {user.is_email_verified ? "✅" : "⏳"}
              {user.is_email_verified ? " подтверждён" : " не подтверждён"}
            </p>
            {user.phone && <p><strong>Телефон:</strong> {user.phone}</p>}
            <p><strong>Дата рождения:</strong> {user.birth_date}</p>
            
            {/* Блок с тарифом и кнопкой изменения */}
            <div className="profile-tariff" style={{ marginTop: 16, marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                <span className="profile-tariff__label"><strong>Текущий тариф:</strong></span>
                <span className="profile-tariff__value">{getTariffDisplayName(user.tariff)}</span>
              </div>
              <button 
                className="primary-button" 
                onClick={openTariffModal}
                style={{ marginTop: 8, width: "auto", minWidth: "150px" }}
              >
                Изменить тариф
              </button>
            </div>
            
            {user.telegram_id && (
              <>
                <p><strong>Telegram ID:</strong> {user.telegram_id}</p>
                {user.telegram_username && (
                  <p><strong>Telegram username:</strong> @{user.telegram_username}</p>
                )}
              </>
            )}
          </div>
          
          {/* Кнопка поддержки */}
          {SUPPORT_URL && (
            <button 
              onClick={handleSupportClick}
              className="primary-button"
              style={{ marginTop: 16 }}
            >
              Поддержка
            </button>
          )}
          
          <button 
            onClick={handleLogout} 
            className="btn-primary"
            style={{ marginTop: 16 }}
          >
            Выйти
          </button>
        </div>

        {/* Модальное окно выбора тарифа */}
        {isTariffModalOpen && (
          <div className="modal-overlay" onClick={closeTariffModal}>
            <div className="modal-card" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Выберите тариф</h2>
                <button className="modal-close" onClick={closeTariffModal}>×</button>
              </div>
              
              <div className="tariff-list">
                {/* Тариф Бесплатный */}
                <div className="tariff-card">
                  <h3>Бесплатный</h3>
                  <p>Базовый доступ к калькуляторам и основным функциям приложения.</p>
                  <button
                    className="primary-button"
                    onClick={() => handleSelectTariff("free")}
                  >
                    Выбрать «Бесплатный»
                  </button>
                </div>

                {/* Тариф Базовый */}
                <div className="tariff-card">
                  <h3>Базовый</h3>
                  <p>Расширенный доступ к расчётам, большее количество запросов к калькуляторам.</p>
                  <button
                    className="primary-button"
                    onClick={() => handleSelectTariff("basic")}
                  >
                    Выбрать «Базовый»
                  </button>
                </div>

                {/* Тариф Профессиональный */}
                <div className="tariff-card">
                  <h3>Профессиональный</h3>
                  <p>Полный доступ ко всем функциям, включая AI-интерпретации и неограниченное количество расчётов.</p>
                  <button
                    className="primary-button"
                    onClick={() => handleSelectTariff("pro")}
                  >
                    Выбрать «Профессиональный»
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Форма верификации email
  if (step === "verify") {
    return (
      <div className="card">
        <h2>Подтверждение email</h2>
        
        <p style={{ marginTop: 16, fontSize: 14 }}>
          Мы отправили код на email <strong>{user?.email || email}</strong>.
          В dev-режиме код также выводится в лог сервера.
        </p>
        
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span> {error}
          </div>
        )}
        
        <input
          type="text"
          placeholder="Код подтверждения"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
          style={{ marginTop: 16 }}
          maxLength={6}
        />
        
        <button 
          onClick={handleVerify} 
          disabled={loading}
          className="btn-primary"
          style={{ marginTop: 12 }}
        >
          {loading ? "Проверка..." : "Подтвердить"}
        </button>
      </div>
    );
  }

  // Формы логина/регистрации
  return (
    <div className="card">
      <div className="auth-toggle">
        <button
          onClick={() => switchMode("login")}
          className={mode === "login" ? "active" : ""}
        >
          Войти
        </button>
        <button
          onClick={() => switchMode("register")}
          className={mode === "register" ? "active" : ""}
        >
          Зарегистрироваться
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span> {error}
        </div>
      )}

      {mode === "login" ? (
        <>
          <h2>Вход</h2>
          <input
            type="email"
            placeholder="Email"
            value={loginEmail}
            onChange={(e) => setLoginEmail(e.target.value)}
            style={{ marginTop: 16 }}
          />
          <input
            type="password"
            placeholder="Пароль"
            value={loginPassword}
            onChange={(e) => setLoginPassword(e.target.value)}
            style={{ marginTop: 12 }}
          />
          <button 
            type="button"
            className="text-button"
            onClick={handleForgotPassword}
            style={{ marginTop: 8 }}
          >
            Забыли пароль?
          </button>
          <button 
            onClick={handleLogin} 
            disabled={loading}
            className="btn-primary"
            style={{ marginTop: 16 }}
          >
            {loading ? "Вход..." : "Войти"}
          </button>
        </>
      ) : (
        <>
          <h2>Регистрация</h2>
          <input
            type="text"
            placeholder="Имя *"
            value={name}
            onChange={(e) => {
              const formatted = formatNameInput(e.target.value);
              setName(formatted);
            }}
            style={{ marginTop: 16 }}
          />
          <input
            type="email"
            placeholder="E-mail *"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ marginTop: 12 }}
          />
          <input
            type="tel"
            placeholder="Телефон"
            value={phone}
            onChange={(e) => {
              const formatted = formatPhoneInput(e.target.value);
              setPhone(formatted);
            }}
            style={{ marginTop: 12 }}
          />
          <input
            type="text"
            placeholder="Дата рождения (дд.мм.гггг) *"
            value={birthDate}
            onChange={(e) => {
              const formatted = formatBirthDateInput(e.target.value);
              setBirthDate(formatted);
            }}
            style={{ marginTop: 12 }}
            maxLength={10}
          />
          <input
            type="password"
            placeholder="Пароль (мин. 6 символов) *"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ marginTop: 12 }}
          />
          <input
            type="password"
            placeholder="Повторите пароль *"
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            style={{ marginTop: 12 }}
          />
          <button 
            onClick={handleRegister} 
            disabled={loading}
            className="btn-primary"
            style={{ marginTop: 16 }}
          >
            {loading ? "Регистрация..." : "Зарегистрироваться"}
          </button>
        </>
      )}
    </div>
  );
}
