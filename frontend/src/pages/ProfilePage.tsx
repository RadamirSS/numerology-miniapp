import { useEffect, useState, useRef } from "react";
import { useUserStore } from "../store/userStore";
import { formatBirthDateInput, formatNameInput } from "../utils/format";
import { processAvatarFile } from "../utils/avatar";
import { normalizeImageUrl } from "../api";

// URL поддержки из переменных окружения
const SUPPORT_URL = import.meta.env.VITE_SUPPORT_URL;

declare global {
  interface Window {
    Telegram?: any;
  }
}

export default function ProfilePage() {
  const { profile, loading, error, loadProfileFromTelegram, updateProfile, setProfile } = useUserStore();
  const [isEditing, setIsEditing] = useState(false);
  const [isTariffModalOpen, setTariffModalOpen] = useState(false);
  const [avatarMenuOpen, setAvatarMenuOpen] = useState(false);
  
  // Поля для редактирования
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [avatarObjectUrl, setAvatarObjectUrl] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const avatarMenuRef = useRef<HTMLDivElement>(null);

  // Загрузка профиля при монтировании
  useEffect(() => {
    if (!profile) {
      loadProfileFromTelegram();
    }
  }, []);

  // Обработка события для открытия модалки тарифов
  useEffect(() => {
    function handleOpenTariffModal() {
      setTariffModalOpen(true);
    }

    window.addEventListener('profileTariffModalOpen', handleOpenTariffModal);

    return () => {
      window.removeEventListener('profileTariffModalOpen', handleOpenTariffModal);
    };
  }, []);

  // Синхронизация полей с профилем
  useEffect(() => {
    if (profile) {
      setName(profile.name || "");
      setEmail(profile.email || "");
      setPhone(profile.phone || "");
      setBirthDate(profile.birth_date || "");
      setAvatarUrl(profile.avatar_url || null);
    }
  }, [profile]);

  // Очистка object URL при размонтировании
  useEffect(() => {
    return () => {
      if (avatarObjectUrl) {
        URL.revokeObjectURL(avatarObjectUrl);
      }
    };
  }, [avatarObjectUrl]);

  // Закрытие меню аватара при клике вне его
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (avatarMenuRef.current && !avatarMenuRef.current.contains(event.target as Node)) {
        setAvatarMenuOpen(false);
      }
    }
    
    if (avatarMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [avatarMenuOpen]);

  // Валидация email
  function validateEmail(email: string): boolean {
    if (!email) return true; // email необязателен
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  // Валидация даты рождения
  function validateBirthDate(date: string): boolean {
    if (!date) return true; // дата необязательна
    return /^\d{2}\.\d{2}\.\d{4}$/.test(date);
  }

  // Обработка загрузки аватара
  async function handleAvatarSelect(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const base64 = await processAvatarFile(file);
      // Сохраняем base64 как avatar_url (в продакшене можно загрузить на сервер и получить URL)
      setAvatarUrl(base64);
      
      // Создаём object URL для предпросмотра
      if (avatarObjectUrl) {
        URL.revokeObjectURL(avatarObjectUrl);
      }
      const objectUrl = URL.createObjectURL(file);
      setAvatarObjectUrl(objectUrl);
      
      // Если режим редактирования включен, сохраняем сразу
      if (isEditing) {
        await updateProfile({ avatar_url: base64 });
      }
    } catch (err: any) {
      alert(err.message || "Ошибка загрузки аватара");
    }
    
    // Очищаем input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setAvatarMenuOpen(false);
  }

  // Открытие диалога выбора файла
  function handleChangeAvatarClick() {
    fileInputRef.current?.click();
  }

  // Включение режима редактирования
  function handleEditClick() {
    setIsEditing(true);
    setAvatarMenuOpen(false);
  }

  // Сохранение изменений
  async function handleSave() {
    // Валидация
    if (name.trim() === "") {
      alert("Имя не может быть пустым");
      return;
    }
    
    if (email && !validateEmail(email)) {
      alert("Неверный формат email");
      return;
    }
    
    if (birthDate && !validateBirthDate(birthDate)) {
      alert("Дата рождения должна быть в формате ДД.ММ.ГГГГ");
      return;
    }

    try {
      await updateProfile({
        name: formatNameInput(name.trim()),
        email: email.trim() || undefined,
        phone: phone || null,
        birth_date: birthDate || "",
        avatar_url: avatarUrl || null,
      });
      setIsEditing(false);
      setAvatarMenuOpen(false);
    } catch (err: any) {
      alert(err.message || "Ошибка сохранения профиля");
    }
  }

  // Отмена редактирования
  function handleCancel() {
    if (profile) {
      setName(profile.name || "");
      setEmail(profile.email || "");
      setPhone(profile.phone || "");
      setBirthDate(profile.birth_date || "");
      setAvatarUrl(profile.avatar_url || null);
    }
    setIsEditing(false);
    setAvatarMenuOpen(false);
    
    // Очищаем временный object URL
    if (avatarObjectUrl) {
      URL.revokeObjectURL(avatarObjectUrl);
      setAvatarObjectUrl(null);
    }
  }

  // Получение URL аватара для отображения
  function getAvatarDisplayUrl(): string | null {
    if (avatarObjectUrl) return avatarObjectUrl; // Временный URL для предпросмотра
    if (avatarUrl) {
      // Если это base64, возвращаем как есть, иначе нормализуем
      if (avatarUrl.startsWith("data:")) return avatarUrl;
      return normalizeImageUrl(avatarUrl);
    }
    // Пытаемся получить из Telegram
    const tg = window.Telegram?.WebApp;
    const tgUser = tg?.initDataUnsafe?.user;
    if (tgUser?.photo_url) return tgUser.photo_url;
    return null;
  }

  // Получение имени пользователя для отображения
  function getDisplayName(): string {
    if (profile?.name) return profile.name;
    const tg = window.Telegram?.WebApp;
    const tgUser = tg?.initDataUnsafe?.user;
    if (tgUser?.first_name) {
      return tgUser.last_name ? `${tgUser.first_name} ${tgUser.last_name}` : tgUser.first_name;
    }
    return "Пользователь";
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

  // Обработка клика на поддержку
  function handleSupportClick() {
    if (!SUPPORT_URL) return;
    window.open(SUPPORT_URL, "_blank");
  }

  // Обработка выбора тарифа
  async function handleSelectTariff(tariffId: string) {
    try {
      // Если профиля нет, создаём временный для сохранения тарифа
      if (!profile) {
        const tg = window.Telegram?.WebApp;
        const tgUser = tg?.initDataUnsafe?.user;
        if (tgUser?.id) {
          // Создаём профиль с тарифом через create-or-update
          await updateProfile({
            name: tgUser.first_name || 'Пользователь',
            email: '',
            phone: null,
            birth_date: '',
            tariff: tariffId,
            telegram_id: tgUser.id,
            telegram_username: tgUser.username || null,
            telegram_first_name: tgUser.first_name || null,
            telegram_last_name: tgUser.last_name || null,
            is_email_verified: false,
          });
        } else {
          // Если нет Telegram-пользователя, просто сохраняем локально
          setProfile({
            id: 0,
            name: 'Пользователь',
            email: '',
            phone: null,
            birth_date: '',
            tariff: tariffId,
            telegram_id: null,
            telegram_username: null,
            telegram_first_name: null,
            telegram_last_name: null,
            is_email_verified: false,
          });
        }
      } else {
        // Обновляем существующий профиль
        await updateProfile({ tariff: tariffId });
      }
      setTariffModalOpen(false);
    } catch (err: any) {
      alert(err.message || "Ошибка сохранения тарифа");
    }
  }

  const avatarDisplayUrl = getAvatarDisplayUrl();
  const displayName = getDisplayName();

  if (loading && !profile) {
    return (
      <div className="card">
        <p>Загрузка профиля...</p>
      </div>
    );
  }

  return (
    <>
      <div className="card">
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 24 }}>
          {/* Аватар */}
          <div style={{ position: "relative" }}>
            <div
              onClick={() => setAvatarMenuOpen(!avatarMenuOpen)}
              style={{
                width: 64,
                height: 64,
                borderRadius: "50%",
                backgroundColor: "var(--border-soft)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                overflow: "hidden",
                border: "2px solid var(--gold)",
              }}
            >
              {avatarDisplayUrl ? (
                <img
                  src={avatarDisplayUrl}
                  alt="Аватар"
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                />
              ) : (
                <span style={{ fontSize: 24 }}>👤</span>
              )}
            </div>
            
            {/* Меню смены аватара */}
            {avatarMenuOpen && (
              <div
                ref={avatarMenuRef}
                style={{
                  position: "absolute",
                  top: "100%",
                  left: 0,
                  marginTop: 8,
                  backgroundColor: "var(--bg-card)",
                  border: "1px solid var(--gold)",
                  borderRadius: 8,
                  padding: 8,
                  zIndex: 1000,
                  minWidth: 150,
                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.5)",
                }}
              >
                <button
                  onClick={handleChangeAvatarClick}
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
          
          {/* Имя пользователя */}
          <div style={{ flex: 1 }}>
            <h2 style={{ margin: 0 }}>{displayName}</h2>
            {profile?.telegram_username && (
              <p style={{ margin: "4px 0 0 0", fontSize: 13, color: "var(--text-muted)" }}>
                @{profile.telegram_username}
              </p>
            )}
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          style={{ display: "none" }}
          onChange={handleAvatarSelect}
        />

        {/* Поля профиля */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Имя */}
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <label style={{ fontSize: 14, fontWeight: 500 }}>Имя пользователя</label>
              {isEditing && (
                <button
                  onClick={() => {
                    // Можно добавить логику для редактирования конкретного поля
                  }}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: "var(--accent-light)",
                    cursor: "pointer",
                    fontSize: 12,
                    textDecoration: "underline",
                  }}
                >
                  Изменить
                </button>
              )}
            </div>
            {isEditing ? (
              <input
                type="text"
                value={name}
                onChange={(e) => {
                  const formatted = formatNameInput(e.target.value);
                  setName(formatted);
                }}
                placeholder="Введите имя"
              />
            ) : (
              <div style={{ padding: "10px 12px", borderRadius: 999, border: "1px solid var(--border-soft)", backgroundColor: "rgba(1, 12, 10, 0.9)" }}>
                {profile?.name || "Не указано"}
              </div>
            )}
          </div>

          {/* Телефон */}
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <label style={{ fontSize: 14, fontWeight: 500 }}>Номер телефона</label>
              {isEditing && (
                <button
                  style={{
                    background: "transparent",
                    border: "none",
                    color: profile?.phone ? "var(--accent-light)" : "var(--gold)",
                    cursor: "pointer",
                    fontSize: 12,
                    textDecoration: "underline",
                  }}
                >
                  {profile?.phone ? "Изменить" : "Добавить"}
                </button>
              )}
            </div>
            {isEditing ? (
              <input
                type="tel"
                value={phone}
                onChange={(e) => {
                  const formatted = e.target.value.replace(/\D/g, "").slice(0, 15);
                  setPhone(formatted);
                }}
                placeholder="Введите номер телефона"
              />
            ) : (
              <div style={{ padding: "10px 12px", borderRadius: 999, border: "1px solid var(--border-soft)", backgroundColor: "rgba(1, 12, 10, 0.9)" }}>
                {profile?.phone || "Не указано"}
              </div>
            )}
          </div>

          {/* Дата рождения */}
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <label style={{ fontSize: 14, fontWeight: 500 }}>Дата рождения</label>
              {isEditing && (
                <button
                  style={{
                    background: "transparent",
                    border: "none",
                    color: profile?.birth_date ? "var(--accent-light)" : "var(--gold)",
                    cursor: "pointer",
                    fontSize: 12,
                    textDecoration: "underline",
                  }}
                >
                  {profile?.birth_date ? "Изменить" : "Добавить"}
                </button>
              )}
            </div>
            {isEditing ? (
              <input
                type="text"
                value={birthDate}
                onChange={(e) => {
                  const formatted = formatBirthDateInput(e.target.value);
                  setBirthDate(formatted);
                }}
                placeholder="ДД.ММ.ГГГГ"
                maxLength={10}
              />
            ) : (
              <div style={{ padding: "10px 12px", borderRadius: 999, border: "1px solid var(--border-soft)", backgroundColor: "rgba(1, 12, 10, 0.9)" }}>
                {profile?.birth_date || "Не указано"}
              </div>
            )}
          </div>

          {/* Email */}
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <label style={{ fontSize: 14, fontWeight: 500 }}>
                Email {profile?.is_email_verified && "✅"}
              </label>
              {isEditing && (
                <button
                  style={{
                    background: "transparent",
                    border: "none",
                    color: profile?.email ? "var(--accent-light)" : "var(--gold)",
                    cursor: "pointer",
                    fontSize: 12,
                    textDecoration: "underline",
                  }}
                >
                  {profile?.email ? "Изменить" : "Добавить"}
                </button>
              )}
            </div>
            {isEditing ? (
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Введите email"
              />
            ) : (
              <div style={{ padding: "10px 12px", borderRadius: 999, border: "1px solid var(--border-soft)", backgroundColor: "rgba(1, 12, 10, 0.9)" }}>
                {profile?.email || "Не указано"}
              </div>
            )}
          </div>

          {/* Тариф */}
          <div className="profile-tariff" style={{ marginTop: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <span className="profile-tariff__label"><strong>Текущий тариф:</strong></span>
              <span className="profile-tariff__value">{getTariffDisplayName(profile?.tariff || null)}</span>
            </div>
            <button 
              className="primary-button" 
              onClick={() => setTariffModalOpen(true)}
              style={{ marginTop: 8, width: "auto", minWidth: "150px" }}
            >
              {profile?.tariff ? "Изменить тариф" : "Выбрать тариф"}
            </button>
          </div>
        </div>

        {/* Кнопки управления */}
        <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
          {isEditing ? (
            <>
              <button 
                onClick={handleSave} 
                disabled={loading}
                className="btn-primary"
                style={{ flex: 1 }}
              >
                {loading ? "Сохранение..." : "Сохранить"}
              </button>
              <button 
                onClick={handleCancel} 
                className="primary-button"
                style={{ flex: 1 }}
              >
                Отмена
              </button>
            </>
          ) : (
            <button 
              onClick={handleEditClick} 
              className="btn-primary"
              style={{ width: "100%" }}
            >
              Редактировать профиль
            </button>
          )}
        </div>

        {/* Кнопка поддержки */}
        {SUPPORT_URL && (
          <button 
            onClick={handleSupportClick}
            className="primary-button"
            style={{ marginTop: 12 }}
          >
            Поддержка
          </button>
        )}

        {error && (
          <div className="error-message" style={{ marginTop: 16 }}>
            <span className="error-icon">⚠️</span> {error}
          </div>
        )}
      </div>

      {/* Модальное окно выбора тарифа */}
      {isTariffModalOpen && (
        <div className="modal-overlay" onClick={() => setTariffModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Выберите тариф</h2>
              <button className="modal-close" onClick={() => setTariffModalOpen(false)}>×</button>
            </div>
            
            <div className="tariff-list">
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
