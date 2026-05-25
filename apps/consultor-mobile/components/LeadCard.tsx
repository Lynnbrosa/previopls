import { Pressable, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { PerfilChip } from './PerfilChip';
import { PrioridadeBadge } from './PrioridadeBadge';
import { Colors } from '@/constants/colors';
import { perfilFromScore } from '@/constants/perfis';
import { useColorScheme } from '@/hooks/useColorScheme';
import type { LeadListItem } from '@/types';

export function LeadCard({ lead }: { lead: LeadListItem }) {
  const scheme = useColorScheme();
  const c = Colors[scheme];
  const router = useRouter();
  const perfil = perfilFromScore(lead.scoreRisco);

  return (
    <Pressable
      onPress={() => router.push(`/lead/${lead.id}`)}
      style={({ pressed }) => [
        styles.card,
        {
          backgroundColor: c.card,
          borderColor: c.border,
          opacity: pressed ? 0.7 : 1,
        },
      ]}
    >
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={[styles.nome, { color: c.text }]} numberOfLines={1}>
            {lead.nomeCliente}
          </Text>
          <Text style={[styles.modelo, { color: c.textSecondary }]} numberOfLines={1}>
            {lead.modeloVeiculo}
          </Text>
        </View>
        <PrioridadeBadge prioridade={lead.prioridade} />
      </View>

      <View style={styles.footer}>
        <PerfilChip perfil={perfil} />
        <Text style={[styles.score, { color: c.textSecondary }]}>
          Score {(lead.scoreRisco * 100).toFixed(0)}%
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 14,
    marginHorizontal: 16,
    marginVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerText: { flex: 1 },
  nome: { fontSize: 16, fontWeight: '600' },
  modelo: { fontSize: 13, marginTop: 2 },
  footer: {
    marginTop: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  score: { fontSize: 12, fontWeight: '500' },
});
