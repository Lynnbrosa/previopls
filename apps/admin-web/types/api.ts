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
  cpfMascarado: string;
  email: string;
  telefone: string;
  regiao: string;
  perfil: Perfil | null;
  scoreRisco: number | null;
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

export interface Lead {
  id: string;
  cliente: Cliente;
  veiculo: Veiculo;
  scoreRisco: number;
  prioridade: Prioridade;
  status: StatusLead;
  scriptOferta: string;
  observacao: string | null;
  criadoEm: string;
  atualizadoEm: string;
}

export interface LeadListPage {
  items: Lead[];
  page: number;
  perPage: number;
  total: number;
}

export interface LeadPatchRequest {
  status: StatusLead;
  observacao?: string;
}
