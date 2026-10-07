/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
      colors: {
        primary: {
          DEFAULT: '#002D62', // Azul marino único FOSST
          50:  '#e6f0fa',
          100: '#b8d5f5',
          200: '#85b5ed',
          300: '#5294e5',
          400: '#2677dd',
          500: '#002D62', // Azul marino principal del logo
          600: '#00244e',
          700: '#001b3b',
          800: '#001227',
          900: '#000914',
        },
        brand: {
          DEFAULT: '#F5A800', // Dorado/Amarillo FOSST (casco)
          50:  '#fff8e6',
          100: '#ffedb3',
          200: '#ffe180',
          300: '#ffd54d',
          400: '#ffcc26',
          500: '#F5A800', // Amarillo casco logo
          600: '#db9600',
          700: '#c28500',
          800: '#a87300',
          900: '#7a5400',
        },
        alert: {
          DEFAULT: '#DC2626', // Rojo de alerta único
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#DC2626',
          600: '#b91c1c',
          700: '#991b1b',
        },
        surface: {
          DEFAULT: '#F8FAFC', // Fondo general limpio
          1: '#FFFFFF',       // Tarjetas y elementos flotantes
          2: '#E2E8F0',       // Bordes neutros
          3: '#CBD5E1',       // Bordes secundarios
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        float:   { '0%,100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-10px)' } },
      },
    },
  },
  plugins: [],
}
