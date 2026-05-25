import axios, { AxiosError } from 'axios';
import { getToken, clearSession } from './auth';
import { AUTH_EXPIRED, events } from './events';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://10.0.2.2:5000';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use(async (config) => {
  const token = await getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      await clearSession();
      events.emit(AUTH_EXPIRED);
    }
    return Promise.reject(error);
  },
);

export default api;
