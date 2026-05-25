import axios from 'axios';
import { create } from 'zustand';
import { getToken, getRole, setSession, clearSession } from '@/lib/auth';
import { AUTH_EXPIRED, events } from '@/lib/events';
import type { LoginResponse, RolePapel } from '@/types';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://10.0.2.2:5000';

interface AuthState {
  token: string | null;
  role: RolePapel | null;
  loading: boolean;
  bootstrapped: boolean;

  bootstrap: () => Promise<void>;
  login: (email: string, senha: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  role: null,
  loading: false,
  bootstrapped: false,

  bootstrap: async () => {
    const [token, role] = await Promise.all([getToken(), getRole()]);
    set({ token, role, bootstrapped: true });
  },

  login: async (email, senha) => {
    set({ loading: true });
    try {
      const { data } = await axios.post<LoginResponse>(
        `${BASE_URL}/v1/auth/login`,
        { email, senha },
        { timeout: 15000, headers: { 'Content-Type': 'application/json' } },
      );
      await setSession(data.accessToken, data.role);
      set({ token: data.accessToken, role: data.role });
    } finally {
      set({ loading: false });
    }
  },

  logout: async () => {
    await clearSession();
    set({ token: null, role: null });
  },
}));

// Reage a 401 emitido pelo interceptor — limpa estado do Zustand sem ciclo de import.
events.on(AUTH_EXPIRED, () => {
  useAuthStore.setState({ token: null, role: null });
});
