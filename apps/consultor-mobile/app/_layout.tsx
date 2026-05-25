import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useAuthStore } from '@/store/auth';
import { useThemeStore } from '@/store/theme';
import { useColorScheme } from '@/hooks/useColorScheme';
import { requestPermissions } from '@/lib/notifications';

export default function RootLayout() {
  const bootstrap = useAuthStore((s) => s.bootstrap);
  const hydrateTheme = useThemeStore((s) => s.hydrate);
  const scheme = useColorScheme();

  useEffect(() => {
    bootstrap();
    hydrateTheme();
    requestPermissions();
  }, [bootstrap, hydrateTheme]);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <StatusBar style={scheme === 'dark' ? 'light' : 'dark'} />
        <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
          <Stack.Screen name="index" />
          <Stack.Screen name="login" options={{ animation: 'fade' }} />
          <Stack.Screen name="(app)" />
        </Stack>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
