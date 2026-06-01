/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./*.html', './docs/*.html', './assets/*.js', './build_docs.py', './_template.py'],
  theme: {
    extend: {
      // The whole site is built on the slate scale. Nudge every shade a step
      // darker than Tailwind's default so the grey section backgrounds,
      // borders and muted text read with a touch more contrast. Defining it
      // here keeps it the single source of truth: every page, and any new
      // page reusing slate utilities, inherits the darker greys for free.
      colors: {
        slate: {
          50: '#f1f5f9',
          100: '#e7edf3',
          200: '#d2dbe6',
          300: '#b5c0cf',
          400: '#7f8da1',
          500: '#556376',
          600: '#3c4859',
          700: '#2b3747',
          800: '#1a2433',
          900: '#0c1320',
          950: '#020617',
        },
      },
    },
  },
  plugins: [],
};
