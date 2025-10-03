/**
 * Modern Design System Theme
 * Inspired by Netflix and modern learning platforms
 */

export const lightTheme = {
  // Brand Colors
  colors: {
    primary: '#FF6B6B',      // Vibrant red (Netflix-inspired)
    primaryDark: '#EE5A52',
    primaryLight: '#FF8787',

    secondary: '#4ECDC4',    // Teal accent
    secondaryDark: '#38B2AA',
    secondaryLight: '#6DD5CE',

    success: '#52C41A',      // Green
    warning: '#FAAD14',      // Orange
    error: '#F5222D',        // Red
    info: '#1890FF',         // Blue

    // Neutrals
    background: '#FFFFFF',
    surface: '#F8F9FA',
    surfaceHover: '#F0F2F5',

    text: '#1A1A1A',
    textSecondary: '#6C757D',
    textLight: '#ADB5BD',
    textInverse: '#FFFFFF',

    border: '#E1E4E8',
    borderLight: '#F0F2F5',

    // Semantic
    disabled: '#D1D5DB',
    overlay: 'rgba(0, 0, 0, 0.5)',
    shadow: 'rgba(0, 0, 0, 0.1)',
  },

  // Typography
  typography: {
    fontFamily: {
      primary: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      secondary: '"Poppins", "Inter", sans-serif',
      mono: '"JetBrains Mono", "Courier New", monospace',
    },

    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '1.875rem',// 30px
      '4xl': '2.25rem', // 36px
      '5xl': '3rem',    // 48px
    },

    fontWeight: {
      light: 300,
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
    },

    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
      loose: 2,
    },
  },

  // Spacing
  spacing: {
    xs: '0.25rem',   // 4px
    sm: '0.5rem',    // 8px
    md: '1rem',      // 16px
    lg: '1.5rem',    // 24px
    xl: '2rem',      // 32px
    '2xl': '3rem',   // 48px
    '3xl': '4rem',   // 64px
    '4xl': '6rem',   // 96px
  },

  // Border Radius
  radius: {
    none: '0',
    sm: '0.25rem',   // 4px
    md: '0.5rem',    // 8px
    lg: '0.75rem',   // 12px
    xl: '1rem',      // 16px
    '2xl': '1.5rem', // 24px
    full: '9999px',
  },

  // Shadows
  shadows: {
    none: 'none',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',

    // Colored shadows
    primary: '0 10px 40px -10px rgba(255, 107, 107, 0.35)',
    secondary: '0 10px 40px -10px rgba(78, 205, 196, 0.35)',
  },

  // Transitions
  transitions: {
    fast: '150ms ease-in-out',
    normal: '250ms ease-in-out',
    slow: '350ms ease-in-out',

    easing: {
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    },
  },

  // Z-index layers
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

  // Breakpoints
  breakpoints: {
    xs: '480px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },

  // Grid
  grid: {
    columns: 12,
    gutter: '1rem',
    maxWidth: '1280px',
  },
};

// Dark Theme
export const darkTheme = {
  ...lightTheme,
  colors: {
    ...lightTheme.colors,

    // Override colors for dark mode
    primary: '#FF6B6B',
    primaryDark: '#FF5252',
    primaryLight: '#FF8A80',

    background: '#0A0A0A',
    surface: '#1A1A1A',
    surfaceHover: '#252525',

    text: '#F0F0F0',
    textSecondary: '#B0B0B0',
    textLight: '#808080',
    textInverse: '#0A0A0A',

    border: '#2D2D2D',
    borderLight: '#1F1F1F',

    disabled: '#4A4A4A',
    overlay: 'rgba(0, 0, 0, 0.8)',
    shadow: 'rgba(0, 0, 0, 0.3)',
  },

  shadows: {
    ...lightTheme.shadows,
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.2)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.3)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.6)',

    primary: '0 10px 40px -10px rgba(255, 107, 107, 0.5)',
    secondary: '0 10px 40px -10px rgba(78, 205, 196, 0.5)',
  },
};

export type Theme = typeof lightTheme;

// Media query helpers
export const media = {
  xs: `@media (min-width: ${lightTheme.breakpoints.xs})`,
  sm: `@media (min-width: ${lightTheme.breakpoints.sm})`,
  md: `@media (min-width: ${lightTheme.breakpoints.md})`,
  lg: `@media (min-width: ${lightTheme.breakpoints.lg})`,
  xl: `@media (min-width: ${lightTheme.breakpoints.xl})`,
  '2xl': `@media (min-width: ${lightTheme.breakpoints['2xl']})`,
};

export default lightTheme;
