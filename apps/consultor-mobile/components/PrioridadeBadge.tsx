import { StyleSheet, Text, View } from 'react-native';
import { PRIORIDADE_COLOR, PRIORIDADE_LABEL } from '@/constants/perfis';
import type { PrioridadeLead } from '@/types';

export function PrioridadeBadge({ prioridade }: { prioridade: PrioridadeLead }) {
  const color = PRIORIDADE_COLOR[prioridade];
  return (
    <View style={[styles.badge, { borderColor: color }]}>
      <Text style={[styles.text, { color }]}>{PRIORIDADE_LABEL[prioridade]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    borderWidth: 1.5,
  },
  text: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
});
