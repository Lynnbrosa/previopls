import Link from 'next/link';
import { notFound } from 'next/navigation';
import { LeadActions } from '@/components/lead-actions';
import { ApiError, getLead } from '@/lib/api';
import { formatCurrency, formatDate, formatDateTime, formatPercent } from '@/lib/utils';
import type { Perfil, Prioridade } from '@/types/api';

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

export default async function LeadDetailPage({ params }: { params: { id: string } }) {
  let lead;
  try {
    lead = await getLead(params.id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  return (
    <div className="space-y-8">
      <nav className="flex items-center gap-2 text-xs uppercase tracking-[0.12em] text-slate-400">
        <Link href="/leads" className="font-semibold hover:text-ford">Leads</Link>
        <span>›</span>
        <span className="text-slate-700">{lead.cliente.nome}</span>
      </nav>

      <header>
        <p className="eyebrow">Visão 360 do cliente</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900">{lead.cliente.nome}</h1>
        <div className="ford-rule mt-4" />
        <p className="mt-4 text-sm text-slate-600">
          {lead.veiculo.modelo} {lead.veiculo.versao} · ano {lead.veiculo.ano} · concessionária{' '}
          {lead.veiculo.concessionariaId}
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-2">
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${PERFIL_COR[(lead.cliente.perfil ?? 'ESQUECIDO') as Perfil]}`}>
            {lead.cliente.perfil ?? 'sem perfil'}
          </span>
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${PRIORIDADE_COR[lead.prioridade]}`}>
            {lead.prioridade}
          </span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            Score {formatPercent(lead.scoreRisco)}
          </span>
        </div>
      </header>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <div className="card-header">
            <p className="eyebrow">Cliente</p>
          </div>
          <div className="card-body">
            <dl className="grid grid-cols-3 gap-y-3 text-sm">
              <dt className="text-slate-500">Nome</dt>
              <dd className="col-span-2 text-slate-800">{lead.cliente.nome}</dd>
              <dt className="text-slate-500">CPF</dt>
              <dd className="col-span-2 font-mono text-slate-800">{lead.cliente.cpf}</dd>
              <dt className="text-slate-500">Email</dt>
              <dd className="col-span-2 text-slate-800">{lead.cliente.email ?? '—'}</dd>
              <dt className="text-slate-500">Telefone</dt>
              <dd className="col-span-2 text-slate-800">{lead.cliente.telefone ?? '—'}</dd>
              <dt className="text-slate-500">Região</dt>
              <dd className="col-span-2 text-slate-800">{lead.cliente.regiao}</dd>
            </dl>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <p className="eyebrow">Veículo</p>
          </div>
          <div className="card-body">
            <dl className="grid grid-cols-3 gap-y-3 text-sm">
              <dt className="text-slate-500">Modelo</dt>
              <dd className="col-span-2 text-slate-800">
                {lead.veiculo.modelo} {lead.veiculo.versao}
              </dd>
              <dt className="text-slate-500">Ano</dt>
              <dd className="col-span-2 text-slate-800">{lead.veiculo.ano}</dd>
              <dt className="text-slate-500">VIN</dt>
              <dd className="col-span-2 font-mono text-xs text-slate-800">{lead.veiculo.vin}</dd>
              <dt className="text-slate-500">Data da compra</dt>
              <dd className="col-span-2 text-slate-800">{formatDate(lead.veiculo.dataCompra)}</dd>
              <dt className="text-slate-500">Valor</dt>
              <dd className="col-span-2 font-semibold text-slate-900">{formatCurrency(lead.veiculo.valorCompra)}</dd>
              <dt className="text-slate-500">Concessionária</dt>
              <dd className="col-span-2 text-slate-800">{lead.veiculo.concessionariaId}</dd>
            </dl>
          </div>
        </div>
      </section>

      <section className="card border-l-4 border-l-ford">
        <div className="card-header">
          <p className="eyebrow">Script comercial sugerido</p>
        </div>
        <div className="card-body">
          <p className="text-base leading-relaxed text-slate-700">{lead.scriptOferta}</p>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <p className="eyebrow">Ação do consultor</p>
        </div>
        <div className="card-body">
          <LeadActions leadId={lead.id} currentStatus={lead.status} />
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <p className="eyebrow">Histórico</p>
        </div>
        <div className="card-body">
          <dl className="grid grid-cols-3 gap-y-2 text-sm">
            <dt className="text-slate-500">Criado em</dt>
            <dd className="col-span-2 text-slate-800">{formatDateTime(lead.criadoEm)}</dd>
            <dt className="text-slate-500">Última atualização</dt>
            <dd className="col-span-2 text-slate-800">{formatDateTime(lead.atualizadoEm)}</dd>
            <dt className="text-slate-500">Observação</dt>
            <dd className="col-span-2 text-slate-800">{lead.observacao ?? '—'}</dd>
          </dl>
        </div>
      </section>
    </div>
  );
}
