import { useCallback, useState } from 'react';
import { apiFetch } from '../lib/api';
import type { KPIMetrics, DestinationDistribution } from '../types/models';

interface UseKPIsReturn {
  kpis: KPIMetrics | null;
  distribution: DestinationDistribution | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;
  refreshKPIs: () => Promise<void>;
  refreshDistribution: () => Promise<void>;
  refreshAll: () => Promise<void>;
}

export function useKPIs(): UseKPIsReturn {
  const [kpis, setKpis] = useState<KPIMetrics | null>(null);
  const [distribution, setDistribution] = useState<DestinationDistribution | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const refreshKPIs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiFetch<KPIMetrics>('/api/v1/control-tower/kpis');
      setKpis(data);
      setLastUpdated(new Date().toISOString());
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error fetching KPIs';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshDistribution = useCallback(async () => {
    try {
      const data = await apiFetch<DestinationDistribution>('/api/v1/control-tower/distribution');
      setDistribution(data);
    } catch (err) {
      console.error('Error fetching distribution:', err);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    await Promise.all([refreshKPIs(), refreshDistribution()]);
  }, [refreshKPIs, refreshDistribution]);

  return {
    kpis,
    distribution,
    isLoading,
    error,
    lastUpdated,
    refreshKPIs,
    refreshDistribution,
    refreshAll,
  };
}
