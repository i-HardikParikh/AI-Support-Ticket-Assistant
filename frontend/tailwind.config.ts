import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        surface2: 'var(--surface2)',
        border: 'var(--border)',
        border2: 'var(--border2)',
        muted: '#a1a1aa',
        accent: 'var(--accent)',
        'accent-hover': '#6352e8',
        success: '#22c55e',
        danger: '#ef4444',
        warning: '#eab308',
        info: '#06b6d4',
      },
    },
  },
  plugins: [],
}
export default config


