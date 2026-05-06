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
        bg: '#09090b',
        surface: '#18181b',
        border: '#27272a',
        muted: '#a1a1aa',
        accent: '#3b82f6',
        'accent-hover': '#2563eb',
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


