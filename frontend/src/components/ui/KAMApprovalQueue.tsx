import React, { useState } from 'react';
import { CheckCircle, XCircle, Clock, User, Package } from 'lucide-react';
import { tokens } from '../../styles/tokens';
import { StatusBadge } from './StatusBadge';
import { PrimaryButtonCTA } from './PrimaryButtonCTA';
import type { ReturnRequest } from '../../types/models';

interface KAMApprovalQueueProps {
  returns: ReturnRequest[];
  onApprove: (returnId: string) => Promise<void>;
  onReject: (returnId: string, reason: string) => Promise<void>;
  isLoading?: boolean;
}

export const KAMApprovalQueue: React.FC<KAMApprovalQueueProps> = ({
  returns,
  onApprove,
  onReject,
  isLoading = false,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [processingId, setProcessingId] = useState<string | null>(null);

  const pendingReturns = returns.filter(
    (r) => r.status === 'EXCEPTION' || r.requires_kam_approval
  );

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleApprove = async (returnId: string) => {
    setProcessingId(returnId);
    try {
      await onApprove(returnId);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (returnId: string) => {
    if (!rejectReason.trim()) return;
    setProcessingId(returnId);
    try {
      await onReject(returnId, rejectReason);
      setRejectingId(null);
      setRejectReason('');
    } finally {
      setProcessingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900">Pendientes KAM</h3>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-20 bg-gray-200 rounded-lg" />
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
          <Clock className="w-5 h-5 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900">Pendientes KAM</h3>
          {pendingReturns.length > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-700 rounded-full">
              {pendingReturns.length}
            </span>
          )}
        </div>
        {pendingReturns.length > 0 && (
          <button className="text-xs text-blue-600 hover:text-blue-800">
            Ver todas
          </button>
        )}
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {pendingReturns.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
            <p className="text-sm">Sin solicitudes pendientes</p>
          </div>
        )}

        {pendingReturns.map((ret) => (
          <div
            key={ret.return_id}
            className="border border-gray-200 rounded-lg overflow-hidden"
          >
            <div
              className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() =>
                setExpandedId(expandedId === ret.return_id ? null : ret.return_id)
              }
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm font-medium text-gray-900">
                      {ret.return_id}
                    </span>
                    <StatusBadge value={ret.channel} size="sm" />
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <User className="w-3 h-3" />
                    <span>{ret.customer_id}</span>
                    <span>•</span>
                    <Package className="w-3 h-3" />
                    <span>{ret.total_items} artículos</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                    <Clock className="w-3 h-3" />
                    <span>{formatDate(ret.created_at)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-900">
                    €{Number(ret.estimated_refund || 0).toFixed(2)}
                  </span>
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${
                      expandedId === ret.return_id ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </div>

              {ret.destination && (
                <div className="mt-2">
                  <StatusBadge value={ret.destination} size="sm" />
                </div>
              )}
            </div>

            {expandedId === ret.return_id && (
              <div className="border-t border-gray-200 p-4 bg-gray-50">
                <div className="space-y-3">
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">Artículos</p>
                    <div className="space-y-1">
                      {ret.items.slice(0, 3).map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between text-xs"
                        >
                          <span className="text-gray-700">
                            {item.quantity}x {item.product_name}
                          </span>
                          <span className="text-gray-500">€{item.unit_price.toFixed(2)}</span>
                        </div>
                      ))}
                      {ret.items.length > 3 && (
                        <p className="text-xs text-gray-400">
                          +{ret.items.length - 3} más
                        </p>
                      )}
                    </div>
                  </div>

                  {ret.return_reason_description && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 mb-1">Motivo</p>
                      <p className="text-xs text-gray-700">{ret.return_reason_description}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-3 border-t border-gray-200">
                    <div className="text-xs text-gray-500">
                      <span className="font-medium">Total:</span>{' '}
                      <span className="font-semibold text-gray-900">
                        €{Number(ret.total_value).toFixed(2)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      {rejectingId === ret.return_id ? (
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                            placeholder="Motivo del rechazo..."
                            className="px-2 py-1 text-xs border border-gray-300 rounded"
                            onClick={(e) => e.stopPropagation()}
                          />
                          <PrimaryButtonCTA
                            variant="danger"
                            size="sm"
                            onClick={() => {
                              handleReject(ret.return_id);
                            }}
                            disabled={processingId === ret.return_id || !rejectReason.trim()}
                          >
                            Rechazar
                          </PrimaryButtonCTA>
                          <PrimaryButtonCTA
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setRejectingId(null);
                              setRejectReason('');
                            }}
                          >
                            Cancelar
                          </PrimaryButtonCTA>
                        </div>
                      ) : (
                        <>
                          <PrimaryButtonCTA
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setRejectingId(ret.return_id);
                            }}
                          >
                            <XCircle className="w-4 h-4 mr-1" />
                            Rechazar
                          </PrimaryButtonCTA>
                          <PrimaryButtonCTA
                            variant="solid"
                            size="sm"
                            onClick={() => {
                              handleApprove(ret.return_id);
                            }}
                            loading={processingId === ret.return_id}
                          >
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Aprobar
                          </PrimaryButtonCTA>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default KAMApprovalQueue;