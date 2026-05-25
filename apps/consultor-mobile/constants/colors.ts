export const FordBlue = '#003478';

export const Colors = {
  light: {
    text: '#11181C',
    textSecondary: '#687076',
    background: '#f5f5f7',
    card: '#ffffff',
    border: '#e5e5ea',
    tint: FordBlue,
    danger: '#d32f2f',
    warning: '#f57c00',
    success: '#388e3c',
    overlay: 'rgba(0,0,0,0.4)',
  },
  dark: {
    text: '#ECEDEE',
    textSecondary: '#9BA1A6',
    background: '#0a0a0a',
    card: '#1c1c1e',
    border: '#38383a',
    tint: '#3d8bff',
    danger: '#ef5350',
    warning: '#ff9800',
    success: '#66bb6a',
    overlay: 'rgba(0,0,0,0.6)',
  },
} as const;

export type ColorPalette = typeof Colors.light;
