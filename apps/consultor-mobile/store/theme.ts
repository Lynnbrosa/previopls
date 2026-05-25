import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = 'theme:preference:v1';

export type ThemePreference = 'light' | 'dark' | 'system';

interface ThemeState {
  preference: ThemePreference;
  hydrated: boolean;

  hydrate: () => Promise<void>;
  setPreference: (p: ThemePreference) => Promise<void>;
  cycle: () => Promise<void>;
}

const isValid = (v: unknown): v is ThemePreference =>
  v === 'light' || v === 'dark' || v === 'system';

export const useThemeStore = create<ThemeState>((set, get) => ({
  preference: 'system',
  hydrated: false,

  hydrate: async () => {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (isValid(raw)) {
      set({ preference: raw, hydrated: true });
    } else {
      set({ hydrated: true });
    }
  },

  setPreference: async (p) => {
    await AsyncStorage.setItem(STORAGE_KEY, p);
    set({ preference: p });
  },

  cycle: async () => {
    const order: ThemePreference[] = ['system', 'light', 'dark'];
    const idx = order.indexOf(get().preference);
    const next = order[(idx + 1) % order.length];
    await AsyncStorage.setItem(STORAGE_KEY, next);
    set({ preference: next });
  },
}));
