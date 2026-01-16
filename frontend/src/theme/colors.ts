// Color palette from mobile-design-system.md

export const colors = {
  background: '#0B0F1A', // deep midnight blue
  primary: '#5B8CFF', // intelligent blue
  danger: '#FF4D4F', // High Risk
  warning: '#FFB020', // Medium
  success: '#22C55E', // Low
  card: '#111827',
  textPrimary: '#F9FAFB',
  textMuted: '#9CA3AF',
  border: '#1F2937',
  glow: '#FF4D4F', // red glow for high-risk cards
} as const;

export type ColorKey = keyof typeof colors;
