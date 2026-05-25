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
 * Inferência de perfil a partir do score quando o endpoint de lista
 * só retorna o score (e não o perfil do cliente).
 * Cortes idênticos aos buckets do MlService.classificar no backend.
 */
export function perfilFromScore(score: number): PerfilCliente {
  if (score >= 0.78) return 'abandono';
  if (score >= 0.55) return 'esquecido';
  if (score >= 0.30) return 'economico';
  return 'fiel';
}
