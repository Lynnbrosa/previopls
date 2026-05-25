import { Redirect, Stack } from 'expo-router';
import { useAuthStore } from '@/store/auth';

export default function AppLayout() {
  const token = useAuthStore((s) => s.token);
  const bootstrapped = useAuthStore((s) => s.bootstrapped);

  if (!bootstrapped) return null;
  if (!token) return <Redirect href="/login" />;

  return (
    <Stack screenOptions={{ headerShown: false, animation: 'slide_from_right' }}>
      <Stack.Screen name="leads" />
      <Stack.Screen name="lead/[id]" />
    </Stack>
  );
}
