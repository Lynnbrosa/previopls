export type Perfil = 'FIEL' | 'ABANDONO' | 'ESQUECIDO' | 'ECONOMICO';

export type Prioridade = 'CRITICA' | 'ALTA' | 'MEDIA' | 'BAIXA';

export type StatusLead = 'aberto' | 'agendado' | 'recusado' | 'sem-contato';

export type Role = 'admin' | 'consultor' | 'analista';

export interface LoginRequest {
  email: string;
  senha: string;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  role: Role;
}

export interface Cliente {
  id: string;
  nome: string;
  cpf: string;
  email: string | null;
  telefone: string | null;
  regiao: string;
  perfil: Perfil | null;
  scoreRisco: number | null;
  criadoEm: string;
  classificadoEm: string | null;
}

export interface Veiculo {
  id: string;
  modelo: string;
  versao: string;
  ano: number;
  vin: string;
  dataCompra: string;
  valorCompra: string;
  concessionariaId: string;
}

export interface LeadListItem {
  id: string;
  clienteId: string;
  veiculoId: string;
  nomeCliente: string;
  modeloVeiculo: string;
  scoreRisco: number;
  prioridade: Prioridade;
  status: StatusLead;
  criadoEm: string;
}

export interface LeadDetail {
  id: string;
  scoreRisco: number;
  prioridade: Prioridade;
  status: StatusLead;
  scriptOferta: string;
  observacao: string | null;
  criadoEm: string;
  atualizadoEm: string;
  cliente: Cliente;
  veiculo: Veiculo;
}

export interface LeadListPage {
  items: LeadListItem[];
  page: number;
  perPage: number;
  total: number;
}

export interface LeadPatchRequest {
  status: StatusLead;
  observacao?: string;
}
