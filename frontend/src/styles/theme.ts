/**
 * Design tokens for engineering dark neutral theme
 * Used by RF, CAD, EDA, aerospace tools
 */

export const theme = {
  colors: {
    // Backgrounds
    background: {
      main: '#0E1116',      // Deep Charcoal - main background
      panel: '#1C2128',     // Slate Gray - panels, sidebars
    },
    
    // Actions/Selection
    action: {
      primary: '#2F6FED',   // Steel Blue - primary actions, selection, focus
      secondary: '#4FB3C8', // Muted Cyan - secondary highlights
    },
    
    // Data Visualization
    signal: {
      success: '#3DDC97',   // Signal Green - good performance, convergence
      warning: '#F4B860',    // Warning Amber - threshold / uncertainty
      critical: '#E5533D',   // Critical Red - mismatch, violation, failure
    },
    
    // Text
    text: {
      primary: '#E6EDF3',   // Primary text
      secondary: '#9BA3AF', // Secondary text
      disabled: '#6B7280',  // Disabled text
    },
    
    // Borders
    border: {
      default: '#2D3748',   // Subtle borders
      focus: '#2F6FED',     // Focus border
      divider: '#1A1F2E',   // Panel dividers
    },
  },
  
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    xxl: '32px',
    xxxl: '48px',
  },
  
  typography: {
    fontFamily: {
      primary: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      mono: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
    },
    fontSize: {
      xs: '11px',
      sm: '12px',
      md: '13px',
      lg: '14px',
      xl: '16px',
      xxl: '18px',
      xxxl: '24px',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
    },
  },
  
  borderRadius: {
    sm: '2px',
    md: '4px',
    lg: '6px',
  },
  
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
    md: '0 2px 4px rgba(0, 0, 0, 0.3)',
    lg: '0 4px 8px rgba(0, 0, 0, 0.4)',
  },
  
  zIndex: {
    dropdown: 1000,
    modal: 2000,
    tooltip: 3000,
  },
} as const;

export type Theme = typeof theme;



















