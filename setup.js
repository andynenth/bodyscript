#!/usr/bin/env node

/**
 * BodyScript Frontend Setup Script
 *
 * This script handles initial setup, dependency installation,
 * and environment validation for the BodyScript frontend build system.
 */

import { execSync } from 'child_process';
import { existsSync, mkdirSync, writeFileSync } from 'fs';
import { resolve } from 'path';

const __dirname = new URL('.', import.meta.url).pathname;

/**
 * Setup configuration
 */
const setupConfig = {
  requiredNodeVersion: '18.0.0',
  requiredDirectories: [
    'dist',
    'frontend/js/entries',
    'frontend/css/dist',
  ],
  environmentFiles: [
    '.env.development',
    '.env.production',
  ],
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
    console.log(`${colors[type]}[SETUP]${colors.reset} ${message}`);
  },

  exec: (command, options = {}) => {
    try {
      return execSync(command, { stdio: 'inherit', ...options });
    } catch (error) {
      utils.log(`Command failed: ${command}`, 'error');
      throw error;
    }
  },

  checkNodeVersion: () => {
    const currentVersion = process.version.slice(1); // Remove 'v' prefix
    const required = setupConfig.requiredNodeVersion;

    if (currentVersion < required) {
      utils.log(`Node.js ${required} or higher required. Current: ${currentVersion}`, 'error');
      process.exit(1);
    }

    utils.log(`Node.js version check passed: ${currentVersion}`, 'success');
  },
};

/**
 * Check system requirements
 */
function checkSystemRequirements() {
  utils.log('Checking system requirements...', 'info');

  // Check Node.js version
  utils.checkNodeVersion();

  // Check if git is available
  try {
    execSync('git --version', { stdio: 'pipe' });
    utils.log('Git is available', 'success');
  } catch {
    utils.log('Git is not available (recommended for development)', 'warning');
  }

  // Check package manager
  try {
    execSync('npm --version', { stdio: 'pipe' });
    utils.log('npm is available', 'success');
  } catch {
    utils.log('npm is required but not available', 'error');
    process.exit(1);
  }
}

/**
 * Create required directories
 */
function createDirectories() {
  utils.log('Creating required directories...', 'info');

  setupConfig.requiredDirectories.forEach(dir => {
    const fullPath = resolve(__dirname, dir);
    if (!existsSync(fullPath)) {
      mkdirSync(fullPath, { recursive: true });
      utils.log(`Created directory: ${dir}`, 'success');
    } else {
      utils.log(`Directory exists: ${dir}`, 'info');
    }
  });
}

/**
 * Install dependencies
 */
function installDependencies() {
  utils.log('Installing dependencies...', 'info');

  // Check if package.json exists
  if (!existsSync(resolve(__dirname, 'package.json'))) {
    utils.log('package.json not found!', 'error');
    process.exit(1);
  }

  // Install dependencies
  utils.exec('npm install');
  utils.log('Dependencies installed successfully', 'success');
}

/**
 * Validate environment files
 */
function validateEnvironment() {
  utils.log('Validating environment configuration...', 'info');

  setupConfig.environmentFiles.forEach(envFile => {
    const fullPath = resolve(__dirname, envFile);
    if (!existsSync(fullPath)) {
      utils.log(`Environment file missing: ${envFile}`, 'warning');
    } else {
      utils.log(`Environment file found: ${envFile}`, 'success');
    }
  });
}

/**
 * Create a simple .gitignore if it doesn't exist
 */
function createGitIgnore() {
  const gitignorePath = resolve(__dirname, '.gitignore');

  if (!existsSync(gitignorePath)) {
    const gitignoreContent = `# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build output
dist/
*.tgz
*.tar.gz

# Environment files
.env.local
.env.*.local

# Editor directories and files
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# nyc test coverage
.nyc_output/

# node-waf configuration
.lock-wscript

# Compiled binary addons
build/Release/

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity
`;

    writeFileSync(gitignorePath, gitignoreContent);
    utils.log('Created .gitignore file', 'success');
  } else {
    utils.log('.gitignore file exists', 'info');
  }
}

/**
 * Run setup validation
 */
function validateSetup() {
  utils.log('Running setup validation...', 'info');

  // Check if build can run
  try {
    utils.exec('npm run build', { stdio: 'pipe' });
    utils.log('Build test passed', 'success');
  } catch {
    utils.log('Build test failed - this may be expected if backend is not running', 'warning');
  }

  // Check linting
  try {
    utils.exec('npm run lint:js', { stdio: 'pipe' });
    utils.log('JavaScript linting passed', 'success');
  } catch {
    utils.log('JavaScript linting failed - please fix errors before continuing', 'warning');
  }
}

/**
 * Display completion message
 */
function displayCompletionMessage() {
  utils.log('Setup completed successfully!', 'success');
  utils.log('', 'info');
  utils.log('Available commands:', 'info');
  utils.log('  npm run dev       - Start development server', 'info');
  utils.log('  npm run build     - Build for production', 'info');
  utils.log('  npm run preview   - Preview production build', 'info');
  utils.log('  npm run lint:js   - Lint JavaScript files', 'info');
  utils.log('  npm run lint:css  - Lint CSS files', 'info');
  utils.log('  npm run format    - Format all files', 'info');
  utils.log('', 'info');
  utils.log('To start developing:', 'info');
  utils.log('  npm run dev', 'success');
}

/**
 * Main setup function
 */
async function runSetup() {
  try {
    utils.log('Starting BodyScript frontend setup...', 'info');

    checkSystemRequirements();
    createDirectories();
    createGitIgnore();
    installDependencies();
    validateEnvironment();
    validateSetup();

    displayCompletionMessage();

  } catch (error) {
    utils.log(`Setup failed: ${error.message}`, 'error');
    process.exit(1);
  }
}

// Run setup if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runSetup();
}

export { runSetup, setupConfig, utils };