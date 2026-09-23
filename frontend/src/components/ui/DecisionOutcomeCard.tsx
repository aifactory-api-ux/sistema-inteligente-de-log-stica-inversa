import React from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { CheckCircle, Truck, Recycle, Store, AlertTriangle, Clock, Shield } from 'lucide-react';
import { tokens, semanticTokens } from '../../styles/tokens';
import type { DecisionResult, ReturnRequest } from '../../types/models';
import { StatusBadge } from './StatusBadge';
import { PrimaryButtonCTA } from './PrimaryButtonCTA';

interface DecisionOutcomeCardProps {
  decision: DecisionResult | null;
  returnRequest?: ReturnRequest | null;
  onDownloadQR?: () => void;
  onSchedulePickup?: () => void;
  showActions?: boolean;
}

const destinationConfig: Record<string, { icon: React.ReactNode; color: string; bgColor: string; label: string }> = {
  CARRIL_RAPIDO: {
    icon: <Store className="w-5 h-5" />,
    color: '#2563EB',
    bgColor: '#DBEAFE',
    label: 'Carril Rápido',
  },
  OUTLET: {
    icon: <Store className="w-5 h-5" />,
    color: '#7C3AED',
    bgColor: '#EDE9FE',
    label: 'Outlet',
  },
  RECICLAJE: {
    icon: <Recycle className="w-5 h-5" />,
    color: '#059669',
    bgColor: '#D1FAE5',
    label: 'Reciclaje Textil',
  },
  KEEP_IT: {
    icon: <CheckCircle className="w-5 h-5" />,
    color: '#0D9488',
    bgColor: '#CCFBF1',
    label: 'Keep It',
  },
  INSPECCION_B2B: {
    icon: <AlertTriangle className="w-5 h-5" />,
    color: '#D97706',
    bgColor: '#FED7AA',
    label: 'Inspección B2B',
  },
};

const methodConfig: Record<string, { icon: React.ReactNode; label: string }> = {
  DROP_OFF: { icon: <QRCodeSVG value="DROP_OFF" size={20} />, label: 'Código QR para Drop-off' },
  PICKUP: { icon: <Truck className="w-5 h-5" />, label: 'Recogida Programada' },
  KEEP_IT: { icon: <CheckCircle className="w-5 h-5" />, label: 'Sin Retorno Físico' },
};

export const DecisionOutcomeCard: React.FC<DecisionOutcomeCardProps> = ({
  decision,
  returnRequest,
  onDownloadQR,
  onSchedulePickup,
  showActions = true,
}) => {
  if (!decision && !returnRequest) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <p className="text-gray-500 text-sm text-center">
          Inicia el proceso de devolución para ver el resultado
        </p>
      </div>
    );
  }

  const destination = decision?.destination || returnRequest?.destination;
  const method = decision?.return_method || returnRequest?.return_method;
  const destinationInfo = destination ? destinationConfig[destination] : null;
  const methodInfo = method ? methodConfig[method] : null;

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div
        className="px-6 py-4 border-b border-gray-200"
        style={{ backgroundColor: destinationInfo?.bgColor || '#F3F4F6' }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="p-2 rounded-lg"
              style={{ backgroundColor: destinationInfo?.color || '#6B7280', color: 'white' }}
            >
              {destinationInfo?.icon}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">
                {destinationInfo?.label || 'Destino Asignado'}
              </h3>
              <p className="text-xs text-gray-600 mt-0.5">
                {decision?.business_rule_applied || 'Regla de negocio aplicada'}
              </p>
            </div>
          </div>
          {destination && <StatusBadge variant="destination" value={destination} />}
        </div>
      </div>

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Método de Retorno</p>
            <div className="flex items-center gap-2">
              <span style={{ color: methodInfo ? destinationInfo?.color : '#6B7280' }}>
                {methodInfo?.icon}
              </span>
              <span className="text-sm font-medium text-gray-900">{methodInfo?.label}</span>
            </div>
          </div>

          <div className="space-y-1">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Puntuación</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className="h-2 rounded-full"
                  style={{
                    width: `${decision?.score || returnRequest?.decision_score || 0}%`,
                    backgroundColor: destinationInfo?.color || '#6B7280',
                  }}
                />
              </div>
              <span className="text-sm font-semibold text-gray-900">
                {decision?.score || returnRequest?.decision_score || 0}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <Shield className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-gray-600">
              {decision?.explanation || returnRequest?.decision_explanation || ''}
            </p>
          </div>
        </div>

        {returnRequest?.estimated_refund !== undefined && returnRequest.estimated_refund !== null && (
          <div className="flex justify-between items-center py-3 border-t border-gray-200">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-600">Reembolso estimado</span>
            </div>
            <span className="text-lg font-bold text-gray-900">
              €{Number(returnRequest.estimated_refund).toFixed(2)}
            </span>
          </div>
        )}

        {decision?.requires_kam_approval || returnRequest?.requires_kam_approval ? (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800">Pendiente de Aprobación KAM</p>
                <p className="text-xs text-amber-600 mt-1">
                  Este lote requiere autorización del Key Account Manager antes de proceder.
                </p>
              </div>
            </div>
          </div>
        ) : null}

        {method === 'DROP_OFF' && returnRequest?.drop_off_qr_code && showActions && (
          <div className="border-t border-gray-200 pt-4">
            <p className="text-xs text-gray-500 mb-3">Código QR para Drop-off</p>
            <div className="flex items-center gap-4">
              <div className="bg-white p-2 rounded-lg border border-gray-200">
                <QRCodeSVG
                  value={`RET:${returnRequest.return_id}:${returnRequest.trace_id}`}
                  size={100}
                  level="M"
                />
              </div>
              <div className="flex-1">
                <p className="text-xs text-gray-500 mb-1">ID de Solicitud</p>
                <p className="text-sm font-mono font-medium text-gray-900">{returnRequest.return_id}</p>
                <p className="text-xs text-gray-500 mt-2 mb-1">Instrucciones</p>
                <p className="text-xs text-gray-600">
                  Presenta este código QR en el punto de drop-off seleccionado.
                </p>
              </div>
            </div>
            {onDownloadQR && (
              <div className="mt-4">
                <PrimaryButtonCTA onClick={onDownloadQR} variant="outline" size="sm">
                  Descargar Etiqueta
                </PrimaryButtonCTA>
              </div>
            )}
          </div>
        )}

        {method === 'PICKUP' && showActions && (
          <div className="border-t border-gray-200 pt-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Truck className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-blue-800">Recogida Programada</p>
                  <p className="text-xs text-blue-600 mt-1">
                    Un transportista recogerá el pedido en la dirección indicada.
                  </p>
                </div>
              </div>
            </div>
            {onSchedulePickup && (
              <div className="mt-4">
                <PrimaryButtonCTA onClick={onSchedulePickup} variant="solid" size="sm">
                  Programar Recogida
                </PrimaryButtonCTA>
              </div>
            )}
          </div>
        )}

        {method === 'KEEP_IT' && (
          <div className="border-t border-gray-200 pt-4">
            <div className="bg-teal-50 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-teal-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-teal-800">Reembolso Inmediato</p>
                  <p className="text-xs text-teal-600 mt-1">
                    No se requiere retorno físico. El reembolso se procesará automáticamente.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="text-xs text-gray-400 text-center pt-2">
          Procesado en {decision?.processing_time_ms || returnRequest?.processing_time_ms || 0}ms
        </div>
      </div>
    </div>
  );
};

export default DecisionOutcomeCard;
