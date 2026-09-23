import React from 'react';
import { tokens, semanticTokens } from '../../styles/tokens';
import type { ReturnStatus, ReturnDestination, ReturnMethod, AlertPriority } from '../../types/models';

type BadgeVariant = 'status' | 'destination' | 'method' | 'priority';

interface StatusBadgeProps {
  variant?: BadgeVariant;
  value: string;
  size?: 'sm' | 'md' | 'lg';
}

const statusColors: Record<string, { bg: string; text: string; border: string }> = {
  PENDIENTE: { bg: '#FEF3C7', text: '#92400E', border: '#FCD34D' },
  PRE_APROBADO: { bg: '#DBEAFE', text: '#1E40AF', border: '#93C5FD' },
  APROBADO: { bg: '#D1FAE5', text: '#065F46', border: '#6EE7B7' },
  RECHAZADO: { bg: '#FEE2E2', text: '#991B1B', border: '#FCA5A5' },
  EN_TRANSITO: { bg: '#E0E7FF', text: '#3730A3', border: '#A5B4FC' },
  ENTREGADO: { bg: '#D1FAE5', text: '#065F46', border: '#6EE7B7' },
  INSPECCION: { bg: '#FED7AA', text: '#9A3412', border: '#FDBA74' },
  PROCESADO: { bg: '#D1FAE5', text: '#065F46', border: '#6EE7B7' },
  EXCEPTION: { bg: '#FEE2E2', text: '#991B1B', border: '#FCA5A5' },
  CARRIL_RAPIDO: { bg: '#DBEAFE', text: '#1E40AF', border: '#93C5FD' },
  OUTLET: { bg: '#EDE9FE', text: '#5B21B6', border: '#C4B5FD' },
  RECICLAJE: { bg: '#D1FAE5', text: '#065F46', border: '#6EE7B7' },
  KEEP_IT: { bg: '#CCFBF1', text: '#0F766E', border: '#5EEAD4' },
  INSPECCION_B2B: { bg: '#FED7AA', text: '#9A3412', border: '#FDBA74' },
  DROP_OFF: { bg: '#DBEAFE', text: '#1E40AF', border: '#93C5FD' },
  PICKUP: { bg: '#E0E7FF', text: '#3730A3', border: '#A5B4FC' },
  LOW: { bg: '#D1FAE5', text: '#065F46', border: '#6EE7B7' },
  MEDIUM: { bg: '#FEF3C7', text: '#92400E', border: '#FCD34D' },
  HIGH: { bg: '#FED7AA', text: '#9A3412', border: '#FDBA74' },
  CRITICAL: { bg: '#FEE2E2', text: '#991B1B', border: '#FCA5A5' },
};

const defaultColors = { bg: '#F3F4F6', text: '#374151', border: '#D1D5DB' };

function getBadgeColor(value: string): { bg: string; text: string; border: string } {
  return statusColors[value] || defaultColors;
}

function formatBadgeLabel(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  variant = 'status',
  value,
  size = 'md',
}) => {
  const colors = getBadgeColor(value);

  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm',
  };

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full border ${sizeClasses[size]}`}
      style={{
        backgroundColor: colors.bg,
        color: colors.text,
        borderColor: colors.border,
      }}
    >
      {formatBadgeLabel(value)}
    </span>
  );
};

export default StatusBadge;
