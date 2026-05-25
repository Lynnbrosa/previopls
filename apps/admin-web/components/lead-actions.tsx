'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import type { StatusLead } from '@/types/api';

const ACTIONS: { status: StatusLead; label: string; tone: string }[] = [
  { status: 'agendado', label: 'Agendar', tone: 'bg-emerald-600 hover:bg-emerald-700 text-white' },
  { status: 'recusado', label: 'Recusado pelo cliente', tone: 'bg-red-600 hover:bg-red-700 text-white' },
  { status: 'sem-contato', label: 'Sem contato', tone: 'bg-slate-600 hover:bg-slate-700 text-white' },
];

export function LeadActions({ leadId, currentStatus }: { leadId: string; currentStatus: StatusLead }) {
  const router = useRouter();
  const [pending, setPending] = useState<StatusLead | null>(null);
  const [observacao, setObservacao] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function submit(status: StatusLead) {
    setError(null);
    setPending(status);
    try {
      const res = await fetch(`/api/leads/${encodeURIComponent(leadId)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, observacao: observacao || undefined }),
      });
      if (!res.ok) {
        setError('Falha ao atualizar lead');
        setPending(null);
        return;
      }
      router.refresh();
    } finally {
      setPending(null);
    }
  }

  if (currentStatus !== 'aberto') {
    return (
      <p className="text-sm text-slate-500">
        Este lead já foi marcado como <span className="font-medium">{currentStatus}</span>. Nenhuma ação pendente.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="label" htmlFor="observacao">Observação (opcional)</label>
        <textarea
          id="observacao"
          rows={3}
          value={observacao}
          onChange={(e) => setObservacao(e.target.value.slice(0, 500))}
          className="input"
          placeholder="ex: Agendado para 18/05 às 14h, cliente confirmou por WhatsApp."
        />
      </div>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        {ACTIONS.map((action) => (
          <button
            key={action.status}
            type="button"
            disabled={pending !== null}
            onClick={() => submit(action.status)}
            className={`inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition disabled:opacity-50 ${action.tone}`}
          >
            {pending === action.status ? 'Salvando...' : action.label}
          </button>
        ))}
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
