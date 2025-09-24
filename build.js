#!/usr/bin/env node

/**
 * BodyScript Frontend Build Script
 *
 * This script provides enhanced build capabilities beyond the basic Vite configuration.
 * It handles asset optimization, bundle analysis, and deployment preparation.
 */

import { build } from 'vite';
import { existsSync, mkdirSync, copyFileSync, statSync } from 'fs';
import { resolve, join } from 'path';
import { execSync } from 'child_process';

const __dirname = new URL('.', import.meta.url).pathname;

// Build configuration
const config = {
  modes: {
    development: {
      minify: false,
      sourcemap: true,
      dropConsole: false,
    },
    production: {
      minify: true,
      sourcemap: false,
      dropConsole: true,
    },
  },

  paths: {
    frontend: resolve(__dirname, 'frontend'),
    dist: resolve(__dirname, 'dist'),
    static: resolve(__dirname, 'frontend/assets'),
  },
};

/**
 * Utility functions
 */
const utils = {
  log: (message, type = 'info') => {
    const colors = {
      info: '\x1b[36m',
      success: '\x1b[32m',
      warning: '\x1b[33m',
      error: '\x1b[31m',
      reset: '\x1b[0m',
    };
    console.log(`${colors[type]}[BUILD]${colors.reset} ${message}`);
  },

  formatBytes: (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  getBundleSize: (filePath) => {
    try {
      const stats = statSync(filePath);
      return stats.size;
    } catch {
      return 0;
    }
  },
};

/**
 * Pre-build tasks
 */
async function preBuild(mode) {
  utils.log(`Starting ${mode} build...`, 'info');

  // Clean dist directory
  if (existsSync(config.paths.dist)) {
    utils.log('Cleaning dist directory...', 'info');
    execSync(`rm -rf ${config.paths.dist}`, { stdio: 'inherit' });
  }

  // Create dist directory
  mkdirSync(config.paths.dist, { recursive: true });

  // Copy static assets that aren't processed by Vite
  const staticFiles = ['player.png', 'mobile.png'];
  staticFiles.forEach(file => {
    const srcPath = join(config.paths.frontend, file);
    const destPath = join(config.paths.dist, file);

    if (existsSync(srcPath)) {
      copyFileSync(srcPath, destPath);
      utils.log(`Copied ${file}`, 'success');
    }
  });
}

/**
 * Post-build tasks
 */
async function postBuild(mode) {
  utils.log('Running post-build tasks...', 'info');

  // Bundle analysis for production
  if (mode === 'production') {
    await analyzeBundles();
  }

  // Generate build report
  generateBuildReport(mode);

  utils.log(`${mode} build completed successfully!`, 'success');
}

/**
 * Analyze bundle sizes and composition
 */
async function analyzeBundles() {
  utils.log('Analyzing bundle composition...', 'info');

  const assetsDir = join(config.paths.dist, 'assets');

  if (!existsSync(assetsDir)) {
    utils.log('No assets directory found for analysis', 'warning');
    return;
  }

  // Get all JS bundles
  const jsFiles = execSync(`find ${assetsDir} -name "*.js" -type f`)
    .toString()
    .split('\n')
    .filter(file => file.trim());

  // Get all CSS files
  const cssFiles = execSync(`find ${assetsDir} -name "*.css" -type f`)
    .toString()
    .split('\n')
    .filter(file => file.trim());

  let totalJsSize = 0;
  let totalCssSize = 0;

  utils.log('JavaScript bundles:', 'info');
  jsFiles.forEach(file => {
    const size = utils.getBundleSize(file);
    totalJsSize += size;
    const fileName = file.split('/').pop();
    utils.log(`  ${fileName}: ${utils.formatBytes(size)}`, 'info');
  });

  utils.log('CSS bundles:', 'info');
  cssFiles.forEach(file => {
    const size = utils.getBundleSize(file);
    totalCssSize += size;
    const fileName = file.split('/').pop();
    utils.log(`  ${fileName}: ${utils.formatBytes(size)}`, 'info');
  });

  utils.log(`Total JS: ${utils.formatBytes(totalJsSize)}`, 'success');
  utils.log(`Total CSS: ${utils.formatBytes(totalCssSize)}`, 'success');
  utils.log(`Total Assets: ${utils.formatBytes(totalJsSize + totalCssSize)}`, 'success');
}

/**
 * Generate build report
 */
function generateBuildReport(mode) {
  const report = {
    mode,
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    node: process.version,
    environment: process.env.NODE_ENV || mode,
  };

  utils.log('Build Report:', 'info');
  Object.entries(report).forEach(([key, value]) => {
    utils.log(`  ${key}: ${value}`, 'info');
  });
}

/**
 * Main build function
 */
async function runBuild() {
  const mode = process.env.NODE_ENV || process.argv[2] || 'development';

  try {
    await preBuild(mode);

    // Run Vite build
    await build({
      mode,
      configFile: resolve(__dirname, 'vite.config.js'),
    });

    await postBuild(mode);

  } catch (error) {
    utils.log(`Build failed: ${error.message}`, 'error');
    process.exit(1);
  }
}

// Run build if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runBuild();
}

export { runBuild, config, utils };