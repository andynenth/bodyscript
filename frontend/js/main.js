/**
 * BodyScript Frontend Main Entry Point
 *
 * This is the main entry point for the entire frontend application.
 * It provides shared functionality and initializes common features.
 */

// Import core utilities that should be available everywhere
import '@utils/passive-events-polyfill.js';

// Import shared styles
import '@css/main.css';

/**
 * Global application state and configuration
 */
window.BodyScript = {
  version: '1.0.0',
  initialized: false,
  features: {
    touchSupport: 'ontouchstart' in window,
    mediaSupport: 'mediaDevices' in navigator,
    moduleSupport: true,
  },

  // Global configuration that can be overridden
  config: {
    debug: __DEV__,
    apiBaseUrl: window.API_BASE_URL || '/api',
    maxFileSize: 50 * 1024 * 1024, // 50MB
    supportedFormats: ['video/mp4', 'video/quicktime', 'video/x-msvideo'],
  },
};

/**
 * Global utility functions
 */
window.BodyScript.utils = {
  /**
   * Log function that respects debug mode
   */
  log: (...args) => {
    if (window.BodyScript.config.debug) {
      console.log('[BodyScript]', ...args);
    }
  },

  /**
   * Error logging
   */
  error: (...args) => {
    console.error('[BodyScript]', ...args);
  },

  /**
   * Format bytes for display
   */
  formatBytes: (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  /**
   * Format duration in seconds to MM:SS
   */
  formatDuration: (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  },

  /**
   * Debounce function for performance
   */
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  /**
   * Throttle function for performance
   */
  throttle: (func, wait) => {
    let inThrottle;
    return function executedFunction(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, wait);
      }
    };
  },
};

/**
 * Global event system for cross-module communication
 */
window.BodyScript.events = {
  listeners: {},

  /**
   * Subscribe to an event
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  },

  /**
   * Unsubscribe from an event
   */
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  },

  /**
   * Emit an event
   */
  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          window.BodyScript.utils.error('Event callback error:', error);
        }
      });
    }
  },
};

/**
 * Initialize global features
 */
function initializeGlobalFeatures() {
  window.BodyScript.utils.log('Initializing global features...');

  // Feature detection
  const features = window.BodyScript.features;

  if (features.touchSupport) {
    document.body.classList.add('touch-device');
  }

  if (!features.mediaSupport) {
    window.BodyScript.utils.error('Media devices not supported in this browser');
  }

  // Global error handling
  window.addEventListener('error', (event) => {
    window.BodyScript.utils.error('Global error:', event.error);
  });

  // Unhandled promise rejection handling
  window.addEventListener('unhandledrejection', (event) => {
    window.BodyScript.utils.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
  });

  // Page visibility API for performance optimization
  if ('visibilityState' in document) {
    document.addEventListener('visibilitychange', () => {
      window.BodyScript.events.emit('visibility-change', {
        hidden: document.hidden,
        state: document.visibilityState,
      });
    });
  }

  window.BodyScript.initialized = true;
  window.BodyScript.utils.log('Global features initialized');
}

/**
 * Initialize when DOM is ready
 */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeGlobalFeatures);
} else {
  initializeGlobalFeatures();
}

// Expose for debugging in development
if (__DEV__) {
  window.BodyScriptDebug = {
    features: window.BodyScript.features,
    config: window.BodyScript.config,
    events: window.BodyScript.events,
  };
}

export { initializeGlobalFeatures };