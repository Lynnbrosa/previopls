import type { PerfilCliente, PrioridadeLead, StatusLead } from '@/types';

export const PERFIL_LABEL: Record<PerfilCliente, string> = {
  fiel: 'Fiel',
  abandono: 'Abandono',
  esquecido: 'Esquecido',
  economico: 'Econômico',
};

export const PERFIL_COLOR: Record<PerfilCliente, string> = {
  abandono: '#d32f2f',
  esquecido: '#f57c00',
  economico: '#fbc02d',
  fiel: '#388e3c',
};

export const PRIORIDADE_LABEL: Record<PrioridadeLead, string> = {
  critica: 'CRÍTICA',
  alta: 'ALTA',
  media: 'MÉDIA',
  baixa: 'BAIXA',
};

export const PRIORIDADE_COLOR: Record<PrioridadeLead, string> = {
  critica: '#b71c1c',
  alta: '#e53935',
  media: '#fb8c00',
  baixa: '#43a047',
};

export const STATUS_LABEL: Record<StatusLead, string> = {
  aberto: 'Aberto',
  agendado: 'Agendado',
  recusado: 'Recusado',
  'sem-contato': 'Sem contato',
};

/**
 * Fallback: inferência de perfil a partir do score quando o backend não
 * devolve `perfil` no item da lista (versões antigas do Core).
 * O Core atual já envia o perfil classificado pelo ml-api; prefira-o.
 */
export function perfilFromScore(score: number): PerfilCliente {
  if (score >= 0.78) return 'abandono';
  if (score >= 0.55) return 'esquecido';
  if (score >= 0.30) return 'economico';
  return 'fiel';
}
