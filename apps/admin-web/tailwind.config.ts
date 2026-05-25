import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ford: {
          DEFAULT: '#003478',
          50: '#e6ecf3',
          100: '#cdd9e7',
          200: '#9bb2d0',
          300: '#688cb9',
          400: '#3665a1',
          500: '#003478',
          600: '#002a60',
          700: '#002048',
          800: '#001630',
          900: '#000b18',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
