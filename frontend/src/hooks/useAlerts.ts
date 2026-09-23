import { useCallback, useState } from 'react';
import { apiFetch } from '../lib/api';
import type { Alert, AlertFilters, AlertPriority } from '../types/models';

interface UseAlertsReturn {
  alerts: Alert[];
  unacknowledgedCount: number;
  isLoading: boolean;
  error: string | null;
  fetchAlerts: (filters?: AlertFilters) => Promise<void>;
  acknowledgeAlert: (alertId: string) => Promise<void>;
  acknowledgeAll: () => Promise<void>;
  getAlertsByPriority: (priority: AlertPriority) => Alert[];
  getUnacknowledgedAlerts: () => Alert[];
}

export function useAlerts(): UseAlertsReturn {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [unacknowledgedCount, setUnacknowledgedCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async (filters?: AlertFilters) => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters?.priority) params.set('priority', filters.priority);
      if (filters?.acknowledged !== undefined) {
        params.set('acknowledged', String(filters.acknowledged));
      }
      if (filters?.limit) params.set('limit', String(filters.limit));

      const queryString = params.toString();
      const path = `/api/v1/control-tower/alerts${queryString ? `?${queryString}` : ''}`;

      const response = await apiFetch<{
        alerts: Alert[];
        total: number;
        unacknowledged_count: number;
      }>(path);

      setAlerts(response.alerts);
      setUnacknowledgedCount(response.unacknowledged_count);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error fetching alerts';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      await apiFetch(`/api/v1/control-tower/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        body: JSON.stringify({}),
      });

      setAlerts((prev) =>
        prev.map((a) =>
          a.alert_id === alertId ? { ...a, acknowledged_at: new Date().toISOString() } : a
        )
      );
      setUnacknowledgedCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Error acknowledging alert:', err);
      throw err;
    }
  }, []);

  const acknowledgeAll = useCallback(async () => {
    const unacknowledged = alerts.filter((a) => !a.acknowledged_at);
    await Promise.all(unacknowledged.map((a) => acknowledgeAlert(a.alert_id)));
  }, [alerts, acknowledgeAlert]);

  const getAlertsByPriority = useCallback(
    (priority: AlertPriority) => {
      return alerts.filter((a) => a.priority === priority);
    },
    [alerts]
  );

  const getUnacknowledgedAlerts = useCallback(() => {
    return alerts.filter((a) => !a.acknowledged_at);
  }, [alerts]);

  return {
    alerts,
    unacknowledgedCount,
    isLoading,
    error,
    fetchAlerts,
    acknowledgeAlert,
    acknowledgeAll,
    getAlertsByPriority,
    getUnacknowledgedAlerts,
  };
}
