/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./*.html', './download/*.html', './docs/*.html', './assets/*.js', './build_docs.py', './_template.py'],
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
          800: '#13203b',
          900: '#0b1428',
          950: '#060c1a',
        },
        // Brand accent. The whole UI leans on the amber utilities for links,
        // underlines and call-to-action buttons. Remapping the scale to the
        // MurOS yellow keeps every accent on brand without touching markup.
        amber: {
          50: '#fffbeb',
          100: '#fffcc5',
          200: '#fff985',
          300: '#fff645',
          400: '#fff41a',
          500: '#ffdc00',
          600: '#e6b100',
          700: '#bf9200',
          800: '#9b7808',
          900: '#7f640a',
          950: '#493800',
        },
      },
    },
  },
  plugins: [],
};
