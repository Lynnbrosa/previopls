export type RolePapel = 'admin' | 'consultor';

export type PerfilCliente = 'fiel' | 'abandono' | 'esquecido' | 'economico';

export type PrioridadeLead = 'critica' | 'alta' | 'media' | 'baixa';

export type StatusLead = 'aberto' | 'agendado' | 'recusado' | 'sem-contato';

export interface LoginRequest {
  email: string;
  senha: string;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  role: RolePapel;
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

export interface Cliente {
  id: string;
  nome: string;
  cpf: string;
  email?: string | null;
  telefone?: string | null;
  regiao: string;
  perfil?: PerfilCliente | null;
  scoreRisco?: number | null;
  criadoEm: string;
  classificadoEm?: string | null;
  veiculos?: Veiculo[];
}

export interface LeadListItem {
  id: string;
  clienteId: string;
  veiculoId: string;
  nomeCliente: string;
  modeloVeiculo: string;
  scoreRisco: number;
  prioridade: PrioridadeLead;
  status: StatusLead;
  criadoEm: string;
}

export interface LeadListResponse {
  items: LeadListItem[];
  page: number;
  perPage: number;
  total: number;
}

export interface LeadDetail {
  id: string;
  scoreRisco: number;
  prioridade: PrioridadeLead;
  status: StatusLead;
  scriptOferta?: string | null;
  observacao?: string | null;
  criadoEm: string;
  atualizadoEm: string;
  cliente: Cliente;
  veiculo: Veiculo;
}

export interface LeadPatchRequest {
  status: StatusLead;
  observacao?: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
