import React, { useState, useMemo } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Filter,
  Download,
  Search,
  Package,
  MoreHorizontal,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
} from 'lucide-react';
import { tokens } from '../../styles/tokens';
import { StatusBadge } from './StatusBadge';
import { PrimaryButtonCTA } from './PrimaryButtonCTA';
import { ReturnStatus, ReturnDestination, ReturnChannel } from '../../types/models';
import type { ReturnRequest } from '../../types/models';

interface DataDensityTableProps {
  returns: ReturnRequest[];
  isLoading?: boolean;
  onExport?: () => void;
  onViewDetails?: (returnId: string) => void;
  onApprove?: (returnId: string) => Promise<void>;
  onReject?: (returnId: string, reason: string) => Promise<void>;
}

type SortField = 'created_at' | 'status' | 'destination' | 'total_value' | 'customer_id';
type SortOrder = 'asc' | 'desc';

const statusOptions: ReturnStatus[] = [
  ReturnStatus.PENDIENTE,
  ReturnStatus.PRE_APROBADO,
  ReturnStatus.APROBADO,
  ReturnStatus.EN_TRANSITO,
  ReturnStatus.ENTREGADO,
  ReturnStatus.INSPECCION,
  ReturnStatus.PROCESADO,
  ReturnStatus.EXCEPTION,
  ReturnStatus.RECHAZADO,
];

const destinationOptions: ReturnDestination[] = [
  ReturnDestination.CARRIL_RAPIDO,
  ReturnDestination.OUTLET,
  ReturnDestination.RECICLAJE,
  ReturnDestination.KEEP_IT,
  ReturnDestination.INSPECCION_B2B,
];

const channelOptions: ReturnChannel[] = [ReturnChannel.B2C, ReturnChannel.B2B];

const reasonCodes = [
  'DEFECT',
  'WRONG_ITEM',
  'SIZE_ISSUE',
  'NOT_AS_DESCRIBED',
  'CHANGED_MIND',
  'DAMAGED',
  'OTHER',
];

export const DataDensityTable: React.FC<DataDensityTableProps> = ({
  returns,
  isLoading = false,
  onExport,
  onViewDetails,
  onApprove,
  onReject,
}) => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<ReturnStatus | ''>('');
  const [filterDestination, setFilterDestination] = useState<ReturnDestination | ''>('');
  const [filterChannel, setFilterChannel] = useState<ReturnChannel | ''>('');
  const [filterReason, setFilterReason] = useState<string | ''>('');
  const [showFilters, setShowFilters] = useState(false);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const filteredAndSortedReturns = useMemo(() => {
    let result = [...returns];

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (r) =>
          r.return_id.toLowerCase().includes(term) ||
          r.customer_id.toLowerCase().includes(term) ||
          r.order_reference.toLowerCase().includes(term)
      );
    }

    if (filterStatus) {
      result = result.filter((r) => r.status === filterStatus);
    }

    if (filterDestination) {
      result = result.filter((r) => r.destination === filterDestination);
    }

    if (filterChannel) {
      result = result.filter((r) => r.channel === filterChannel);
    }

    if (filterReason) {
      result = result.filter((r) => r.return_reason === filterReason);
    }

    result.sort((a, b) => {
      let aVal: string | number;
      let bVal: string | number;

      switch (sortField) {
        case 'created_at':
          aVal = new Date(a.created_at).getTime();
          bVal = new Date(b.created_at).getTime();
          break;
        case 'status':
          aVal = a.status;
          bVal = b.status;
          break;
        case 'destination':
          aVal = a.destination || '';
          bVal = b.destination || '';
          break;
        case 'total_value':
          aVal = Number(a.total_value);
          bVal = Number(b.total_value);
          break;
        case 'customer_id':
          aVal = a.customer_id;
          bVal = b.customer_id;
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [returns, searchTerm, filterStatus, filterDestination, filterChannel, filterReason, sortField, sortOrder]);

  const totalPages = Math.ceil(filteredAndSortedReturns.length / pageSize);
  const paginatedReturns = filteredAndSortedReturns.slice(
    (page - 1) * pageSize,
    page * pageSize
  );

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ChevronDown className="w-3 h-3 text-gray-400" />;
    }
    return sortOrder === 'asc' ? (
      <ChevronUp className="w-3 h-3 text-blue-600" />
    ) : (
      <ChevronDown className="w-3 h-3 text-blue-600" />
    );
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilterStatus('');
    setFilterDestination('');
    setFilterChannel('');
    setFilterReason('');
    setPage(1);
  };

  const hasActiveFilters = searchTerm || filterStatus || filterDestination || filterChannel || filterReason;

  const handleApprove = async (returnId: string) => {
    if (!onApprove) return;
    setProcessingId(returnId);
    try {
      await onApprove(returnId);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (returnId: string) => {
    if (!onReject || !rejectReason.trim()) return;
    setProcessingId(returnId);
    try {
      await onReject(returnId, rejectReason);
      setRejectingId(null);
      setRejectReason('');
    } finally {
      setProcessingId(null);
    }
  };

  const exceptionReturns = filteredAndSortedReturns.filter(
    (r) => r.status === 'EXCEPTION' || r.requires_kam_approval
  );

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="animate-pulse space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="p-3 border-b border-gray-200">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Package className="w-4 h-4 text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-900">
              Supervisión de Lotes
            </h3>
            <span className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
              {filteredAndSortedReturns.length}
            </span>
            {exceptionReturns.length > 0 && (
              <span className="px-1.5 py-0.5 text-xs bg-amber-100 text-amber-700 rounded">
                {exceptionReturns.length} excepciones
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-1.5 rounded-lg border transition-colors ${
                showFilters || hasActiveFilters
                  ? 'border-blue-300 bg-blue-50 text-blue-600'
                  : 'border-gray-200 text-gray-500 hover:bg-gray-50'
              }`}
            >
              <Filter className="w-3.5 h-3.5" />
            </button>
            {onExport && (
              <button
                onClick={onExport}
                className="p-1.5 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>

        <div className="mt-2 relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            placeholder="Buscar ID, cliente, pedido..."
            className="w-full pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {showFilters && (
          <div className="mt-2 p-2.5 bg-gray-50 rounded-lg border border-gray-200">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-0.5">
                  Estado
                </label>
                <select
                  value={filterStatus}
                  onChange={(e) => {
                    setFilterStatus(e.target.value as ReturnStatus | '');
                    setPage(1);
                  }}
                  className="w-full px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  {statusOptions.map((s) => (
                    <option key={s} value={s}>
                      {s.replace('_', ' ')}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-0.5">
                  Destino
                </label>
                <select
                  value={filterDestination}
                  onChange={(e) => {
                    setFilterDestination(e.target.value as ReturnDestination | '');
                    setPage(1);
                  }}
                  className="w-full px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  {destinationOptions.map((d) => (
                    <option key={d} value={d}>
                      {d.replace('_', ' ')}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-0.5">
                  Canal
                </label>
                <select
                  value={filterChannel}
                  onChange={(e) => {
                    setFilterChannel(e.target.value as ReturnChannel | '');
                    setPage(1);
                  }}
                  className="w-full px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  {channelOptions.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-0.5">
                  Motivo
                </label>
                <select
                  value={filterReason}
                  onChange={(e) => {
                    setFilterReason(e.target.value);
                    setPage(1);
                  }}
                  className="w-full px-2 py-1 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  {reasonCodes.map((r) => (
                    <option key={r} value={r}>
                      {r.replace('_', ' ')}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-end">
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="w-full px-2 py-1 text-xs text-blue-600 hover:text-blue-800 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    Limpiar
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead style={{ backgroundColor: tokens.colors.gray50 }}>
            <tr>
              <th className="px-2 py-2 text-left">
                <button
                  onClick={() => handleSort('created_at')}
                  className="flex items-center gap-0.5 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-gray-900"
                >
                  Fecha/Hora
                  <SortIcon field="created_at" />
                </button>
              </th>
              <th className="px-2 py-2 text-left">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  ID
                </span>
              </th>
              <th className="px-2 py-2 text-left">
                <button
                  onClick={() => handleSort('customer_id')}
                  className="flex items-center gap-0.5 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-gray-900"
                >
                  Cliente
                  <SortIcon field="customer_id" />
                </button>
              </th>
              <th className="px-2 py-2 text-center">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  Canal
                </span>
              </th>
              <th className="px-2 py-2 text-center">
                <button
                  onClick={() => handleSort('status')}
                  className="flex items-center gap-0.5 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-gray-900 mx-auto"
                >
                  Estado
                  <SortIcon field="status" />
                </button>
              </th>
              <th className="px-2 py-2 text-center">
                <button
                  onClick={() => handleSort('destination')}
                  className="flex items-center gap-0.5 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-gray-900 mx-auto"
                >
                  Destino
                  <SortIcon field="destination" />
                </button>
              </th>
              <th className="px-2 py-2 text-center">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  Uds
                </span>
              </th>
              <th className="px-2 py-2 text-right">
                <button
                  onClick={() => handleSort('total_value')}
                  className="flex items-center gap-0.5 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-gray-900 ml-auto"
                >
                  Valor
                  <SortIcon field="total_value" />
                </button>
              </th>
              <th className="px-2 py-2 text-center">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  Acciones
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            {paginatedReturns.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-2 py-8 text-center text-gray-500">
                  <Package className="w-6 h-6 mx-auto mb-1 text-gray-300" />
                  <p className="text-xs">Sin devoluciones encontradas</p>
                </td>
              </tr>
            ) : (
              paginatedReturns.map((ret) => (
                <React.Fragment key={ret.return_id}>
                  <tr
                    className={`border-t border-gray-100 hover:bg-gray-50 transition-colors ${
                      (ret.status === 'EXCEPTION' || ret.requires_kam_approval)
                        ? 'bg-amber-50 hover:bg-amber-100'
                        : ''
                    }`}
                  >
                    <td className="px-2 py-1.5 text-xs text-gray-500 font-mono">
                      {formatDate(ret.created_at)}
                    </td>
                    <td className="px-2 py-1.5">
                      <span className="font-mono text-xs font-medium text-gray-900">
                        {ret.return_id.substring(0, 8)}...
                      </span>
                    </td>
                    <td className="px-2 py-1.5 text-xs text-gray-700">
                      {ret.customer_id}
                    </td>
                    <td className="px-2 py-1.5 text-center">
                      <StatusBadge value={ret.channel} size="sm" />
                    </td>
                    <td className="px-2 py-1.5 text-center">
                      <StatusBadge value={ret.status} size="sm" />
                    </td>
                    <td className="px-2 py-1.5 text-center">
                      {ret.destination ? (
                        <StatusBadge value={ret.destination} size="sm" />
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-2 py-1.5 text-center text-xs text-gray-700">
                      {ret.total_items}
                    </td>
                    <td className="px-2 py-1.5 text-right font-mono text-xs font-medium text-gray-900">
                      €{Number(ret.total_value).toFixed(0)}
                    </td>
                    <td className="px-2 py-1.5 text-center">
                      <div className="flex items-center justify-center gap-1">
                        {onViewDetails && (
                          <button
                            onClick={() => onViewDetails(ret.return_id)}
                            className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                            title="Ver detalles"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                        )}
                        {(ret.status === 'EXCEPTION' || ret.requires_kam_approval) && onApprove && onReject && (
                          <button
                            onClick={() =>
                              setExpandedRow(expandedRow === ret.return_id ? null : ret.return_id)
                            }
                            className="p-1 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded"
                            title="Acciones KAM"
                          >
                            <MoreHorizontal className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                  {expandedRow === ret.return_id && (
                    <tr className="border-t border-gray-200 bg-gray-50">
                      <td colSpan={9} className="px-2 py-3">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-1">
                              Información del pedido
                            </p>
                            <div className="space-y-0.5 text-xs text-gray-700">
                              <p>
                                <span className="text-gray-500">Pedido:</span> {ret.order_reference}
                              </p>
                              <p>
                                <span className="text-gray-500">Factura:</span>{' '}
                                {ret.invoice_reference || '—'}
                              </p>
                              <p>
                                <span className="text-gray-500">Motivo:</span>{' '}
                                {ret.return_reason_description || ret.return_reason}
                              </p>
                              <p>
                                <span className="text-gray-500">Método:</span>{' '}
                                {ret.return_method || '—'}
                              </p>
                            </div>
                          </div>
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-1">Artículos</p>
                            <div className="max-h-20 overflow-y-auto space-y-0.5">
                              {ret.items.slice(0, 5).map((item, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-center justify-between text-xs"
                                >
                                  <span className="text-gray-700 truncate">
                                    {item.quantity}x {item.product_name}
                                  </span>
                                  <span className="text-gray-500 ml-2">
                                    €{item.unit_price.toFixed(2)}
                                  </span>
                                </div>
                              ))}
                              {ret.items.length > 5 && (
                                <p className="text-xs text-gray-400">
                                  +{ret.items.length - 5} más
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                        {(ret.status === 'EXCEPTION' || ret.requires_kam_approval) && (
                          <div className="flex items-center justify-end gap-2 mt-3 pt-2 border-t border-gray-200">
                            {rejectingId === ret.return_id ? (
                              <div className="flex items-center gap-2">
                                <input
                                  type="text"
                                  value={rejectReason}
                                  onChange={(e) => setRejectReason(e.target.value)}
                                  placeholder="Motivo del rechazo..."
                                  className="px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                                />
                                <PrimaryButtonCTA
                                  variant="danger"
                                  size="sm"
                                  onClick={() => handleReject(ret.return_id)}
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
                                  onClick={() => setRejectingId(ret.return_id)}
                                >
                                  <XCircle className="w-3.5 h-3.5 mr-1" />
                                  Rechazar
                                </PrimaryButtonCTA>
                                <PrimaryButtonCTA
                                  variant="solid"
                                  size="sm"
                                  onClick={() => handleApprove(ret.return_id)}
                                  loading={processingId === ret.return_id}
                                >
                                  <CheckCircle className="w-3.5 h-3.5 mr-1" />
                                  Aprobar
                                </PrimaryButtonCTA>
                              </>
                            )}
                          </div>
                        )}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="px-3 py-2 border-t border-gray-200 flex items-center justify-between">
          <div className="text-xs text-gray-500">
            {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, filteredAndSortedReturns.length)} de{' '}
            {filteredAndSortedReturns.length}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-2 py-1 text-xs font-medium text-gray-600 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Ant.
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = i + 1;
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`px-2 py-1 text-xs font-medium rounded ${
                    page === pageNum
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 border border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-2 py-1 text-xs font-medium text-gray-600 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Sig.
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataDensityTable;
