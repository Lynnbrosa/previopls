import { create } from 'zustand';
import api from '@/lib/api';
import { Cache } from '@/lib/storage';
import { notifyNewCriticalLead } from '@/lib/notifications';
import type {
  LeadDetail,
  LeadListItem,
  LeadListResponse,
  PrioridadeLead,
  StatusLead,
} from '@/types';

const CACHE_KEY = 'leads:items:v1';

interface Filters {
  status?: StatusLead;
  prioridade?: PrioridadeLead;
}

interface LeadsState {
  items: LeadListItem[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  filters: Filters;
  knownCriticalIds: Set<string>;

  hydrate: () => Promise<void>;
  setFilters: (f: Filters) => void;
  fetchLeads: () => Promise<void>;
  refreshLeads: () => Promise<void>;
  patchStatus: (id: string, status: StatusLead, observacao?: string) => Promise<LeadDetail>;
}

function buildParams(filters: Filters) {
  const params: Record<string, string | number> = {
    status: filters.status ?? 'aberto',
    per_page: 100,
  };
  if (filters.prioridade) params.prioridade = filters.prioridade;
  return params;
}

async function detectAndNotify(items: LeadListItem[], known: Set<string>): Promise<Set<string>> {
  const next = new Set(known);
  for (const lead of items) {
    if (lead.prioridade === 'critica' && !known.has(lead.id)) {
      await notifyNewCriticalLead(lead.id, lead.nomeCliente, lead.modeloVeiculo);
      next.add(lead.id);
    }
    if (lead.prioridade === 'critica') next.add(lead.id);
  }
  return next;
}

export const useLeadsStore = create<LeadsState>((set, get) => ({
  items: [],
  loading: false,
  refreshing: false,
  error: null,
  filters: { status: 'aberto' },
  knownCriticalIds: new Set(),

  hydrate: async () => {
    const cached = await Cache.get<LeadListItem[]>(CACHE_KEY);
    if (cached && cached.length > 0) set({ items: cached });
  },

  setFilters: (f) => {
    set({ filters: f });
  },

  fetchLeads: async () => {
    const { items, filters, knownCriticalIds } = get();
    set({ loading: items.length === 0, error: null });
    try {
      const { data } = await api.get<LeadListResponse>('/v1/leads', {
        params: buildParams(filters),
      });
      const nextKnown = await detectAndNotify(data.items, knownCriticalIds);
      set({ items: data.items, loading: false, knownCriticalIds: nextKnown });
      await Cache.set(CACHE_KEY, data.items);
    } catch (e: any) {
      set({
        loading: false,
        error: e?.response?.data?.error?.message ?? 'Erro ao carregar leads.',
      });
    }
  },

  refreshLeads: async () => {
    const { filters, knownCriticalIds } = get();
    set({ refreshing: true, error: null });
    try {
      const { data } = await api.get<LeadListResponse>('/v1/leads', {
        params: buildParams(filters),
      });
      const nextKnown = await detectAndNotify(data.items, knownCriticalIds);
      set({ items: data.items, knownCriticalIds: nextKnown });
      await Cache.set(CACHE_KEY, data.items);
    } catch (e: any) {
      set({
        error: e?.response?.data?.error?.message ?? 'Erro ao atualizar leads.',
      });
    } finally {
      set({ refreshing: false });
    }
  },

  patchStatus: async (id, status, observacao) => {
    const { data } = await api.patch<LeadDetail>(`/v1/leads/${id}`, { status, observacao });

    set((s) => ({
      items:
        status === 'aberto'
          ? s.items.map((l) => (l.id === id ? { ...l, status } : l))
          : s.items.filter((l) => l.id !== id),
    }));
    await Cache.set(CACHE_KEY, get().items);
    return data;
  },
}));
