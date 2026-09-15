import { getSession } from '@/lib/auth';
import type {
  LeadDetail,
  LeadListPage,
  LeadPatchRequest,
  LoginRequest,
  LoginResponse,
  RawLoginResponse,
} from '@/types/api';

// Base interna: Gateway (borda LGPD) por padrão. Pode apontar direto ao Core em setups isolados.
const INTERNAL_BASE = process.env.INTERNAL_GATEWAY_URL ?? 'http://gateway:8000';

// Cabe dentro do maxDuration (60 s) das route handlers; cobre o cold start de free tier.
const UPSTREAM_TIMEOUT_MS = 55_000;

function buildUrl(path: string): string {
  return `${INTERNAL_BASE.replace(/\/$/, '')}${path.startsWith('/') ? path : `/${path}`}`;
}

/**
 * Headers de correlação para o backend: IP real do navegador (o gateway aplica rate limit,
 * lockout e audit por IP; sem isso todos os usuários do painel chegam com o IP do container)
 * e o X-Request-Id que o nginx/gateway possam ter atribuído.
 */
export function forwardingHeaders(request: Request): Record<string, string> {
  const headers: Record<string, string> = {};
  // X-Real-IP é definido pelo proxy confiável (nginx/Vercel) a partir da conexão e não pode ser
  // forjado pelo cliente; X-Forwarded-For fica como fallback (primeiro salto).
  const clientIp = request.headers.get('x-real-ip') ?? request.headers.get('x-forwarded-for')?.split(',')[0];
  if (clientIp && clientIp.trim()) headers['X-Forwarded-For'] = clientIp.trim();
  const requestId = request.headers.get('x-request-id');
  if (requestId) headers['X-Request-Id'] = requestId;
  return headers;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = getSession();
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(init.headers as Record<string, string> | undefined),
  };
  if (session) {
    headers.Authorization = `Bearer ${session.token}`;
  }
  const res = await fetch(buildUrl(path), {
    ...init,
    headers,
    cache: 'no-store',
    signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new ApiError(res.status, body);
  }
  return (await res.json()) as T;
}

export class ApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`request failed (${status})`);
  }
}

export async function login(payload: LoginRequest, extraHeaders: Record<string, string> = {}): Promise<LoginResponse> {
  const res = await fetch(buildUrl('/v1/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
    body: JSON.stringify(payload),
    cache: 'no-store',
    signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new ApiError(res.status, body);
  }
  return normalizeLogin((await res.json()) as RawLoginResponse);
}

/**
 * Gateway (FastAPI) responde snake_case com refresh token; Core (Spring) responde camelCase.
 * O painel só precisa do access token, do papel e da validade.
 */
export function normalizeLogin(raw: RawLoginResponse): LoginResponse {
  const accessToken = raw.accessToken ?? raw.access_token;
  if (!accessToken) {
    throw new ApiError(502, 'login response without access token');
  }
  return {
    accessToken,
    tokenType: raw.tokenType ?? raw.token_type ?? 'Bearer',
    expiresIn: raw.expiresIn ?? raw.access_expires_in ?? 900,
    role: raw.role,
  };
}

export interface LeadsQuery {
  status?: string;
  prioridade?: string;
  page?: number;
  perPage?: number;
}

export async function listLeads(query: LeadsQuery = {}): Promise<LeadListPage> {
  const params = new URLSearchParams();
  if (query.status) params.set('status', query.status);
  if (query.prioridade) params.set('prioridade', query.prioridade);
  params.set('page', String(query.page ?? 1));
  params.set('per_page', String(query.perPage ?? 50));
  return request<LeadListPage>(`/v1/leads?${params.toString()}`);
}

export async function getLead(id: string): Promise<LeadDetail> {
  return request<LeadDetail>(`/v1/leads/${encodeURIComponent(id)}`);
}

export async function patchLead(
  id: string,
  payload: LeadPatchRequest,
  extraHeaders: Record<string, string> = {},
): Promise<LeadDetail> {
  return request<LeadDetail>(`/v1/leads/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
    body: JSON.stringify(payload),
  });
}
