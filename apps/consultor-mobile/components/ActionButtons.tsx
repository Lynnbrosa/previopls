import { useState } from 'react';
import { ActivityIndicator, Alert, Pressable, StyleSheet, Text, View } from 'react-native';
import type { StatusLead } from '@/types';

interface Props {
  onAction: (status: StatusLead) => Promise<void>;
}

const ACTIONS: { status: StatusLead; label: string; color: string }[] = [
  { status: 'agendado', label: 'Agendar', color: '#388e3c' },
  { status: 'recusado', label: 'Recusado', color: '#d32f2f' },
  { status: 'sem-contato', label: 'Sem contato', color: '#616161' },
];

export function ActionButtons({ onAction }: Props) {
  const [loading, setLoading] = useState<StatusLead | null>(null);

  const handlePress = (status: StatusLead, label: string) => {
    Alert.alert(
      'Confirmar ação',
      `Marcar este lead como "${label}"?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Confirmar',
          onPress: async () => {
            setLoading(status);
            try {
              await onAction(status);
            } catch (e: any) {
              Alert.alert(
                'Erro',
                e?.response?.data?.error?.message ?? 'Falha ao atualizar lead.',
              );
            } finally {
              setLoading(null);
            }
          },
        },
      ],
    );
  };

  return (
    <View style={styles.container}>
      {ACTIONS.map((a) => (
        <Pressable
          key={a.status}
          disabled={loading !== null}
          onPress={() => handlePress(a.status, a.label)}
          style={({ pressed }) => [
            styles.button,
            {
              backgroundColor: a.color,
              opacity: pressed || loading !== null ? 0.7 : 1,
            },
          ]}
        >
          {loading === a.status ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.label}>{a.label}</Text>
          )}
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  button: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
});
