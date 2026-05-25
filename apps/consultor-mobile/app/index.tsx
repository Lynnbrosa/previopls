import { Redirect } from 'expo-router';
import { ActivityIndicator, View } from 'react-native';
import { useAuthStore } from '@/store/auth';
import { FordBlue } from '@/constants/colors';

export default function Index() {
  const { token, bootstrapped } = useAuthStore();

  if (!bootstrapped) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={FordBlue} />
      </View>
    );
  }

  return <Redirect href={token ? '/(app)/leads' : '/login'} />;
}
