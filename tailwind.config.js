/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        primary:          'var(--primary)',
        'primary-hover':  'var(--primary-hover)',
        'primary-light':  'var(--primary-light)',
        'primary-muted':  'var(--primary-muted)',
        secondary:        'var(--secondary)',
        'secondary-hover':'var(--secondary-hover)',
        'secondary-light':'var(--secondary-light)',
        'secondary-muted':'var(--secondary-muted)',
        success:          'var(--success)',
        'success-light':  'var(--success-light)',
        danger:           'var(--danger)',
        'danger-hover':   'var(--danger-hover)',
        'danger-light':   'var(--danger-light)',
        warning:          'var(--warning)',
        'warning-light':  'var(--warning-light)',
        info:             'var(--info)',
        'info-light':     'var(--info-light)',
        surface:          'var(--surface)',
        'surface-2':      'var(--surface-2)',
        'bg-page':        'var(--bg-page)',
        'bg-light':       'var(--bg-light)',
        border:           'var(--border)',
        'border-strong':  'var(--border-strong)',
        'text-primary':   'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted':     'var(--text-muted)',
      },
      spacing: {
        // Custom spacing if needed
      },
      fontFamily: {
        sans: [
          'Alexandria',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
          'Apple Color Emoji',
          'Segoe UI Emoji',
        ],
      },
    },
  },
  plugins: [
    require('tailwindcss-rtl'),
  ],
  // Enable RTL mode
  ltr: false,
  rtl: true,
}
