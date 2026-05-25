import Link from 'next/link';
import { PerfilPie } from '@/components/perfil-pie';
import { listLeads } from '@/lib/api';
import { formatPercent } from '@/lib/utils';
import type { LeadListItem, Prioridade } from '@/types/api';

const PRIORIDADES: Prioridade[] = ['CRITICA', 'ALTA', 'MEDIA', 'BAIXA'];

const PRIORIDADE_COR: Record<Prioridade, string> = {
  CRITICA: 'bg-red-600 text-white',
  ALTA: 'bg-orange-500 text-white',
  MEDIA: 'bg-yellow-500 text-white',
  BAIXA: 'bg-slate-300 text-slate-700',
};

interface DashboardStats {
  totalLeads: number;
  abertos: number;
  porPrioridade: Record<Prioridade, number>;
  criticos: LeadListItem[];
}

async function loadStats(): Promise<DashboardStats> {
  const page = await listLeads({ perPage: 100 });
  const items = page.items ?? [];
  const porPrioridade: Record<Prioridade, number> = { CRITICA: 0, ALTA: 0, MEDIA: 0, BAIXA: 0 };
  for (const lead of items) {
    porPrioridade[lead.prioridade] = (porPrioridade[lead.prioridade] ?? 0) + 1;
  }
  const criticos = items
    .filter((l) => l.prioridade === 'CRITICA' && l.status === 'aberto')
    .sort((a, b) => b.scoreRisco - a.scoreRisco)
    .slice(0, 8);
  const abertos = items.filter((l) => l.status === 'aberto').length;
  return { totalLeads: page.total ?? items.length, abertos, porPrioridade, criticos };
}

export default async function DashboardPage() {
  let stats: DashboardStats;
  try {
    stats = await loadStats();
  } catch {
    return (
      <div className="card">
        <div className="card-body text-sm text-slate-500">
          Falha ao carregar dados do backend. Verifique se o serviço de domínio está respondendo na rede interna.
        </div>
      </div>
    );
  }

  const pieData = PRIORIDADES.map((prioridade) => ({
    perfil: prioridade,
    count: stats.porPrioridade[prioridade] ?? 0,
  }));

  return (
    <div className="space-y-10">
      <header>
        <p className="eyebrow">Visão executiva</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900">Funil de retenção pós-venda</h1>
        <div className="ford-rule mt-4" />
        <p className="mt-6 max-w-2xl text-base leading-relaxed text-slate-600">
          Status do ciclo de classificação D0 hoje. Cada lead representa um cliente classificado como risco
          de evasão e pronto para abordagem antes da primeira revisão.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-px overflow-hidden rounded-md border border-slate-200 bg-slate-200 sm:grid-cols-3">
        <div className="bg-white px-6 py-6">
          <p className="eyebrow">Leads classificados</p>
          <p className="metric">{stats.totalLeads}</p>
          <p className="mt-2 text-xs text-slate-500">Total acumulado no ciclo atual.</p>
        </div>
        <div className="bg-white px-6 py-6">
          <p className="eyebrow">Abertos no funil</p>
          <p className="metric">{stats.abertos}</p>
          <p className="mt-2 text-xs text-slate-500">Aguardam contato do consultor.</p>
        </div>
        <div className="bg-white px-6 py-6">
          <p className="eyebrow">Críticos hoje</p>
          <p className="metric metric-negative">{stats.criticos.length}</p>
          <p className="mt-2 text-xs text-slate-500">Score acima de 0,85. Ação imediata.</p>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="card lg:col-span-2">
          <div className="card-header">
            <p className="eyebrow">Distribuição por prioridade</p>
          </div>
          <div className="card-body">
            <PerfilPie data={pieData} />
            <ul className="mt-6 space-y-3 text-sm">
              {pieData.map((row) => (
                <li key={row.perfil} className="flex items-center justify-between">
                  <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${PRIORIDADE_COR[row.perfil as Prioridade]}`}>
                    {row.perfil}
                  </span>
                  <span className="font-semibold text-slate-800">{row.count}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="card lg:col-span-3">
          <div className="card-header flex items-center justify-between">
            <p className="eyebrow">Leads críticos do dia</p>
            <Link href="/leads" className="text-xs font-semibold uppercase tracking-[0.12em] text-ford hover:underline">
              Ver todos →
            </Link>
          </div>
          <div className="card-body">
            {stats.criticos.length === 0 ? (
              <p className="py-12 text-center text-sm text-slate-400">
                Nenhum lead crítico aberto no momento.
              </p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {stats.criticos.map((lead) => (
                  <li key={lead.id}>
                    <Link
                      href={`/leads/${lead.id}`}
                      className="flex items-center justify-between gap-4 py-4 transition hover:bg-slate-50 -mx-2 px-2 rounded-sm"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-slate-900">{lead.nomeCliente}</p>
                        <p className="mt-0.5 truncate text-xs text-slate-500">
                          {lead.modeloVeiculo}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 whitespace-nowrap">
                        <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${PRIORIDADE_COR[lead.prioridade]}`}>
                          {lead.prioridade}
                        </span>
                        <span className="text-xs font-semibold text-slate-700">{formatPercent(lead.scoreRisco)}</span>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
