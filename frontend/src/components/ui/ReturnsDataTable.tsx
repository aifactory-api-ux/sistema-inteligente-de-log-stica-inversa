import React, { useState, useMemo } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Filter,
  Download,
  Search,
  Package,
} from 'lucide-react';
import { tokens } from '../../styles/tokens';
import { StatusBadge } from './StatusBadge';
import { ReturnStatus, ReturnDestination, ReturnChannel } from '../../types/models';
import type { ReturnRequest } from '../../types/models';

interface ReturnsDataTableProps {
  returns: ReturnRequest[];
  isLoading?: boolean;
  onExport?: () => void;
}

type SortField = 'created_at' | 'status' | 'destination' | 'total_value';
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

export const ReturnsDataTable: React.FC<ReturnsDataTableProps> = ({
  returns,
  isLoading = false,
  onExport,
}) => {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<ReturnStatus | ''>('');
  const [filterDestination, setFilterDestination] = useState<ReturnDestination | ''>('');
  const [filterChannel, setFilterChannel] = useState<ReturnChannel | ''>('');
  const [showFilters, setShowFilters] = useState(false);

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
        default:
          return 0;
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [returns, searchTerm, filterStatus, filterDestination, filterChannel, sortField, sortOrder]);

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
      return <ChevronDown className="w-4 h-4 text-gray-400" />;
    }
    return sortOrder === 'asc' ? (
      <ChevronUp className="w-4 h-4 text-blue-600" />
    ) : (
      <ChevronDown className="w-4 h-4 text-blue-600" />
    );
  };

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

  const clearFilters = () => {
    setSearchTerm('');
    setFilterStatus('');
    setFilterDestination('');
    setFilterChannel('');
    setPage(1);
  };

  const hasActiveFilters = searchTerm || filterStatus || filterDestination || filterChannel;

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Package className="w-5 h-5 text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-900">Returns</h3>
          </div>
        </div>
        <div className="animate-pulse space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Package className="w-5 h-5 text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-900">
              Detalle de Devoluciones
            </h3>
            <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded-full">
              {filteredAndSortedReturns.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 rounded-lg border transition-colors ${
                showFilters || hasActiveFilters
                  ? 'border-blue-300 bg-blue-50 text-blue-600'
                  : 'border-gray-200 text-gray-500 hover:bg-gray-50'
              }`}
            >
              <Filter className="w-4 h-4" />
            </button>
            {onExport && (
              <button
                onClick={onExport}
                className="p-2 rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        <div className="mt-3 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            placeholder="Buscar por ID, cliente o pedido..."
            className="w-full pl-10 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {showFilters && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Estado
                </label>
                <select
                  value={filterStatus}
                  onChange={(e) => {
                    setFilterStatus(e.target.value as ReturnStatus | '');
                    setPage(1);
                  }}
                  className="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Destino
                </label>
                <select
                  value={filterDestination}
                  onChange={(e) => {
                    setFilterDestination(e.target.value as ReturnDestination | '');
                    setPage(1);
                  }}
                  className="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Canal
                </label>
                <select
                  value={filterChannel}
                  onChange={(e) => {
                    setFilterChannel(e.target.value as ReturnChannel | '');
                    setPage(1);
                  }}
                  className="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Todos</option>
                  {channelOptions.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            {hasActiveFilters && (
              <div className="mt-2 flex justify-end">
                <button
                  onClick={clearFilters}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Limpiar filtros
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead style={{ backgroundColor: tokens.colors.gray50 }}>
            <tr>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('created_at')}
                  className="flex items-center gap-1 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-gray-900"
                >
                  Fecha
                  <SortIcon field="created_at" />
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  ID Devolución
                </span>
              </th>
              <th className="px-4 py-3 text-left">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  Cliente
                </span>
              </th>
              <th className="px-4 py-3 text-center">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  Canal
                </span>
              </th>
              <th className="px-4 py-3 text-center">
                <button
                  onClick={() => handleSort('status')}
                  className="flex items-center gap-1 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-gray-900 mx-auto"
                >
                  Estado
                  <SortIcon field="status" />
                </button>
              </th>
              <th className="px-4 py-3 text-center">
                <button
                  onClick={() => handleSort('destination')}
                  className="flex items-center gap-1 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-gray-900 mx-auto"
                >
                  Destino
                  <SortIcon field="destination" />
                </button>
              </th>
              <th className="px-4 py-3 text-center">
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  Artículos
                </span>
              </th>
              <th className="px-4 py-3 text-right">
                <button
                  onClick={() => handleSort('total_value')}
                  className="flex items-center gap-1 text-xs font-semibold text-gray-600 uppercase tracking-wide hover:text-gray-900 ml-auto"
                >
                  Valor
                  <SortIcon field="total_value" />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {paginatedReturns.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-gray-500">
                  <Package className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">No se encontraron devoluciones</p>
                </td>
              </tr>
            ) : (
              paginatedReturns.map((ret) => (
                <tr
                  key={ret.return_id}
                  className="border-t border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {formatDate(ret.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs font-medium text-gray-900">
                      {ret.return_id}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-700">
                    {ret.customer_id}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge value={ret.channel} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusBadge value={ret.status} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-center">
                    {ret.destination ? (
                      <StatusBadge value={ret.destination} size="sm" />
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center text-xs text-gray-700">
                    {ret.total_items}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs font-medium text-gray-900">
                    €{Number(ret.total_value).toFixed(2)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
          <div className="text-xs text-gray-500">
            Mostrando {(page - 1) * pageSize + 1} -{' '}
            {Math.min(page * pageSize, filteredAndSortedReturns.length)} de{' '}
            {filteredAndSortedReturns.length}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 text-xs font-medium text-gray-600 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = i + 1;
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`px-3 py-1 text-xs font-medium rounded ${
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
              className="px-3 py-1 text-xs font-medium text-gray-600 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReturnsDataTable;