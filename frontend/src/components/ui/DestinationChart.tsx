import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts';
import { tokens, semanticTokens } from '../../styles/tokens';
import type { DestinationDistribution } from '../../types/models';

interface DestinationChartProps {
  distribution: DestinationDistribution | null;
  isLoading?: boolean;
}

const DESTINATION_LABELS: Record<keyof Omit<DestinationDistribution, 'total'>, string> = {
  CARRIL_RAPIDO: 'Carril Rápido',
  OUTLET: 'Outlet',
  RECICLAJE: 'Reciclaje',
  KEEP_IT: 'Keep-it',
  INSPECCION_B2B: 'Inspección B2B',
};

const DESTINATION_COLORS: Record<keyof Omit<DestinationDistribution, 'total'>, string> = {
  CARRIL_RAPIDO: semanticTokens.destinationCarrilRapido,
  OUTLET: semanticTokens.destinationOutlet,
  RECICLAJE: semanticTokens.destinationReciclaje,
  KEEP_IT: semanticTokens.destinationKeepIt,
  INSPECCION_B2B: semanticTokens.destinationInspeccion,
};

interface ChartDataItem {
  name: string;
  value: number;
  color: string;
  percentage: number;
}

export const DestinationChart: React.FC<DestinationChartProps> = ({
  distribution,
  isLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">
          Distribución de Destinos
        </h3>
        <div className="h-64 animate-pulse bg-gray-100 rounded-lg" />
      </div>
    );
  }

  if (!distribution) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">
          Distribución de Destinos
        </h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          <p className="text-sm">Sin datos disponibles</p>
        </div>
      </div>
    );
  }

  const chartData: ChartDataItem[] = (
    ['CARRIL_RAPIDO', 'OUTLET', 'RECICLAJE', 'KEEP_IT', 'INSPECCION_B2B'] as const
  )
    .map((key) => {
      const value = distribution[key] as number;
      return {
        name: DESTINATION_LABELS[key],
        value,
        color: DESTINATION_COLORS[key],
        percentage: distribution.total > 0 ? (value / distribution.total) * 100 : 0,
      };
    })
    .filter((item) => item.value > 0);

  const total = distribution.total || 1;

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: ChartDataItem }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white px-3 py-2 rounded-lg border border-gray-200 shadow-lg">
          <p className="text-xs font-medium text-gray-900">{data.name}</p>
          <p className="text-xs text-gray-600">
            <span className="font-semibold">{data.value}</span> devoluciones (
            {data.percentage.toFixed(1)}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">
          Distribución de Destinos
        </h3>
        <span className="text-xs text-gray-500">{total} total</span>
      </div>

      {chartData.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-gray-500">
          <p className="text-sm">Sin datos de distribución</p>
        </div>
      ) : (
        <>
          <div className="h-48 mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 0, right: 0, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
                <XAxis
                  type="number"
                  tick={{ fontSize: 11, fill: '#6B7280' }}
                  axisLine={{ stroke: '#E5E7EB' }}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 11, fill: '#6B7280' }}
                  axisLine={false}
                  tickLine={false}
                  width={90}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.05)' }} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={32}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {chartData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-sm flex-shrink-0"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-gray-600 truncate">{item.name}</span>
                <span className="text-xs font-medium text-gray-900 ml-auto">
                  {item.percentage.toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default DestinationChart;