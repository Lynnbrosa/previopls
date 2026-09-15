import Link from 'next/link';
import { redirect } from 'next/navigation';
import { ApiError, listLeads } from '@/lib/api';
import { BackendError } from '@/components/backend-error';
import { formatDate, formatPercent } from '@/lib/utils';


import {
  PERFIL_COR,
  PERFIL_LABEL,
  PRIORIDADES,
  PRIORIDADE_COR,
  PRIORIDADE_LABEL,
  STATUSES,
  STATUS_COR,
  STATUS_LABEL,
} from '@/lib/labels';

// Leituras server-side esperam o backend acordar (free tier). Sem isso a função da Vercel
// morre em 10 s com 504 sem corpo e o card de diagnóstico nunca aparece.
export const maxDuration = 60;

export default async function LeadsPage({
  searchParams,
}: {
  searchParams: { prioridade?: string; status?: string; page?: string };
}) {
  const page = Number(searchParams.page ?? 1);
  const perPage = 25;

  let result;
  try {
    result = await listLeads({
      status: searchParams.status,
      prioridade: searchParams.prioridade,
      page,
      perPage,
    });
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) redirect('/login?motivo=sessao');
    return <BackendError error={err} />;
  }

  const items = result.items ?? [];
  const totalPages = Math.max(1, Math.ceil((result.total ?? items.length) / perPage));

  return (
    <div className="space-y-8">
      <header>
        <p className="eyebrow">Operação</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900">Leads</h1>
        <div className="ford-rule mt-4" />
        <p className="mt-4 text-sm text-slate-600">
          {result.total ?? items.length} {(result.total ?? items.length) === 1 ? 'resultado' : 'resultados'} no filtro atual.
        </p>
      </header>

      <section className="card">
        <div className="card-header">
          <form className="flex flex-wrap items-end gap-4 text-sm">
            <FiltroSelect name="status" label="Status" valor={searchParams.status} opcoes={STATUSES} labels={STATUS_LABEL} />
            <FiltroSelect name="prioridade" label="Prioridade" valor={searchParams.prioridade} opcoes={PRIORIDADES} labels={PRIORIDADE_LABEL} />
            <div className="flex gap-2">
              <button type="submit" className="btn-primary">Filtrar</button>
              <Link href="/leads" className="btn-secondary">Limpar</Link>
            </div>
          </form>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Cliente</th>
                <th className="px-6 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Veículo</th>
                <th className="px-6 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Perfil</th>
                <th className="px-6 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Prioridade</th>
                <th className="px-6 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Score</th>
                <th className="px-6 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Status</th>
                <th className="px-6 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">Criado</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-sm text-slate-400">
                    Nenhum lead encontrado para os filtros atuais.
                  </td>
                </tr>
              ) : (
                items.map((lead) => (
                  <tr key={lead.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-semibold text-slate-900">{lead.nomeCliente}</td>
                    <td className="px-6 py-4 text-slate-700">{lead.modeloVeiculo}</td>
                    <td className="px-6 py-4">
                      {lead.perfil ? (
                        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${PERFIL_COR[lead.perfil]}`}>
                          {PERFIL_LABEL[lead.perfil]}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${PRIORIDADE_COR[lead.prioridade]}`}>
                        {PRIORIDADE_LABEL[lead.prioridade]}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-800">{formatPercent(lead.scoreRisco)}</td>
                    <td className="px-6 py-4">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COR[lead.status]}`}>
                        {STATUS_LABEL[lead.status]}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-500">{formatDate(lead.criadoEm)}</td>
                    <td className="px-6 py-4 text-right">
                      <Link href={`/leads/${lead.id}`} className="text-xs font-semibold uppercase tracking-[0.12em] text-ford hover:underline">
                        Abrir →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 px-6 py-4">
          <p className="text-xs text-slate-500">
            Página {page} de {totalPages}
          </p>
          <div className="flex gap-2">
            {page > 1 && (
              <Link
                href={{ pathname: '/leads', query: { ...searchParams, page: page - 1 } }}
                className="btn-secondary"
              >
                Anterior
              </Link>
            )}
            {page < totalPages && (
              <Link
                href={{ pathname: '/leads', query: { ...searchParams, page: page + 1 } }}
                className="btn-secondary"
              >
                Próxima
              </Link>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function FiltroSelect({
  name,
  label,
  valor,
  opcoes,
  labels,
}: {
  name: string;
  label: string;
  valor?: string;
  opcoes: readonly string[];
  labels: Record<string, string>;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</span>
      <select name={name} defaultValue={valor ?? ''} className="input w-40 py-2">
        <option value="">todos</option>
        {opcoes.map((opt) => (
          <option key={opt} value={opt}>
            {labels[opt] ?? opt}
          </option>
        ))}
      </select>
    </label>
  );
}
