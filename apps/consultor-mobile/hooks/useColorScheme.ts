import { useColorScheme as useDeviceColorScheme } from 'react-native';
import { useThemeStore } from '@/store/theme';

/**
 * Drop-in replacement do `useColorScheme` do React Native.
 *
 * Prioriza a preferência manual do usuário (light/dark) salva no AsyncStorage.
 * Quando a preferência é 'system', segue o tema do dispositivo.
 *
 * Uso idêntico ao hook nativo: `const scheme = useColorScheme() ?? 'light'`.
 */
export function useColorScheme(): 'light' | 'dark' {
  const preference = useThemeStore((s) => s.preference);
  const device = useDeviceColorScheme();

  if (preference === 'light') return 'light';
  if (preference === 'dark') return 'dark';
  return device === 'dark' ? 'dark' : 'light';
}
