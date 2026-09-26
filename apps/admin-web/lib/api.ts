import { getSession } from '@/lib/auth';
import type {
  BackendDiagnosis,
  LeadDetail,
  LeadListPage,
  LeadPatchRequest,
  LoginRequest,
  LoginResponse,
  RawLoginResponse,
} from '@/types/api';

// Base interna: Gateway (borda LGPD) por padrão. Pode apontar direto ao Core em setups isolados.
const INTERNAL_BASE = process.env.INTERNAL_GATEWAY_URL ?? 'http://gateway:8000';

// Cabe dentro do maxDuration (60 s) das route handlers e páginas, com folga para o diagnóstico
// (DIAG_TIMEOUT_MS) rodar depois de uma falha; cobre o cold start do Gateway em free tier.
const UPSTREAM_TIMEOUT_MS = 50_000;
const DIAG_TIMEOUT_MS = 5_000;

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
  const clientIp = (request.headers.get('x-real-ip') ?? request.headers.get('x-forwarded-for')?.split(',')[0] ?? '').trim();
  // Só repassa algo com cara de IP (v4/v6) e curto: o gateway grava em VARCHAR(64) e um header
  // forjado não deve virar erro 500 nem lixo na trilha de auditoria.
  if (clientIp && clientIp.length <= 64 && /^[0-9a-fA-F.:]+$/.test(clientIp)) headers['X-Forwarded-For'] = clientIp;
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
    console.error(`[admin-web] ${init.method ?? 'GET'} ${buildUrl(path)} -> ${res.status} ${body.slice(0, 300)}`);
    throw new ApiError(res.status, body);
  }
  return (await res.json()) as T;
}

export class ApiError extends Error {
  /** Código do contrato {error:{code,message}} do gateway/core, quando o corpo é JSON. */
  public code: string | null = null;
  public backendMessage: string | null = null;

  constructor(public status: number, public body: string) {
    super(`request failed (${status})`);
    try {
      const parsed = JSON.parse(body) as { error?: { code?: string; message?: string }; message?: string; detail?: string };
      this.code = parsed?.error?.code ?? null;
      this.backendMessage = parsed?.error?.message ?? parsed?.message ?? parsed?.detail ?? null;
    } catch {
      // corpo não é JSON (proxy/plataforma): fica só o status
    }
  }
}

/** Host do backend interno, sem credenciais, para aparecer em mensagens de diagnóstico. */
export function backendLabel(): string {
  try {
    return new URL(INTERNAL_BASE).host;
  } catch {
    return INTERNAL_BASE;
  }
}

/**
 * Texto para o usuário quando uma leitura do backend falha. Deliberadamente informativo:
 * o painel é interno e o status/código do backend é o que resolve o problema mais rápido.
 */
export function describeApiError(err: unknown, opts: { autoRetry?: boolean } = {}): string {
  const backend = backendLabel();
  // Só quem realmente tenta de novo (o card de erro) promete isso; a route de PATCH não tenta.
  const retry = opts.autoRetry ? 'O painel tenta de novo sozinho.' : 'Tente novamente em alguns segundos.';
  if (err instanceof ApiError) {
    const suffix = err.code ? ` (${err.status} ${err.code})` : ` (HTTP ${err.status})`;
    if (err.status === 401) return `Sessão inválida ou expirada${suffix}. Entre novamente.`;
    if (err.status === 403) return `Seu papel não tem acesso a este recurso${suffix}.`;
    if (err.status === 404) return `Recurso não encontrado no backend${suffix}.`;
    if (err.status === 429) return `Limite de requisições do backend atingido${suffix}. Aguarde um minuto.`;
    if (err.code === 'CORE_AUTH_MISMATCH') {
      return `O Gateway (${backend}) autenticou você, mas o Core rejeitou o token interno${suffix}. JWT_SECRET precisa ser o mesmo no gateway e no core; relógios dessincronizados entre os dois também causam isso.`;
    }
    if (err.code === 'CORE_UNAVAILABLE') {
      return `O Gateway (${backend}) não conseguiu falar com o Core${suffix}. Se o Core roda em free tier ele pode estar acordando. ${retry}`;
    }
    if (err.status >= 500) return `O backend ${backend} respondeu erro${suffix}${err.backendMessage ? `: ${err.backendMessage}` : ''}.`;
    return `Falha ao consultar o backend ${backend}${suffix}${err.backendMessage ? `: ${err.backendMessage}` : ''}.`;
  }
  if (err instanceof Error && (err.name === 'TimeoutError' || err.name === 'AbortError')) {
    return `O backend ${backend} não respondeu a tempo (pode estar acordando). ${retry}`;
  }
  if (err instanceof SyntaxError) {
    return `O backend ${backend} respondeu, mas o corpo não é JSON. A URL em INTERNAL_GATEWAY_URL aponta para outro serviço ou proxy?`;
  }
  return `Não foi possível conectar ao backend ${backend}. Verifique INTERNAL_GATEWAY_URL e se o serviço está no ar.`;
}

/** Erros que costumam passar sozinhos (backend acordando, Core reiniciando): o card tenta de novo. */
export function isTransientError(err: unknown): boolean {
  if (err instanceof ApiError) {
    if (err.code === 'CORE_AUTH_MISMATCH') return false; // configuração: insistir não resolve
    return err.status === 502 || err.status === 503 || err.status === 504;
  }
  // 2xx cujo corpo não é JSON (URL apontando para outro serviço): determinístico, insistir não resolve.
  if (err instanceof SyntaxError) return false;
  return true; // rede, DNS, timeout
}

function errorDetail(reason: unknown): string | null {
  if (!(reason instanceof Error)) return null;
  // fetch do Node embrulha o erro de socket em cause (ENOTFOUND, ECONNREFUSED, ECONNRESET...).
  const cause = (reason as Error & { cause?: { code?: string; message?: string } }).cause;
  return cause?.code ?? cause?.message ?? reason.message ?? reason.name;
}

/**
 * Consulta /health e /version do backend para o card de erro mostrar onde a cadeia quebrou
 * (painel → gateway → banco → core). Nunca lança: qualquer falha vira 'down' ou 'timeout'.
 */
export async function diagnoseBackend(): Promise<BackendDiagnosis> {
  const diag: BackendDiagnosis = {
    backend: backendLabel(),
    defaultBase: !process.env.INTERNAL_GATEWAY_URL,
    vercel: process.env.VERCEL === '1',
    gateway: 'down',
    status: null,
    components: {},
    mode: null,
    version: null,
    detail: null,
  };
  const probe = (path: string) =>
    fetch(buildUrl(path), {
      cache: 'no-store',
      headers: { Accept: 'application/json' },
      signal: AbortSignal.timeout(DIAG_TIMEOUT_MS),
    });
  const [health, version] = await Promise.allSettled([probe('/health'), probe('/version')]);

  if (health.status === 'fulfilled') {
    diag.status = health.value.status;
    const body = (await health.value.json().catch(() => null)) as
      | { status?: string; mode?: string; components?: Record<string, string> }
      | null;
    if (!body) {
      diag.detail = `GET /health respondeu HTTP ${health.value.status} sem JSON`;
    } else {
      diag.components = body.components ?? {};
      diag.mode = body.mode ?? null;
      if (body.status === 'degraded' || health.value.status === 503) diag.gateway = 'degraded';
      else if (health.value.ok) diag.gateway = 'up';
    }
  } else {
    const reason: unknown = health.reason;
    const timedOut = reason instanceof Error && (reason.name === 'TimeoutError' || reason.name === 'AbortError');
    diag.gateway = timedOut ? 'timeout' : 'down';
    diag.detail = errorDetail(reason);
  }

  if (version.status === 'fulfilled' && version.value.ok) {
    const v = (await version.value.json().catch(() => null)) as { version?: string; mode?: string } | null;
    diag.version = v?.version ?? null;
    diag.mode = diag.mode ?? v?.mode ?? null;
  }
  return diag;
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
