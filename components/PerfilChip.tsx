import { StyleSheet, Text, View } from 'react-native';
import { PERFIL_COLOR, PERFIL_LABEL } from '@/constants/perfis';
import type { PerfilCliente } from '@/types';

export function PerfilChip({ perfil }: { perfil: PerfilCliente }) {
  return (
    <View style={[styles.chip, { backgroundColor: PERFIL_COLOR[perfil] }]}>
      <Text style={styles.text}>{PERFIL_LABEL[perfil]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    alignSelf: 'flex-start',
  },
  text: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
});
