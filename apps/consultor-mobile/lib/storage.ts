import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';

const SECURE_KEYS = ['jwt', 'role'] as const;
export type SecureKey = (typeof SECURE_KEYS)[number];

export const Secure = {
  async get(key: SecureKey): Promise<string | null> {
    return SecureStore.getItemAsync(key);
  },
  async set(key: SecureKey, value: string): Promise<void> {
    await SecureStore.setItemAsync(key, value);
  },
  async remove(key: SecureKey): Promise<void> {
    await SecureStore.deleteItemAsync(key);
  },
};

export const Cache = {
  async get<T>(key: string): Promise<T | null> {
    const raw = await AsyncStorage.getItem(key);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as T;
    } catch {
      return null;
    }
  },
  async set<T>(key: string, value: T): Promise<void> {
    await AsyncStorage.setItem(key, JSON.stringify(value));
  },
  async remove(key: string): Promise<void> {
    await AsyncStorage.removeItem(key);
  },
};
