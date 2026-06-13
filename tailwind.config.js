/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./studio/templates/**/*.html'],
  // Не трогаем базовый reset: в проекте свои стили шапки, форм и т.д. в base.html
  corePlugins: {
    preflight: false,
  },
  theme: {
    extend: {
      colors: {
        olive: {
          DEFAULT: '#4a5240',
          soft: '#6b7349',
          deep: '#3a4133',
        },
        gold: {
          DEFAULT: '#9a7b2c',
          bright: '#b8923a',
          muted: 'rgba(154, 123, 44, 0.12)',
        },
        paper: {
          DEFAULT: '#ebe6d4',
          dark: '#dfdac6',
        },
        surface: '#f5f0e2',
        ink: {
          DEFAULT: '#2b2d26',
          muted: '#5c5e56',
        },
        bordersoft: '#cfc9bc',
      },
      fontFamily: {
        heading: ['"Cormorant Garamond"', 'Georgia', '"Times New Roman"', 'serif'],
        body: ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 12px 40px rgba(43, 45, 38, 0.08)',
        gold: '0 18px 36px rgba(154, 123, 44, 0.25)',
      },
      letterSpacing: {
        wider2: '0.14em',
        widest2: '0.22em',
      },
    },
  },
  plugins: [],
};
