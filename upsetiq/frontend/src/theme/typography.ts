// Typography from mobile-design-system.md
// Heading: Inter / SF Pro
// Body: Inter / SF Pro
// Numbers: JetBrains Mono (for UPS % and metrics)

export const typography = {
  // Headings - Inter/SF Pro (system default on iOS, Inter on Android)
  heading1: {
    fontSize: 32,
    fontWeight: '700' as const,
    fontFamily: 'System',
  },
  heading2: {
    fontSize: 24,
    fontWeight: '600' as const,
    fontFamily: 'System',
  },
  heading3: {
    fontSize: 20,
    fontWeight: '600' as const,
    fontFamily: 'System',
  },
  heading4: {
    fontSize: 18,
    fontWeight: '600' as const,
    fontFamily: 'System',
  },
  // Body - Inter/SF Pro
  body: {
    fontSize: 16,
    fontWeight: '400' as const,
    fontFamily: 'System',
  },
  bodySmall: {
    fontSize: 14,
    fontWeight: '400' as const,
    fontFamily: 'System',
  },
  // Numbers - JetBrains Mono (monospace for UPS and metrics)
  number: {
    fontSize: 48,
    fontWeight: '700' as const,
    fontFamily: 'monospace', // Will use system monospace, can be customized later
  },
  numberMedium: {
    fontSize: 32,
    fontWeight: '700' as const,
    fontFamily: 'monospace',
  },
  numberSmall: {
    fontSize: 20,
    fontWeight: '600' as const,
    fontFamily: 'monospace',
  },
} as const;
