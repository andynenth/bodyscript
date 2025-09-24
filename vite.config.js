import { defineConfig } from 'vite';
import { createHtmlPlugin } from 'vite-plugin-html';
import legacy from '@vitejs/plugin-legacy';
import { resolve } from 'path';

export default defineConfig(({ command, mode }) => {
  const isProduction = mode === 'production';

  return {
    // Root directory for source files
    root: './frontend',

    // Base public path
    base: '/',

    // Define entry points
    build: {
      outDir: '../dist',
      emptyOutDir: true,
      sourcemap: !isProduction,

      // Configure rollup options for multi-page app
      rollupOptions: {
        input: {
          main: resolve(__dirname, 'frontend/index.html'),
          upload: resolve(__dirname, 'frontend/upload.html'),
        },

        // Ensure proper chunking for shared dependencies
        manualChunks: {
          // Core application code shared between pages
          'app-core': [
            './frontend/js/main.js',
            './frontend/js/utils/dom-helpers.js',
            './frontend/js/utils/format-helpers.js',
          ],

          // Gallery-specific modules
          'gallery': [
            './frontend/js/core/GalleryCore.js',
            './frontend/js/core/FilterManager.js',
            './frontend/js/core/GalleryDataStore.js',
            './frontend/js/core/VideoModal.js',
          ],

          // Upload-specific modules
          'upload': [
            './frontend/js/components/file-handler.js',
            './frontend/js/components/progress-bar.js',
            './frontend/js/api/upload.js',
          ],

          // UI components shared between pages
          'ui-components': [
            './frontend/js/components/VideoHoverPreview.js',
            './frontend/js/core/Modal.js',
            './frontend/js/core/VideoPlayer.js',
          ],

          // Utilities
          'utils': [
            './frontend/js/utils/LazyLoader.js',
            './frontend/js/utils/TouchHandler.js',
            './frontend/js/utils/event-helpers.js',
          ],
        },

        // Output configuration
        output: {
          // Organize assets in folders
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name.split('.');
            const ext = info[info.length - 1];

            if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
              return `assets/images/[name]-[hash][extname]`;
            }
            if (/css/i.test(ext)) {
              return `assets/css/[name]-[hash][extname]`;
            }
            return `assets/[ext]/[name]-[hash][extname]`;
          },

          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
        },
      },

      // Enable minification in production
      minify: isProduction ? 'terser' : false,

      // Terser options for better minification
      terserOptions: isProduction ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
        },
        format: {
          comments: false,
        },
      } : {},

      // Chunk size warnings
      chunkSizeWarningLimit: 500,
    },

    // Development server configuration
    server: {
      port: 3000,
      open: true,
      cors: true,

      // Proxy API calls to backend during development
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
        '/uploads': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },

    // Preview server (for production build testing)
    preview: {
      port: 3000,
      open: true,
    },

    // CSS processing configuration
    css: {
      devSourcemap: !isProduction,

      // PostCSS configuration will be read from postcss.config.js
      postcss: {},
    },

    // Define global constants
    define: {
      __DEV__: !isProduction,
      __PROD__: isProduction,
    },

    // Configure module resolution
    resolve: {
      alias: {
        '@': resolve(__dirname, 'frontend'),
        '@js': resolve(__dirname, 'frontend/js'),
        '@css': resolve(__dirname, 'frontend/css'),
        '@assets': resolve(__dirname, 'frontend/assets'),
        '@components': resolve(__dirname, 'frontend/js/components'),
        '@utils': resolve(__dirname, 'frontend/js/utils'),
        '@core': resolve(__dirname, 'frontend/js/core'),
      },
    },

    // Plugins
    plugins: [
      // HTML plugin for multi-page app
      createHtmlPlugin({
        minify: isProduction,
        pages: [
          {
            entry: 'js/entries/gallery.js',
            filename: 'index.html',
            template: 'index.html',
            injectOptions: {
              data: {
                title: 'BodyScript Gallery - Terminal Style',
                environment: mode,
              },
            },
          },
          {
            entry: 'js/entries/upload.js',
            filename: 'upload.html',
            template: 'upload.html',
            injectOptions: {
              data: {
                title: 'BodyScript Upload - Terminal Interface',
                environment: mode,
              },
            },
          },
        ],
      }),

      // Legacy browser support
      legacy({
        targets: ['defaults', 'not IE 11'],
        additionalLegacyPolyfills: ['regenerator-runtime/runtime'],
        modernPolyfills: true,
      }),
    ],

    // Optimize dependencies
    optimizeDeps: {
      include: [
        // Pre-bundle these dependencies for faster dev server startup
      ],
      exclude: [
        // Don't pre-bundle these
      ],
    },

    // Enable experimental features if needed
    esbuild: {
      // Drop console and debugger in production
      drop: isProduction ? ['console', 'debugger'] : [],
    },
  };
});