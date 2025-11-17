import { create } from 'zustand';
import { getJSON, postJSON } from '../api';

export interface UserProfile {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  birth_date: string;
  tariff: string | null;
  telegram_id: number | null;
  telegram_username: string | null;
  telegram_first_name: string | null;
  telegram_last_name: string | null;
  is_email_verified: boolean;
  avatar_url?: string | null;
}

interface UserStore {
  profile: UserProfile | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  loadProfileFromTelegram: () => Promise<void>;
  updateProfile: (updates: Partial<UserProfile>) => Promise<void>;
  setProfile: (profile: UserProfile | null) => void;
  clearProfile: () => void;
}

// Получение Telegram пользователя
function getTelegramUser() {
  const tg = (window as any).Telegram?.WebApp;
  return tg?.initDataUnsafe?.user || null;
}

export const useUserStore = create<UserStore>((set, get) => ({
  profile: null,
  loading: false,
  error: null,

  loadProfileFromTelegram: async () => {
    const tgUser = getTelegramUser();
    if (!tgUser?.id) {
      // Если нет Telegram-пользователя, работаем как гость без ошибки
      if (typeof window !== 'undefined' && (window as any).Telegram?.WebApp) {
        console.warn('Telegram user not found. initDataUnsafe:', (window as any).Telegram?.WebApp?.initDataUnsafe);
      }
      set({ profile: null, error: null });
      return;
    }

    set({ loading: true, error: null });
    try {
      const profile = await getJSON(`/users/by-telegram/${tgUser.id}`);
      
      // Обновляем профиль данными из Telegram, если они изменились
      const updatedProfile: UserProfile = {
        ...profile,
        telegram_first_name: tgUser.first_name || profile.telegram_first_name,
        telegram_last_name: tgUser.last_name || profile.telegram_last_name,
        telegram_username: tgUser.username || profile.telegram_username,
      };
      
      set({ profile: updatedProfile, loading: false });
    } catch (err: any) {
      // Если пользователь не найден, создаём профиль из Telegram данных
      if (err.message?.includes('404') || err.message?.includes('not found')) {
        const tgUser = getTelegramUser();
        const newProfile: UserProfile = {
          id: 0, // Временный ID, будет установлен после создания на бэке
          name: tgUser.first_name || 'Пользователь',
          email: '',
          phone: null,
          birth_date: '',
          tariff: null,
          telegram_id: tgUser.id,
          telegram_username: tgUser.username || null,
          telegram_first_name: tgUser.first_name || null,
          telegram_last_name: tgUser.last_name || null,
          is_email_verified: false,
          avatar_url: tgUser.photo_url || null,
        };
        set({ profile: newProfile, loading: false, error: null });
      } else {
        set({ error: err.message || 'Ошибка загрузки профиля', loading: false });
      }
    }
  },

  updateProfile: async (updates: Partial<UserProfile>) => {
    const { profile } = get();
    if (!profile) return;

    set({ loading: true, error: null });
    try {
      const tgUser = getTelegramUser();
      if (tgUser?.id && profile.telegram_id === tgUser.id) {
        // Используем create-or-update endpoint для пользователей из Telegram
        const updated = await postJSON(`/users/by-telegram/${tgUser.id}/create-or-update`, updates);
        set({ profile: updated, loading: false });
      } else if (profile.id > 0) {
        // Используем обычный update endpoint
        const updated = await postJSON(`/users/${profile.id}`, updates, 'PUT');
        set({ profile: updated, loading: false });
      } else {
        // Локальное обновление для временных профилей
        const updatedProfile = { ...profile, ...updates };
        set({ profile: updatedProfile, loading: false });
      }
    } catch (err: any) {
      set({ error: err.message || 'Ошибка обновления профиля', loading: false });
    }
  },

  setProfile: (profile: UserProfile | null) => {
    set({ profile });
  },

  clearProfile: () => {
    set({ profile: null, error: null });
  },
}));

