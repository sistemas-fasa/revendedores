/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
    "./public/**/*.html",
    "./dev-dist/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fdf2f2',
          100: '#fde8e8',
          200: '#fbd5d5',
          300: '#f8b4b4',
          400: '#f98080',
          500: '#f05252',
          600: '#e02424',
          700: '#c81e1e',
          800: '#9b1c1c',
          900: '#771d1d'
        }
      },
      spacing: {
        18: '4.5rem',
        26: '6.5rem'
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Arial']
      }
    },
  },
  safelist: [
    'bg-red-600',
    'text-red-600',
    /^bg-(red|green|blue)-(500|600)/
  ],
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
}
