import { getSession } from '@/lib/auth';
import type { LeadDetail, LeadListPage, LeadPatchRequest, LoginRequest, LoginResponse } from '@/types/api';

const INTERNAL_BASE = process.env.INTERNAL_GATEWAY_URL ?? 'http://gateway:8000';

function buildUrl(path: string): string {
  return `${INTERNAL_BASE.replace(/\/$/, '')}${path.startsWith('/') ? path : `/${path}`}`;
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

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const res = await fetch(buildUrl('/v1/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new ApiError(res.status, body);
  }
  return (await res.json()) as LoginResponse;
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

export async function patchLead(id: string, payload: LeadPatchRequest): Promise<LeadDetail> {
  return request<LeadDetail>(`/v1/leads/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
