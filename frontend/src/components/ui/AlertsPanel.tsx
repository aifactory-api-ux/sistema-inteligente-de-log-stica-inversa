import React, { useEffect, useState } from 'react';
import { AlertTriangle, CheckCircle, Clock, TrendingUp, Bell, X } from 'lucide-react';
import { tokens } from '../../styles/tokens';
import { StatusBadge } from './StatusBadge';
import type { Alert, AlertPriority, AlertType } from '../../types/models';

interface AlertsPanelProps {
  alerts: Alert[];
  onAcknowledge: (alertId: string) => void;
  isLoading?: boolean;
}

const priorityIcons: Record<AlertPriority, React.ReactNode> = {
  LOW: <CheckCircle className="w-4 h-4" />,
  MEDIUM: <Bell className="w-4 h-4" />,
  HIGH: <AlertTriangle className="w-4 h-4" />,
  CRITICAL: <AlertTriangle className="w-4 h-4" />,
};

const priorityColors: Record<AlertPriority, string> = {
  LOW: tokens.colors.success,
  MEDIUM: tokens.colors.warning,
  HIGH: tokens.colors.warningLight,
  CRITICAL: tokens.colors.danger,
};

const alertTypeLabels: Record<AlertType, string> = {
  INSPECTION_SATURATION: 'Saturación de Inspección',
  B2B_APPROVAL_PENDING: 'Aprobación KAM Pendiente',
  RETURN_RATE_SPIKE: 'Pico en Tasa de Devoluciones',
  CYCLE_TIME_EXCEEDED: 'Tiempo de Ciclo Excedido',
  COST_THRESHOLD_BREACH: 'Umbral de Coste Superado',
};

export const AlertsPanel: React.FC<AlertsPanelProps> = ({
  alerts,
  onAcknowledge,
  isLoading = false,
}) => {
  const [localAlerts, setLocalAlerts] = useState<Alert[]>(alerts);

  useEffect(() => {
    setLocalAlerts(alerts);
  }, [alerts]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Hace un momento';
    if (diffMins < 60) return `Hace ${diffMins}m`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `Hace ${diffHours}h`;
    const diffDays = Math.floor(diffHours / 24);
    return `Hace ${diffDays}d`;
  };

  const handleAcknowledge = (alertId: string) => {
    setLocalAlerts((prev) =>
      prev.map((a) =>
        a.alert_id === alertId
          ? { ...a, acknowledged_at: new Date().toISOString() }
          : a
      )
    );
    onAcknowledge(alertId);
  };

  const unacknowledgedAlerts = localAlerts.filter((a) => !a.acknowledged_at);
  const acknowledgedAlerts = localAlerts.filter((a) => a.acknowledged_at);

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="w-5 h-5 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900">Alertas</h3>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-16 bg-gray-200 rounded-lg" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell className="w-5 h-5 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900">Alertas</h3>
          {unacknowledgedAlerts.length > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded-full">
              {unacknowledgedAlerts.length}
            </span>
          )}
        </div>
        {unacknowledgedAlerts.length > 0 && (
          <button className="text-xs text-blue-600 hover:text-blue-800">
            Ver todas
          </button>
        )}
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {unacknowledgedAlerts.length === 0 && acknowledgedAlerts.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
            <p className="text-sm">Sin alertas activas</p>
          </div>
        )}

        {unacknowledgedAlerts.map((alert) => (
          <div
            key={alert.alert_id}
            className="p-3 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-3">
              <div
                className="p-1.5 rounded-lg"
                style={{ backgroundColor: `${priorityColors[alert.priority]}15` }}
              >
                <span style={{ color: priorityColors[alert.priority] }}>
                  {priorityIcons[alert.priority]}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-gray-900">
                    {alertTypeLabels[alert.type] || alert.type}
                  </span>
                  <StatusBadge value={alert.priority} size="sm" />
                </div>
                <p className="text-xs text-gray-600 line-clamp-2">{alert.message}</p>
                <div className="flex items-center gap-2 mt-2">
                  <Clock className="w-3 h-3 text-gray-400" />
                  <span className="text-xs text-gray-400">{formatTime(alert.created_at)}</span>
                </div>
              </div>
              <button
                onClick={() => handleAcknowledge(alert.alert_id)}
                className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                title="Reconocer alerta"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}

        {acknowledgedAlerts.length > 0 && (
          <>
            <div className="border-t border-gray-200 pt-3 mt-3">
              <p className="text-xs text-gray-500 mb-2">
                Reconocidas ({acknowledgedAlerts.length})
              </p>
              {acknowledgedAlerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.alert_id}
                  className="p-3 rounded-lg border border-gray-100 bg-gray-50 opacity-60"
                >
                  <div className="flex items-start gap-3">
                    <div className="p-1.5 rounded-lg bg-gray-200">
                      <CheckCircle className="w-4 h-4 text-gray-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-gray-700">
                          {alertTypeLabels[alert.type] || alert.type}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 line-clamp-1">{alert.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AlertsPanel;