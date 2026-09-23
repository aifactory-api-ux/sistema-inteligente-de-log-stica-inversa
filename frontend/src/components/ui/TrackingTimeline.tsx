import React from 'react';
import { Clock, RefreshCw, CheckCircle, Truck, PackageCheck, Warehouse, Package } from 'lucide-react';
import { tokens } from '../../styles/tokens';
import { StatusBadge } from './StatusBadge';
import type { TrackingTimeline as TrackingTimelineType, ReturnStatus } from '../../types/models';

interface TrackingTimelineProps {
  tracking: TrackingTimelineType | null;
}

const getStatusIcon = (status: string): React.ReactNode => {
  switch (status) {
    case 'APROBADO':
    case 'APPROVED':
      return <CheckCircle className="w-4 h-4 text-emerald-500" />;
    case 'EN_TRANSITO':
    case 'IN_TRANSIT':
      return <Truck className="w-4 h-4 text-blue-500" />;
    case 'ENTREGADO':
    case 'DELIVERED':
      return <PackageCheck className="w-4 h-4 text-emerald-500" />;
    case 'INSPECCION':
    case 'INSPECTION':
      return <Warehouse className="w-4 h-4 text-amber-500" />;
    case 'PROCESADO':
    case 'PROCESSED':
      return <Package className="w-4 h-4 text-emerald-500" />;
    case 'PENDIENTE':
    case 'PENDING':
      return <Clock className="w-4 h-4 text-amber-500" />;
    default:
      return <RefreshCw className="w-4 h-4 text-gray-400" />;
  }
};

const formatDateTime = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleString('es-ES', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const TrackingTimeline: React.FC<TrackingTimelineProps> = ({ tracking }) => {
  if (!tracking) return null;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900">Seguimiento de Devolución</h3>
        </div>
        {tracking.estimated_delivery && (
          <div className="text-sm text-gray-500">
            <Clock className="w-4 h-4 inline mr-1" />
            Entrega estimada: {new Date(tracking.estimated_delivery).toLocaleDateString('es-ES', {
              day: '2-digit',
              month: 'short',
              year: 'numeric',
            })}
          </div>
        )}
      </div>

      <div className="relative">
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

        <div className="space-y-6">
          {tracking.events.map((event, index) => (
            <div key={event.event_id} className="relative flex items-start gap-4">
              <div className="relative z-10 flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-white border-2 border-gray-200 flex items-center justify-center">
                  {getStatusIcon(event.status)}
                </div>
              </div>

              <div className="flex-1 min-w-0 pt-1">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{event.description}</p>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {event.location && `${event.location} · `}
                      {formatDateTime(event.timestamp)}
                    </p>
                  </div>
                  <StatusBadge value={event.status} variant="status" size="sm" />
                </div>
                <p className="text-xs text-gray-400 mt-1">Por: {event.actor}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TrackingTimeline;