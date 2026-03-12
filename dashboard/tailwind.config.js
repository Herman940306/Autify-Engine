/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef7ff',
          100: '#d9ecff',
          200: '#bcddff',
          300: '#8ec8ff',
          400: '#59a8ff',
          500: '#3388ff',
          600: '#1a6af5',
          700: '#1354e1',
          800: '#1645b6',
          900: '#183d8f',
          950: '#132757',
        },
      },
    },
  },
  plugins: [],
}
