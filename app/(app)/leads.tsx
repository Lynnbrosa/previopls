import { useEffect } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLeadsStore } from '@/store/leads';
import { useAuthStore } from '@/store/auth';
import { LeadCard } from '@/components/LeadCard';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Colors } from '@/constants/colors';
import { useColorScheme } from '@/hooks/useColorScheme';

export default function LeadsScreen() {
  const scheme = useColorScheme();
  const c = Colors[scheme];

  const items = useLeadsStore((s) => s.items);
  const loading = useLeadsStore((s) => s.loading);
  const refreshing = useLeadsStore((s) => s.refreshing);
  const error = useLeadsStore((s) => s.error);
  const fetchLeads = useLeadsStore((s) => s.fetchLeads);
  const refreshLeads = useLeadsStore((s) => s.refreshLeads);
  const hydrate = useLeadsStore((s) => s.hydrate);
  const logout = useAuthStore((s) => s.logout);

  useEffect(() => {
    (async () => {
      await hydrate();
      await fetchLeads();
    })();
  }, [hydrate, fetchLeads]);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: c.background }]} edges={['top']}>
      <View style={[styles.header, { borderBottomColor: c.border }]}>
        <View style={styles.headerLeft}>
          <Text style={[styles.title, { color: c.text }]}>Leads de hoje</Text>
          <Text style={[styles.subtitle, { color: c.textSecondary }]}>
            {items.length} {items.length === 1 ? 'cliente' : 'clientes'} pra abordar
          </Text>
        </View>
        <View style={styles.headerActions}>
          <ThemeToggle />
          <Pressable onPress={logout} hitSlop={12}>
            <Text style={[styles.logout, { color: c.tint }]}>Sair</Text>
          </Pressable>
        </View>
      </View>

      {loading && items.length === 0 ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={c.tint} />
        </View>
      ) : error && items.length === 0 ? (
        <View style={styles.centered}>
          <Text style={[styles.errorText, { color: c.danger }]}>{error}</Text>
          <Pressable onPress={() => fetchLeads()} style={styles.retryButton}>
            <Text style={[styles.retryLabel, { color: c.tint }]}>Tentar novamente</Text>
          </Pressable>
        </View>
      ) : items.length === 0 ? (
        <View style={styles.centered}>
          <Text style={[styles.emptyText, { color: c.textSecondary }]}>
            Nenhum lead aberto no momento.
          </Text>
          <Pressable onPress={() => refreshLeads()} style={styles.retryButton}>
            <Text style={[styles.retryLabel, { color: c.tint }]}>Atualizar</Text>
          </Pressable>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <LeadCard lead={item} />}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={refreshLeads}
              tintColor={c.tint}
              colors={[c.tint]}
            />
          }
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerLeft: { flex: 1 },
  headerActions: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  title: { fontSize: 26, fontWeight: '700' },
  subtitle: { fontSize: 13, marginTop: 2 },
  logout: { fontSize: 14, fontWeight: '600' },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorText: { textAlign: 'center', marginBottom: 16, fontSize: 14 },
  emptyText: { fontSize: 15, marginBottom: 16 },
  retryButton: { paddingVertical: 8, paddingHorizontal: 16 },
  retryLabel: { fontWeight: '600', fontSize: 14 },
  list: { paddingVertical: 8 },
});
