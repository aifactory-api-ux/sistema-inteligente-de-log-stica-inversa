export const tokens = {
  colors: {
    primary: '#1E40AF',
    primaryLight: '#3B82F6',
    primaryDark: '#1E3A8A',

    success: '#059669',
    successLight: '#10B981',
    successDark: '#047857',

    warning: '#D97706',
    warningLight: '#F59E0B',
    warningDark: '#B45309',

    danger: '#DC2626',
    dangerLight: '#EF4444',
    dangerDark: '#B91C1C',

    gray50: '#F9FAFB',
    gray100: '#F3F4F6',
    gray200: '#E5E7EB',
    gray300: '#D1D5DB',
    gray400: '#9CA3AF',
    gray500: '#6B7280',
    gray600: '#4B5563',
    gray700: '#374151',
    gray800: '#1F2937',
    gray900: '#111827',

    darkNavy: '#0E1729',
    darkNavyAlt: '#0E1829',
    darkBlue: '#102A43',
    charcoal: '#17212E',

    pageBackground: '#F5F7FA',
    pageBackgroundAlt: '#F6F8FA',
    pageBackgroundDark: '#F2F6FA',

    white: '#FFFFFF',
    black: '#000000',
  },

  typography: {
    fontFamily: {
      sans: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      mono: "'JetBrains Mono', 'Fira Code', 'SF Mono', Monaco, monospace",
    },

    fontSize: {
      xs: '0.6875rem',
      sm: '0.75rem',
      base: '0.875rem',
      lg: '1rem',
      xl: '1.125rem',
      '2xl': '1.25rem',
      '3xl': '1.5rem',
      '4xl': '1.875rem',
      '5xl': '2.25rem',
      '6xl': '3rem',
    },

    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },

    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },

    letterSpacing: {
      tight: '-0.025em',
      normal: '0',
      wide: '0.025em',
      wider: '0.05em',
    },
  },

  spacing: {
    0: '0',
    0.5: '0.125rem',
    1: '0.25rem',
    1.5: '0.375rem',
    2: '0.5rem',
    2.5: '0.625rem',
    3: '0.75rem',
    3.5: '0.875rem',
    4: '1rem',
    5: '1.25rem',
    6: '1.5rem',
    7: '1.75rem',
    8: '2rem',
    9: '2.25rem',
    10: '2.5rem',
    11: '2.75rem',
    12: '3rem',
    14: '3.5rem',
    16: '4rem',
    20: '5rem',
    24: '6rem',
    28: '7rem',
    32: '8rem',

    sectionPadding: '1.5rem',
    cardPadding: '1rem',
    inputPadding: '0.625rem',
  },

  borderRadius: {
    none: '0',
    sm: '0.125rem',
    DEFAULT: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
    '2xl': '1rem',
    '3xl': '1.5rem',
    full: '9999px',
  },

  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
    none: 'none',

    card: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    cardHover: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    modal: '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  },

  transitions: {
    duration: {
      fast: '150ms',
      DEFAULT: '200ms',
      slow: '300ms',
      slower: '500ms',
    },
    easing: {
      DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
  },

  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
    toast: 1080,
  },

  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1440px',
    '3xl': '1536px',
  },
};

export const semanticTokens = {
  pageBg: tokens.colors.pageBackground,
  pageBgAlt: tokens.colors.pageBackgroundAlt,
  pageBgDark: tokens.colors.pageBackgroundDark,

  cardBg: tokens.colors.white,
  cardBorder: tokens.colors.gray200,
  cardShadow: tokens.shadows.card,

  navBg: tokens.colors.darkNavy,
  navBgAlt: tokens.colors.charcoal,
  navText: tokens.colors.white,
  navTextMuted: tokens.colors.gray400,

  textPrimary: tokens.colors.gray900,
  textSecondary: tokens.colors.gray600,
  textMuted: tokens.colors.gray500,
  textDisabled: tokens.colors.gray400,
  textInverse: tokens.colors.white,

  borderDefault: tokens.colors.gray200,
  borderStrong: tokens.colors.gray300,
  borderFocus: tokens.colors.primary,

  statusGreen: tokens.colors.success,
  statusYellow: tokens.colors.warning,
  statusRed: tokens.colors.danger,

  destinationCarrilRapido: '#2563EB',
  destinationOutlet: '#7C3AED',
  destinationReciclaje: '#059669',
  destinationKeepIt: '#0D9488',
  destinationInspeccion: '#D97706',
};

export default tokens;
