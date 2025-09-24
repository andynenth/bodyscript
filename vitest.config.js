import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        'dist/',
        'frontend/js/entries/',
        'frontend/js/main.js',
        'frontend/js/pages/',
        'frontend/js/adapters/',
        'setup.js',
        'build.js',
        'dev-server.js',
        'vite.config.js',
        'vitest.config.js'
      ],
      include: [
        'frontend/js/core/**/*.js',
        'frontend/js/utils/**/*.js',
        'frontend/js/components/**/*.js'
      ]
    },
    include: [
      'tests/**/*.{test,spec}.js'
    ],
    exclude: [
      'node_modules',
      'dist',
      '.git',
      'venv*'
    ]
  },
  resolve: {
    alias: {
      '@': new URL('./frontend/js', import.meta.url).pathname,
      '@core': new URL('./frontend/js/core', import.meta.url).pathname,
      '@utils': new URL('./frontend/js/utils', import.meta.url).pathname,
      '@components': new URL('./frontend/js/components', import.meta.url).pathname
    }
  }
});