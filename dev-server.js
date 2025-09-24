#!/usr/bin/env node

/**
 * BodyScript Development Server
 *
 * Enhanced development server with additional features beyond basic Vite dev server.
 * Provides API mocking, live reload enhancements, and development utilities.
 */

import { createServer } from 'vite';
import { resolve } from 'path';
import { existsSync } from 'fs';

const __dirname = new URL('.', import.meta.url).pathname;

/**
 * Development server configuration
 */
const devConfig = {
  port: 3000,
  host: '0.0.0.0',
  open: true,

  // Mock API responses for development
  mockData: {
    gallery: [
      {
        id: 'demo1',
        title: 'Dancing Motion Analysis',
        category: 'dance',
        accuracy: 94.2,
        preview: '/api/videos/demo1_preview.mp4',
        full: '/api/videos/demo1_full.mp4',
        thumbnail: '/api/videos/demo1_thumb.jpg',
      },
      {
        id: 'demo2',
        title: 'Soccer Training Session',
        category: 'sports',
        accuracy: 89.7,
        preview: '/api/videos/demo2_preview.mp4',
        full: '/api/videos/demo2_full.mp4',
        thumbnail: '/api/videos/demo2_thumb.jpg',
      },
      {
        id: 'demo3',
        title: 'Yoga Flow Sequence',
        category: 'yoga',
        accuracy: 96.1,
        preview: '/api/videos/demo3_preview.mp4',
        full: '/api/videos/demo3_full.mp4',
        thumbnail: '/api/videos/demo3_thumb.jpg',
      },
    ],

    healthCheck: {
      status: 'healthy',
      version: '1.0.0',
      timestamp: new Date().toISOString(),
      features: {
        upload: true,
        processing: true,
        gallery: true,
      },
    },
  },
};

/**
 * Create custom middleware for API mocking
 */
function createMockApiMiddleware() {
  return (req, res, next) => {
    const url = req.url;

    // CORS headers for development
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
      res.status(200).end();
      return;
    }

    // Mock API endpoints
    if (url.startsWith('/api/health')) {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify(devConfig.mockData.healthCheck));
      return;
    }

    if (url.startsWith('/api/gallery')) {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({
        videos: devConfig.mockData.gallery,
        total: devConfig.mockData.gallery.length,
      }));
      return;
    }

    if (url.startsWith('/api/upload') && req.method === 'POST') {
      // Simulate upload processing
      setTimeout(() => {
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({
          success: true,
          id: 'upload_' + Date.now(),
          processed_video_url: '/api/videos/processed_demo.mp4',
          pose_data_url: '/api/data/pose_data.csv',
          accuracy: 92.3,
          processing_time: 15.2,
        }));
      }, 2000);
      return;
    }

    // Continue with normal processing
    next();
  };
}

/**
 * Start development server
 */
async function startDevServer() {
  try {
    console.log('\x1b[36m[DEV SERVER]\x1b[0m Starting BodyScript development server...');

    const server = await createServer({
      configFile: resolve(__dirname, 'vite.config.js'),
      mode: 'development',

      server: {
        port: devConfig.port,
        host: devConfig.host,
        open: devConfig.open,
        cors: true,

        // Enhanced proxy configuration
        proxy: {
          // Proxy API calls to backend (if available)
          '/api': {
            target: process.env.BACKEND_URL || 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
            timeout: 30000,

            // Fallback to mock if backend is not available
            configure: (proxy) => {
              proxy.on('error', (err, req, res) => {
                console.log('\x1b[33m[DEV SERVER]\x1b[0m Backend not available, using mock API');
                createMockApiMiddleware()(req, res, () => {});
              });
            },
          },

          // Proxy uploads
          '/uploads': {
            target: process.env.BACKEND_URL || 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
          },
        },

        // Custom middleware
        middlewares: [
          createMockApiMiddleware(),
        ],
      },

      // Enhanced build options for development
      build: {
        sourcemap: true,
        minify: false,
      },

      // Define development constants
      define: {
        __DEV__: true,
        __PROD__: false,
        'process.env.NODE_ENV': JSON.stringify('development'),
      },
    });

    await server.listen();

    const info = server.config.logger.info;
    info('\x1b[32m[DEV SERVER]\x1b[0m BodyScript development server started successfully!');
    info('\x1b[36m[DEV SERVER]\x1b[0m Features enabled:');
    info('  • Hot module reload');
    info('  • Source maps');
    info('  • Mock API endpoints');
    info('  • CORS enabled');
    info('  • Backend proxy (with fallback)');

    // Log available routes
    info('\x1b[36m[DEV SERVER]\x1b[0m Available routes:');
    info('  • http://localhost:3000/ (Gallery)');
    info('  • http://localhost:3000/upload.html (Upload)');

    // Log mock API endpoints
    info('\x1b[36m[DEV SERVER]\x1b[0m Mock API endpoints:');
    info('  • GET /api/health');
    info('  • GET /api/gallery');
    info('  • POST /api/upload');

  } catch (error) {
    console.error('\x1b[31m[DEV SERVER]\x1b[0m Failed to start development server:', error);
    process.exit(1);
  }
}

/**
 * Handle graceful shutdown
 */
process.on('SIGTERM', () => {
  console.log('\x1b[36m[DEV SERVER]\x1b[0m Shutting down development server...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('\x1b[36m[DEV SERVER]\x1b[0m Shutting down development server...');
  process.exit(0);
});

// Start server if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  startDevServer();
}

export { startDevServer, devConfig };