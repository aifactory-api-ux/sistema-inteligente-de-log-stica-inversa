import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { tokens } from '../../styles/tokens';

interface KPIStatCardProps {
  title: string;
  value: string | number;
  delta?: number;
  unit?: string;
  sparklineData?: number[];
  trend?: 'up' | 'down' | 'neutral';
  inverseTrend?: boolean;
  loading?: boolean;
}

export const KPIStatCard: React.FC<KPIStatCardProps> = ({
  title,
  value,
  delta,
  unit = '',
  sparklineData,
  trend,
  inverseTrend = false,
  loading = false,
}) => {
  const getTrendIcon = () => {
    if (delta === undefined || delta === 0) {
      return <Minus className="w-3 h-3" />;
    }
    return delta > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />;
  };

  const getTrendColor = () => {
    if (delta === undefined || delta === 0) return tokens.colors.gray500;

    const isPositive = inverseTrend ? delta < 0 : delta > 0;
    return isPositive ? tokens.colors.success : tokens.colors.danger;
  };

  const formatDelta = () => {
    if (delta === undefined) return '';
    const sign = delta > 0 ? '+' : '';
    return `${sign}${delta.toFixed(1)}${unit === '%' ? 'pp' : unit}`;
  };

  const renderSparkline = () => {
    if (!sparklineData || sparklineData.length === 0) return null;

    const width = 80;
    const height = 24;
    const max = Math.max(...sparklineData);
    const min = Math.min(...sparklineData);
    const range = max - min || 1;

    const points = sparklineData
      .map((val, i) => {
        const x = (i / (sparklineData.length - 1)) * width;
        const y = height - ((val - min) / range) * height;
        return `${x},${y}`;
      })
      .join(' ');

    return (
      <svg width={width} height={height} className="overflow-visible">
        <polyline
          points={points}
          fill="none"
          stroke={getTrendColor()}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
        <div className="h-3 bg-gray-200 rounded w-24 mb-3" />
        <div className="h-8 bg-gray-200 rounded w-32 mb-2" />
        <div className="h-3 bg-gray-200 rounded w-20" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{title}</p>
        {sparklineData && <div className="flex-shrink-0">{renderSparkline()}</div>}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-gray-900 font-mono">{value}</span>
        {unit && <span className="text-sm text-gray-500">{unit}</span>}
      </div>

      {delta !== undefined && (
        <div className="flex items-center gap-1 mt-2">
          <span style={{ color: getTrendColor() }} className="flex items-center gap-0.5">
            {getTrendIcon()}
            <span className="text-xs font-medium">{formatDelta()}</span>
          </span>
          <span className="text-xs text-gray-400">vs anterior</span>
        </div>
      )}
    </div>
  );
};

export default KPIStatCard;
