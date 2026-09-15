'use client';

import { useEffect, useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import type { BackendDiagnosis } from '@/types/api';

const RETRY_SECONDS = 20;
// 15 tentativas automáticas ≈ 5 min: cobre o cold start de JVM em free tier sem insistir para sempre.
const MAX_AUTO_RETRIES = 15;

type Tone = 'ok' | 'warn' | 'bad' | 'muted';

const TONE: Record<Tone, string> = {
  ok: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  warn: 'bg-amber-50 text-amber-700 ring-amber-200',
  bad: 'bg-red-50 text-red-700 ring-red-200',
  muted: 'bg-slate-100 text-slate-600 ring-slate-200',
};

function toneFor(state: string | undefined): Tone {
  if (state === 'up' || state === 'ok') return 'ok';
  if (state === 'degraded') return 'warn';
  if (state === 'down' || state === 'timeout') return 'bad';
  return 'muted';
}

function labelFor(state: string | undefined): string {
  switch (state) {
    case 'up':
    case 'ok':
      return 'no ar';
    case 'degraded':
      return 'degradado';
    case 'down':
      return 'fora';
    case 'timeout':
      return 'sem resposta';
    default:
      return 'desconhecido';
  }
}

/** Uma dica objetiva por elo quebrado; vazio quando o /health está limpo (o erro em si explica). */
function hintsFor(d: BackendDiagnosis): string[] {
  if (d.gateway === 'down' || d.gateway === 'timeout') {
    if (d.defaultBase) {
      return [
        `INTERNAL_GATEWAY_URL não está definida neste ambiente: o painel está usando o default do compose (${d.backend}).` +
          (d.vercel ? ' Na Vercel, defina a URL pública do Gateway (Render) no escopo Production e faça redeploy.' : ''),
      ];
    }
    if (d.gateway === 'timeout') {
      return [`O Gateway em ${d.backend} não respondeu em 5 s. Em free tier (Render) o serviço acorda em 30 a 60 s.`];
    }
    return [
      `Sem conexão com ${d.backend}${d.detail ? ` (${d.detail})` : ''}. Confira se o serviço está no ar e se a URL está correta (https, sem caminho extra).`,
    ];
  }
  const out: string[] = [];
  if (d.components.database === 'down') out.push('O Gateway não alcança o Postgres dele (DATABASE_URL).');
  if (d.components.core === 'down') {
    out.push('O Core não respondeu ao Gateway (CORE_API_URL). Em free tier ele leva 1 a 2 min para acordar; o Gateway já pediu para ele subir.');
  }
  return out;
}

export function BackendErrorCard({
  message,
  retryable,
  diagnosis,
}: {
  message: string;
  retryable: boolean;
  diagnosis: BackendDiagnosis;
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [seconds, setSeconds] = useState(RETRY_SECONDS);
  const [attempts, setAttempts] = useState(0);
  const autoRetry = retryable && attempts < MAX_AUTO_RETRIES;

  // router.refresh() refaz a leitura no servidor: se der certo, este card sai da tela;
  // se falhar de novo, ele é re-renderizado com um diagnóstico fresco e a contagem recomeça.
  useEffect(() => {
    if (!autoRetry || isPending) return;
    if (seconds <= 0) {
      setAttempts((n) => n + 1);
      setSeconds(RETRY_SECONDS);
      startTransition(() => router.refresh());
      return;
    }
    const timer = setTimeout(() => setSeconds((s) => s - 1), 1000);
    return () => clearTimeout(timer);
  }, [seconds, autoRetry, isPending, router]);

  function retryNow() {
    setAttempts((n) => n + 1);
    setSeconds(RETRY_SECONDS);
    startTransition(() => router.refresh());
  }

  const core = diagnosis.components.core;
  const rows: { label: string; value: string; state?: string }[] = [
    { label: 'Painel → Gateway', value: diagnosis.backend, state: diagnosis.gateway },
    { label: 'Gateway → Banco', value: 'Postgres do Gateway', state: diagnosis.components.database },
    {
      label: 'Gateway → Core',
      value: core ? 'serviço de domínio (CORE_API_URL)' : diagnosis.mode === 'standalone' ? 'não usado (modo standalone)' : 'serviço de domínio',
      state: core ?? (diagnosis.mode === 'standalone' ? 'ok' : undefined),
    },
  ];
  const tips = hintsFor(diagnosis);

  return (
    <div className="card border-l-4 border-l-red-600">
      <div className="card-header flex flex-wrap items-center justify-between gap-3">
        <p className="eyebrow">Backend indisponível</p>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          {isPending ? (
            <span>Consultando de novo…</span>
          ) : autoRetry ? (
            <span>
              Nova tentativa em {seconds} s{attempts > 0 ? ` · ${attempts} até agora` : ''}
            </span>
          ) : attempts > 0 ? (
            <span>{attempts} tentativas</span>
          ) : null}
          <button type="button" onClick={retryNow} disabled={isPending} className="btn-secondary px-4 py-2">
            {isPending ? 'Aguarde…' : 'Tentar novamente'}
          </button>
        </div>
      </div>
      <div className="card-body space-y-5 text-sm text-slate-700">
        <p className="font-medium text-slate-900">{message}</p>

        <div>
          <p className="eyebrow mb-2">Diagnóstico</p>
          <ul className="divide-y divide-slate-100 rounded-sm border border-slate-200">
            {rows.map((row) => (
              <li key={row.label} className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5">
                <div className="min-w-0">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500">{row.label}</p>
                  <p className="truncate font-mono text-xs text-slate-700">{row.value}</p>
                </div>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${TONE[toneFor(row.state)]}`}>
                  {labelFor(row.state)}
                </span>
              </li>
            ))}
          </ul>
          {(diagnosis.version || diagnosis.mode || diagnosis.status) && (
            <p className="mt-2 text-xs text-slate-500">
              Gateway{diagnosis.version ? ` v${diagnosis.version}` : ''}
              {diagnosis.mode ? ` · modo ${diagnosis.mode}` : ''}
              {diagnosis.status ? ` · /health HTTP ${diagnosis.status}` : ''}
            </p>
          )}
        </div>

        {tips.length > 0 && (
          <ul className="list-disc space-y-1 pl-5">
            {tips.map((tip) => (
              <li key={tip}>{tip}</li>
            ))}
          </ul>
        )}

        <p className="text-xs text-slate-500">
          O painel lê os dados pelo servidor (INTERNAL_GATEWAY_URL). Passo a passo em{' '}
          <code>infra/deploy/vercel-admin-web.md</code> e nos logs do serviço admin-web.
        </p>
      </div>
    </div>
  );
}
