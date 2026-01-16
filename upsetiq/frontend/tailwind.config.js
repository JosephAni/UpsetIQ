/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./App.{js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        background: '#0B0F1A',
        primary: '#5B8CFF',
        danger: '#FF4D4F',
        warning: '#FFB020',
        success: '#22C55E',
        card: '#111827',
        'text-primary': '#F9FAFB',
        'text-muted': '#9CA3AF',
        border: '#1F2937',
        glow: '#FF4D4F',
      },
      fontFamily: {
        mono: ['monospace'], // JetBrains Mono fallback
      },
    },
  },
  plugins: [],
}
