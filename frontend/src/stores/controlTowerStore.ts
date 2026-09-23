import { create } from 'zustand';
import { apiFetch } from '../lib/api';
import type { KPIMetrics, DestinationDistribution, Alert, AlertFilters } from '../types/models';

interface ControlTowerState {
  kpis: KPIMetrics | null;
  distribution: DestinationDistribution | null;
  alerts: Alert[];
  unreadAlertCount: number;
  isLoading: boolean;
  lastUpdated: string | null;
  fetchKPIs: () => Promise<void>;
  fetchDistribution: () => Promise<void>;
  fetchAlerts: (filters?: AlertFilters) => Promise<void>;
  acknowledgeAlert: (alertId: string) => Promise<void>;
  subscribeToRealtime: () => () => void;
}

export const useControlTowerStore = create<ControlTowerState>((set, get) => ({
  kpis: null,
  distribution: null,
  alerts: [],
  unreadAlertCount: 0,
  isLoading: false,
  lastUpdated: null,

  fetchKPIs: async () => {
    set({ isLoading: true });
    try {
      const response = await apiFetch<KPIMetrics>('/api/v1/control-tower/kpis');
      set({
        kpis: response,
        lastUpdated: new Date().toISOString(),
        isLoading: false,
      });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchDistribution: async () => {
    try {
      const response = await apiFetch<DestinationDistribution>('/api/v1/control-tower/distribution');
      set({ distribution: response });
    } catch {
      // silently fail
    }
  },

  fetchAlerts: async (filters) => {
    set({ isLoading: true });
    try {
      const params = new URLSearchParams();
      if (filters?.priority) params.set('priority', filters.priority);
      if (filters?.acknowledged !== undefined) {
        params.set('acknowledged', String(filters.acknowledged));
      }
      if (filters?.limit) params.set('limit', String(filters.limit));

      const queryString = params.toString();
      const path = `/api/v1/control-tower/alerts${queryString ? `?${queryString}` : ''}`;

      const response = await apiFetch<{ alerts: Alert[]; total: number; unacknowledged_count: number }>(path);
      set({
        alerts: response.alerts,
        unreadAlertCount: response.unacknowledged_count,
        isLoading: false,
      });
    } catch {
      set({ isLoading: false });
    }
  },

  acknowledgeAlert: async (alertId) => {
    try {
      await apiFetch(`/api/v1/control-tower/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        body: JSON.stringify({}),
      });
      set((state) => ({
        alerts: state.alerts.map((a) =>
          a.alert_id === alertId ? { ...a, acknowledged_at: new Date().toISOString() } : a
        ),
        unreadAlertCount: Math.max(0, state.unreadAlertCount - 1),
      }));
    } catch {
      // silently fail
    }
  },

  subscribeToRealtime: () => {
    // Polling-based updates (MVP without WebSocket)
    const poll = () => {
      get().fetchKPIs();
      get().fetchDistribution();
      get().fetchAlerts();
    };

    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  },
}));
