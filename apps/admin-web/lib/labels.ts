import type { Perfil, Prioridade, StatusLead } from '@/types/api';

/**
 * Rótulos e cores dos enums do domínio. Os valores (chaves) são exatamente os
 * que o Core serializa (@JsonValue em minúsculo); os rótulos são para exibição.
 */

export const PRIORIDADES: Prioridade[] = ['critica', 'alta', 'media', 'baixa'];
export const STATUSES: StatusLead[] = ['aberto', 'agendado', 'recusado', 'sem-contato'];
export const PERFIS: Perfil[] = ['fiel', 'abandono', 'esquecido', 'economico'];

export const PRIORIDADE_LABEL: Record<Prioridade, string> = {
  critica: 'CRÍTICA',
  alta: 'ALTA',
  media: 'MÉDIA',
  baixa: 'BAIXA',
};

export const PRIORIDADE_COR: Record<Prioridade, string> = {
  critica: 'bg-red-600 text-white',
  alta: 'bg-orange-500 text-white',
  media: 'bg-yellow-500 text-white',
  baixa: 'bg-slate-300 text-slate-700',
};

export const PRIORIDADE_HEX: Record<Prioridade, string> = {
  critica: '#dc2626',
  alta: '#f97316',
  media: '#eab308',
  baixa: '#94a3b8',
};

export const STATUS_LABEL: Record<StatusLead, string> = {
  aberto: 'Aberto',
  agendado: 'Agendado',
  recusado: 'Recusado',
  'sem-contato': 'Sem contato',
};

export const STATUS_COR: Record<StatusLead, string> = {
  aberto: 'bg-emerald-100 text-emerald-700',
  agendado: 'bg-blue-100 text-blue-700',
  recusado: 'bg-red-50 text-red-700',
  'sem-contato': 'bg-slate-100 text-slate-600',
};

export const PERFIL_LABEL: Record<Perfil, string> = {
  fiel: 'Fiel',
  abandono: 'Abandono',
  esquecido: 'Esquecido',
  economico: 'Econômico',
};

export const PERFIL_COR: Record<Perfil, string> = {
  fiel: 'bg-blue-100 text-blue-800',
  abandono: 'bg-red-100 text-red-800',
  esquecido: 'bg-amber-100 text-amber-800',
  economico: 'bg-teal-100 text-teal-800',
};

export const PERFIL_HEX: Record<Perfil, string> = {
  fiel: '#2563eb',
  abandono: '#dc2626',
  esquecido: '#f59e0b',
  economico: '#0d9488',
};
