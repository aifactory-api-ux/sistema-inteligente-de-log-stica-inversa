import React from 'react';
import { tokens } from '../../styles/tokens';

type ButtonVariant = 'solid' | 'outline' | 'danger' | 'subtle';
type ButtonSize = 'sm' | 'md' | 'lg';

interface PrimaryButtonCTAProps {
  children: React.ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  className?: string;
}

const variantStyles: Record<ButtonVariant, { bg: string; text: string; border: string; hoverBg: string; hoverBorder: string }> = {
  solid: {
    bg: tokens.colors.primary,
    text: tokens.colors.white,
    border: tokens.colors.primary,
    hoverBg: tokens.colors.primaryLight,
    hoverBorder: tokens.colors.primaryLight,
  },
  outline: {
    bg: 'transparent',
    text: tokens.colors.primary,
    border: tokens.colors.primary,
    hoverBg: `${tokens.colors.primary}10`,
    hoverBorder: tokens.colors.primaryLight,
  },
  danger: {
    bg: tokens.colors.danger,
    text: tokens.colors.white,
    border: tokens.colors.danger,
    hoverBg: tokens.colors.dangerLight,
    hoverBorder: tokens.colors.dangerLight,
  },
  subtle: {
    bg: tokens.colors.gray100,
    text: tokens.colors.gray700,
    border: tokens.colors.gray200,
    hoverBg: tokens.colors.gray200,
    hoverBorder: tokens.colors.gray300,
  },
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export const PrimaryButtonCTA: React.FC<PrimaryButtonCTAProps> = ({
  children,
  onClick,
  type = 'button',
  variant = 'solid',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  className = '',
}) => {
  const style = variantStyles[variant];
  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={`
        inline-flex items-center justify-center gap-2 font-medium rounded-lg border
        transition-all duration-200 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-offset-2
        ${sizeStyles[size]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
      style={{
        backgroundColor: isDisabled ? tokens.colors.gray300 : style.bg,
        color: isDisabled ? tokens.colors.gray500 : style.text,
        borderColor: isDisabled ? tokens.colors.gray300 : style.border,
        cursor: isDisabled ? 'not-allowed' : 'pointer',
        opacity: isDisabled ? 0.6 : 1,
      }}
      onMouseEnter={(e) => {
        if (!isDisabled) {
          e.currentTarget.style.backgroundColor = style.hoverBg;
          e.currentTarget.style.borderColor = style.hoverBorder;
        }
      }}
      onMouseLeave={(e) => {
        if (!isDisabled) {
          e.currentTarget.style.backgroundColor = style.bg;
          e.currentTarget.style.borderColor = style.border;
        }
      }}
    >
      {loading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {!loading && leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
      <span>{children}</span>
      {!loading && rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
    </button>
  );
};

export default PrimaryButtonCTA;
