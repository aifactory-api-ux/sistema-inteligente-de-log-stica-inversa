import { create } from 'zustand';
import { apiFetch } from '../lib/api';
import type {
  ReturnRequest,
  ReturnRequestCreate,
  ReturnsFilters,
  PaginatedResponse,
} from '../types/models';

interface ReturnsState {
  returns: ReturnRequest[];
  currentReturn: ReturnRequest | null;
  isLoading: boolean;
  error: string | null;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
  fetchReturns: (filters?: ReturnsFilters) => Promise<void>;
  fetchReturnById: (returnId: string) => Promise<ReturnRequest>;
  createReturn: (data: ReturnRequestCreate) => Promise<ReturnRequest>;
  updateReturn: (returnId: string, data: Partial<ReturnRequest>) => Promise<ReturnRequest>;
  setCurrentReturn: (ret: ReturnRequest | null) => void;
  clearError: () => void;
}

export const useReturnsStore = create<ReturnsState>((set, get) => ({
  returns: [],
  currentReturn: null,
  isLoading: false,
  error: null,
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0,
  },

  fetchReturns: async (filters) => {
    set({ isLoading: true, error: null });
    try {
      const params = new URLSearchParams();
      if (filters?.page) params.set('page', String(filters.page));
      if (filters?.page_size) params.set('page_size', String(filters.page_size));
      if (filters?.channel) params.set('channel', filters.channel);
      if (filters?.status) params.set('status', filters.status);
      if (filters?.destination) params.set('destination', filters.destination);
      if (filters?.customer_id) params.set('customer_id', filters.customer_id);
      if (filters?.date_from) params.set('date_from', filters.date_from);
      if (filters?.date_to) params.set('date_to', filters.date_to);
      if (filters?.sort_by) params.set('sort_by', filters.sort_by);
      if (filters?.sort_order) params.set('sort_order', filters.sort_order);

      const queryString = params.toString();
      const path = `/api/v1/returns${queryString ? `?${queryString}` : ''}`;

      const response = await apiFetch<PaginatedResponse<ReturnRequest>>(path);

      set({
        returns: response.items,
        pagination: {
          page: response.page,
          pageSize: response.page_size,
          total: response.total,
          totalPages: response.total_pages,
        },
        isLoading: false,
      });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch returns';
      set({ error: errorMessage, isLoading: false });
    }
  },

  fetchReturnById: async (returnId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiFetch<ReturnRequest>(`/api/v1/returns/${returnId}`);
      set({ currentReturn: response, isLoading: false });
      return response;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch return';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  createReturn: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiFetch<ReturnRequest>('/api/v1/returns', {
        method: 'POST',
        body: JSON.stringify(data),
      });
      set((state) => ({
        returns: [response, ...state.returns],
        currentReturn: response,
        isLoading: false,
      }));
      return response;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create return';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  updateReturn: async (returnId, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiFetch<ReturnRequest>(`/api/v1/returns/${returnId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      });
      set((state) => ({
        returns: state.returns.map((r) =>
          r.return_id === returnId ? response : r
        ),
        currentReturn: state.currentReturn?.return_id === returnId
          ? response
          : state.currentReturn,
        isLoading: false,
      }));
      return response;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update return';
      set({ error: errorMessage, isLoading: false });
      throw error;
    }
  },

  setCurrentReturn: (ret) => set({ currentReturn: ret }),

  clearError: () => set({ error: null }),
}));
