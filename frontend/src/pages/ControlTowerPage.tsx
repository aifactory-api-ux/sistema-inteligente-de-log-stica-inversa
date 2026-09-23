import React, { useEffect, useCallback } from 'react';
import { RefreshCw, Clock } from 'lucide-react';
import { tokens } from '../styles/tokens';
import { KPIStatCard } from '../components/ui/KPIStatCard';
import { DestinationChart } from '../components/ui/DestinationChart';
import { AlertsPanel } from '../components/ui/AlertsPanel';
import { KAMApprovalQueue } from '../components/ui/KAMApprovalQueue';
import { ReturnsDataTable } from '../components/ui/ReturnsDataTable';
import { useControlTowerStore } from '../stores/controlTowerStore';
import { useReturnsStore } from '../stores/returnsStore';
import { kamApi } from '../services/api';
import type { ReturnRequest, Alert } from '../types/models';

export const ControlTowerPage: React.FC = () => {
  const {
    kpis,
    distribution,
    alerts,
    unreadAlertCount,
    isLoading: kpiLoading,
    lastUpdated,
    fetchKPIs,
    fetchDistribution,
    fetchAlerts,
    acknowledgeAlert,
    subscribeToRealtime,
  } = useControlTowerStore();

  const {
    returns,
    isLoading: returnsLoading,
    fetchReturns,
  } = useReturnsStore();

  const [kamPending, setKamPending] = React.useState<ReturnRequest[]>([]);
  const [loadingKam, setLoadingKam] = React.useState(false);

  const loadData = useCallback(async () => {
    await Promise.all([
      fetchKPIs(),
      fetchDistribution(),
      fetchAlerts({ limit: 20 }),
    ]);
    fetchReturns({ page: 1, page_size: 100 });
  }, [fetchKPIs, fetchDistribution, fetchAlerts, fetchReturns]);

  const loadKamPending = useCallback(async () => {
    setLoadingKam(true);
    try {
      const pending = await kamApi.getPending();
      setKamPending(pending);
    } catch (error) {
      console.error('Error loading KAM pending:', error);
    } finally {
      setLoadingKam(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    loadKamPending();

    const unsubscribe = subscribeToRealtime();
    return () => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, [loadData, loadKamPending, subscribeToRealtime]);

  const handleAcknowledgeAlert = async (alertId: string) => {
    await acknowledgeAlert(alertId);
  };

  const handleApproveReturn = async (returnId: string) => {
    try {
      await kamApi.approve(returnId);
      await loadKamPending();
      await loadData();
    } catch (error) {
      console.error('Error approving return:', error);
    }
  };

  const handleRejectReturn = async (returnId: string, reason: string) => {
    try {
      await kamApi.reject(returnId, reason);
      await loadKamPending();
      await loadData();
    } catch (error) {
      console.error('Error rejecting return:', error);
    }
  };

  const formatLastUpdated = () => {
    if (!lastUpdated) return 'Nunca';
    const date = new Date(lastUpdated);
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const kpiCards = kpis
    ? [
        {
          title: 'Tasa de Devolución',
          value: `${kpis.return_rate.toFixed(1)}%`,
          delta: kpis.return_rate_delta,
          unit: '%',
          sparklineData: kpis.return_rate_history,
          inverseTrend: true,
        },
        {
          title: 'Tiempo de Ciclo',
          value: `${kpis.cycle_time_hours.toFixed(1)}h`,
          delta: kpis.cycle_time_delta,
          unit: 'h',
          sparklineData: kpis.cycle_time_history,
          inverseTrend: true,
        },
        {
          title: 'Coste Medio Recuperación',
          value: `€${kpis.avg_recovery_cost.toFixed(2)}`,
          delta: kpis.recovery_cost_delta,
          unit: '€',
          sparklineData: kpis.recovery_cost_history,
          inverseTrend: true,
        },
        {
          title: 'Tasa Recuperación Valor',
          value: `${kpis.value_recovery_rate.toFixed(1)}%`,
          delta: kpis.recovery_rate_delta,
          unit: '%',
          sparklineData: kpis.recovery_rate_history,
          inverseTrend: false,
        },
        {
          title: 'Devoluciones Hoy',
          value: kpis.total_returns_today.toString(),
          delta: undefined,
          sparklineData: undefined,
          inverseTrend: true,
        },
      ]
    : [];

  return (
    <div className="min-h-screen" style={{ backgroundColor: tokens.colors.pageBackgroundDark }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Torre de Control de Retornos
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Supervisión logística y gestión de excepciones
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Clock className="w-4 h-4" />
              <span>Actualizado: {formatLastUpdated()}</span>
            </div>
            <button
              onClick={loadData}
              className="p-2 rounded-lg border border-gray-200 bg-white text-gray-500 hover:bg-gray-50 transition-colors"
              title="Actualizar datos"
            >
              <RefreshCw className={`w-4 h-4 ${kpiLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          {kpiCards.map((kpi, index) => (
            <KPIStatCard
              key={index}
              title={kpi.title}
              value={kpi.value}
              delta={kpi.delta}
              unit={kpi.unit}
              sparklineData={kpi.sparklineData}
              trend={kpi.delta && kpi.delta > 0 ? 'up' : kpi.delta && kpi.delta < 0 ? 'down' : 'neutral'}
              inverseTrend={kpi.inverseTrend}
              loading={kpiLoading}
            />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2">
            <DestinationChart
              distribution={distribution}
              isLoading={kpiLoading}
            />
          </div>
          <div className="space-y-6">
            <AlertsPanel
              alerts={alerts}
              onAcknowledge={handleAcknowledgeAlert}
              isLoading={kpiLoading}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2">
            <ReturnsDataTable
              returns={returns}
              isLoading={returnsLoading}
            />
          </div>
          <div>
            <KAMApprovalQueue
              returns={kamPending}
              onApprove={handleApproveReturn}
              onReject={handleRejectReturn}
              isLoading={loadingKam}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ControlTowerPage;