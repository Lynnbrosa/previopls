import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '@/store/auth';
import { FordBlue } from '@/constants/colors';

export default function Login() {
  const [email, setEmail] = useState(__DEV__ ? 'consultor@ford.com' : '');
  const [senha, setSenha] = useState(__DEV__ ? 'cons123' : '');
  const login = useAuthStore((s) => s.login);
  const loading = useAuthStore((s) => s.loading);
  const router = useRouter();

  const handleSubmit = async () => {
    if (!email || !senha) {
      Alert.alert('Campos obrigatórios', 'Informe email e senha.');
      return;
    }
    try {
      await login(email.trim(), senha);
      router.replace('/(app)/leads');
    } catch (e: any) {
      Alert.alert(
        'Erro ao entrar',
        e?.response?.data?.error?.message ??
          'Não foi possível autenticar. Verifique a URL do backend e suas credenciais.',
      );
    }
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <Text style={styles.logo}>Ford</Text>
            <Text style={styles.subtitle}>Predict & Care · Consultor de Serviços</Text>
          </View>

          <View style={styles.form}>
            <Text style={styles.label}>Email</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              autoCorrect={false}
              placeholder="consultor@ford.com"
              placeholderTextColor="#999"
              editable={!loading}
            />

            <Text style={styles.label}>Senha</Text>
            <TextInput
              style={styles.input}
              value={senha}
              onChangeText={setSenha}
              secureTextEntry
              autoComplete="password"
              autoCorrect={false}
              placeholder="••••••••"
              placeholderTextColor="#999"
              editable={!loading}
            />

            <Pressable
              style={({ pressed }) => [
                styles.button,
                { opacity: pressed || loading ? 0.7 : 1 },
              ]}
              onPress={handleSubmit}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonLabel}>Entrar</Text>
              )}
            </Pressable>

            {__DEV__ && (
              <Text style={styles.hint}>
                Credenciais de desenvolvimento já preenchidas.
              </Text>
            )}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: FordBlue },
  container: { flex: 1 },
  scroll: { flexGrow: 1, justifyContent: 'space-between' },
  header: {
    paddingTop: 60,
    paddingBottom: 40,
    alignItems: 'center',
  },
  logo: {
    fontSize: 56,
    fontWeight: '800',
    fontStyle: 'italic',
    color: '#fff',
    letterSpacing: 2,
  },
  subtitle: {
    fontSize: 14,
    color: '#cfd9e8',
    marginTop: 8,
  },
  form: {
    backgroundColor: '#fff',
    paddingHorizontal: 24,
    paddingTop: 32,
    paddingBottom: 48,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    flex: 1,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
    marginTop: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    color: '#000',
  },
  button: {
    marginTop: 24,
    backgroundColor: FordBlue,
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonLabel: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
  hint: {
    marginTop: 16,
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
  },
});
