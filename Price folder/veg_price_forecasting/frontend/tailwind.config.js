/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          50: '#f2f9f4',
          100: '#e1f2e6',
          200: '#c3e4ce',
          300: '#95ceab',
          400: '#5fb181',
          500: '#399460',
          600: '#2b784d',
          700: '#235f3e',
          800: '#1e4c33',
          900: '#193f2b',
        }
      }
    },
  },
  plugins: [],
}
