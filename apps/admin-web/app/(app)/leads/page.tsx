import Link from 'next/link';
import { listLeads } from '@/lib/api';
import { formatDate, formatPercent } from '@/lib/utils';
import type { Perfil, Prioridade, StatusLead } from '@/types/api';

const PERFIL_COR: Record<Perfil, string> = {
  FIEL: 'bg-blue-100 text-blue-800',
  ABANDONO: 'bg-red-100 text-red-800',
  ESQUECIDO: 'bg-amber-100 text-amber-800',
  ECONOMICO: 'bg-teal-100 text-teal-800',
};
const PRIORIDADE_COR: Record<Prioridade, string> = {
  CRITICA: 'bg-red-600 text-white',
  ALTA: 'bg-orange-500 text-white',
  MEDIA: 'bg-yellow-500 text-white',
  BAIXA: 'bg-slate-300 text-slate-700',
};
const STATUS_COR: Record<StatusLead, string> = {
  aberto: 'bg-emerald-100 text-emerald-700',
  agendado: 'bg-blue-100 text-blue-700',
  recusado: 'bg-red-50 text-red-700',
  'sem-contato': 'bg-slate-100 text-slate-600',
};

const PRIORIDADES: Prioridade[] = ['CRITICA', 'ALTA', 'MEDIA', 'BAIXA'];
const STATUSES: StatusLead[] = ['aberto', 'agendado', 'recusado', 'sem-contato'];
const PERFIS: Perfil[] = ['FIEL', 'ABANDONO', 'ESQUECIDO', 'ECONOMICO'];

export default async function LeadsPage({
  searchParams,
}: {
  searchParams: { prioridade?: string; status?: string; perfil?: string; page?: string };
}) {
  const page = Number(searchParams.page ?? 1);
  const perPage = 25;

  let result;
  try {
    result = await listLeads({
      status: searchParams.status,
      prioridade: searchParams.prioridade,
      perfil: searchParams.perfil,
      page,
      perPage,
    });
  } catch {
    return (
      <div className="card">
        <div className="card-body text-sm text-slate-500">Falha ao listar leads.</div>
      </div>
    );
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
            <FiltroSelect name="status" label="Status" valor={searchParams.status} opcoes={STATUSES} />
            <FiltroSelect name="prioridade" label="Prioridade" valor={searchParams.prioridade} opcoes={PRIORIDADES} />
            <FiltroSelect name="perfil" label="Perfil" valor={searchParams.perfil} opcoes={PERFIS} />
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
                    <td className="px-6 py-4 font-semibold text-slate-900">{lead.cliente.nome}</td>
                    <td className="px-6 py-4 text-slate-700">
                      {lead.veiculo.modelo}
                      <span className="text-slate-400"> {lead.veiculo.ano}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${PERFIL_COR[(lead.cliente.perfil ?? 'ESQUECIDO') as Perfil]}`}>
                        {lead.cliente.perfil ?? '—'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${PRIORIDADE_COR[lead.prioridade]}`}>
                        {lead.prioridade}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-800">{formatPercent(lead.scoreRisco)}</td>
                    <td className="px-6 py-4">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COR[lead.status]}`}>
                        {lead.status}
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
}: {
  name: string;
  label: string;
  valor?: string;
  opcoes: readonly string[];
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">{label}</span>
      <select name={name} defaultValue={valor ?? ''} className="input w-40 py-2">
        <option value="">todos</option>
        {opcoes.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </label>
  );
}
