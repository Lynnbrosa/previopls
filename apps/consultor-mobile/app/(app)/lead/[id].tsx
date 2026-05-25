import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import api from '@/lib/api';
import { useLeadsStore } from '@/store/leads';
import { notifyStatusUpdate } from '@/lib/notifications';
import { PerfilChip } from '@/components/PerfilChip';
import { PrioridadeBadge } from '@/components/PrioridadeBadge';
import { ActionButtons } from '@/components/ActionButtons';
import { Colors, type ColorPalette } from '@/constants/colors';
import { STATUS_LABEL, perfilFromScore } from '@/constants/perfis';
import { useColorScheme } from '@/hooks/useColorScheme';
import type { LeadDetail, StatusLead } from '@/types';

const ACTION_LABELS: Record<StatusLead, string> = {
  aberto: 'Aberto',
  agendado: 'Agendado',
  recusado: 'Recusado',
  'sem-contato': 'Sem contato',
};

export default function LeadDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const scheme = useColorScheme();
  const c = Colors[scheme];
  const patchStatus = useLeadsStore((s) => s.patchStatus);

  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const { data } = await api.get<LeadDetail>(`/v1/leads/${id}`);
        setLead(data);
      } catch (e: any) {
        setError(e?.response?.data?.error?.message ?? 'Erro ao carregar lead.');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleAction = async (status: StatusLead) => {
    if (!id) return;
    const updated = await patchStatus(id, status);
    setLead(updated);
    await notifyStatusUpdate(ACTION_LABELS[status]);
    setTimeout(() => router.back(), 700);
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, styles.centered, { backgroundColor: c.background }]}>
        <ActivityIndicator size="large" color={c.tint} />
      </SafeAreaView>
    );
  }

  if (error || !lead) {
    return (
      <SafeAreaView style={[styles.container, styles.centered, { backgroundColor: c.background }]} edges={['top']}>
        <Text style={[styles.errorText, { color: c.danger }]}>
          {error ?? 'Lead não encontrado'}
        </Text>
        <Pressable onPress={() => router.back()} hitSlop={12}>
          <Text style={[styles.backLink, { color: c.tint }]}>Voltar</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  const cliente = lead.cliente;
  const veiculo = lead.veiculo;
  const perfil = cliente.perfil ?? perfilFromScore(lead.scoreRisco);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: c.background }]} edges={['top']}>
      <View style={[styles.header, { borderBottomColor: c.border }]}>
        <Pressable onPress={() => router.back()} hitSlop={12}>
          <Text style={[styles.back, { color: c.tint }]}>← Voltar</Text>
        </Pressable>
        <PrioridadeBadge prioridade={lead.prioridade} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.hero}>
          <PerfilChip perfil={perfil} />
          <Text style={[styles.clienteNome, { color: c.text }]}>{cliente.nome}</Text>
          <Text style={[styles.metaLine, { color: c.textSecondary }]}>
            Score de risco:{' '}
            <Text style={{ fontWeight: '700', color: c.text }}>
              {(lead.scoreRisco * 100).toFixed(0)}%
            </Text>
          </Text>
          <Text style={[styles.metaLine, { color: c.textSecondary }]}>
            Status:{' '}
            <Text style={{ fontWeight: '600', color: c.text }}>
              {STATUS_LABEL[lead.status]}
            </Text>
          </Text>
        </View>

        <Section title="Cliente" palette={c}>
          <Row label="Telefone" value={cliente.telefone ?? '—'} palette={c} />
          <Row label="Email" value={cliente.email ?? '—'} palette={c} />
          <Row label="CPF" value={maskCpf(cliente.cpf)} palette={c} />
          <Row label="Região" value={cliente.regiao} palette={c} />
        </Section>

        <Section title="Veículo" palette={c}>
          <Row label="Modelo" value={`${veiculo.modelo} ${veiculo.versao}`} palette={c} />
          <Row label="Ano" value={String(veiculo.ano)} palette={c} />
          <Row label="VIN" value={veiculo.vin} palette={c} />
          <Row label="Compra" value={formatDate(veiculo.dataCompra)} palette={c} />
          <Row label="Valor" value={`R$ ${formatMoney(veiculo.valorCompra)}`} palette={c} />
          <Row label="Concessionária" value={veiculo.concessionariaId} palette={c} />
        </Section>

        {lead.scriptOferta ? (
          <Section title="Script de abordagem" palette={c}>
            <Text style={[styles.script, { color: c.text }]}>{lead.scriptOferta}</Text>
          </Section>
        ) : null}

        {lead.observacao ? (
          <Section title="Observação" palette={c}>
            <Text style={[styles.script, { color: c.text }]}>{lead.observacao}</Text>
          </Section>
        ) : null}
      </ScrollView>

      {lead.status === 'aberto' && <ActionButtons onAction={handleAction} />}
    </SafeAreaView>
  );
}

function Section({
  title,
  palette: c,
  children,
}: {
  title: string;
  palette: ColorPalette;
  children: React.ReactNode;
}) {
  return (
    <View style={[sectionStyles.box, { backgroundColor: c.card, borderColor: c.border }]}>
      <Text style={[sectionStyles.title, { color: c.textSecondary }]}>
        {title.toUpperCase()}
      </Text>
      {children}
    </View>
  );
}

function Row({
  label,
  value,
  palette: c,
}: {
  label: string;
  value: string;
  palette: ColorPalette;
}) {
  return (
    <View style={sectionStyles.row}>
      <Text style={[sectionStyles.rowLabel, { color: c.textSecondary }]}>{label}</Text>
      <Text style={[sectionStyles.rowValue, { color: c.text }]} numberOfLines={2}>
        {value}
      </Text>
    </View>
  );
}

function maskCpf(cpf: string): string {
  if (cpf.length !== 11) return cpf;
  return `${cpf.slice(0, 3)}.***.***-${cpf.slice(-2)}`;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('pt-BR');
}

function formatMoney(value: string): string {
  const n = parseFloat(value);
  if (isNaN(n)) return value;
  return n.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  centered: { justifyContent: 'center', alignItems: 'center' },
  errorText: { textAlign: 'center', marginBottom: 16, fontSize: 14 },
  backLink: { fontWeight: '600', fontSize: 14 },
  header: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  back: { fontSize: 16, fontWeight: '600' },
  scroll: { paddingBottom: 32 },
  hero: { padding: 20, gap: 6 },
  clienteNome: { fontSize: 28, fontWeight: '700', marginTop: 6, marginBottom: 4 },
  metaLine: { fontSize: 14, marginTop: 2 },
  script: { fontSize: 14, lineHeight: 20 },
});

const sectionStyles = StyleSheet.create({
  box: {
    marginHorizontal: 16,
    marginVertical: 8,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  title: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: 6,
    gap: 12,
  },
  rowLabel: { fontSize: 13, fontWeight: '500' },
  rowValue: { fontSize: 14, fontWeight: '500', flex: 1, textAlign: 'right' },
});
