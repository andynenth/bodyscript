// Sentry Configuration for BodyScript
// Error tracking and performance monitoring

import * as Sentry from "@sentry/browser";
import { Integrations } from "@sentry/tracing";

// Environment-specific configuration
const SENTRY_CONFIG = {
  development: {
    dsn: null, // No tracking in development
    environment: 'development',
    debug: true,
    beforeSend: () => null // Don't send events in development
  },
  staging: {
    dsn: process.env.VITE_SENTRY_DSN,
    environment: 'staging',
    debug: false,
    sampleRate: 1.0, // Track all errors in staging
    tracesSampleRate: 0.5 // Track 50% of performance
  },
  production: {
    dsn: process.env.VITE_SENTRY_DSN,
    environment: 'production',
    debug: false,
    sampleRate: 1.0, // Track all errors
    tracesSampleRate: 0.1, // Track 10% of performance
    beforeSend: (event) => {
      // Filter out known non-critical errors
      if (event.exception) {
        const error = event.exception.values[0];
        if (error.type === 'ChunkLoadError') {
          return null; // Ignore chunk loading errors
        }
        if (error.value && error.value.includes('ResizeObserver loop limit exceeded')) {
          return null; // Ignore ResizeObserver warnings
        }
      }
      return event;
    }
  }
};

// Initialize Sentry
export function initializeSentry() {
  const environment = process.env.VITE_ENVIRONMENT || 'development';
  const config = SENTRY_CONFIG[environment];

  if (!config.dsn && environment !== 'development') {
    console.warn('Sentry DSN not configured for environment:', environment);
    return;
  }

  Sentry.init({
    dsn: config.dsn,
    environment: config.environment,
    debug: config.debug,
    sampleRate: config.sampleRate || 1.0,
    tracesSampleRate: config.tracesSampleRate || 0.1,
    beforeSend: config.beforeSend,

    integrations: [
      new Integrations.BrowserTracing({
        // Performance monitoring for specific components
        routingInstrumentation: Sentry.routingInstrumentation(
          window.history
        ),

        // Custom instrumentation
        tracePropagationTargets: [
          'localhost',
          'bodyscript.com',
          'api.bodyscript.com',
          /^https:\/\/.*\.bodyscript\.com/
        ]
      })
    ],

    // Additional configuration
    initialScope: {
      tags: {
        component: 'frontend',
        version: process.env.VITE_APP_VERSION || '1.0.0'
      }
    },

    // Release tracking
    release: `bodyscript@${process.env.VITE_APP_VERSION || 'unknown'}`,

    // User context (set after authentication)
    beforeSend: (event) => {
      // Apply environment-specific filtering
      if (config.beforeSend) {
        return config.beforeSend(event);
      }
      return event;
    }
  });

  // Set up custom error boundaries
  window.addEventListener('unhandledrejection', event => {
    Sentry.captureException(event.reason);
  });

  // Performance monitoring for MediaPipe operations
  window.addEventListener('pose-processing-start', () => {
    Sentry.startTransaction({
      name: 'pose-processing',
      op: 'mediapipe.process'
    });
  });

  window.addEventListener('pose-processing-complete', (event) => {
    Sentry.addBreadcrumb({
      category: 'pose-processing',
      message: 'Pose processing completed',
      level: 'info',
      data: {
        duration: event.detail.duration,
        frames: event.detail.frames,
        landmarks: event.detail.landmarks
      }
    });
  });

  console.log(`Sentry initialized for ${environment} environment`);
}

// Custom error tracking functions
export const trackError = (error, context = {}) => {
  Sentry.withScope((scope) => {
    scope.setContext('error_context', context);
    scope.setLevel('error');
    Sentry.captureException(error);
  });
};

export const trackWarning = (message, context = {}) => {
  Sentry.withScope((scope) => {
    scope.setContext('warning_context', context);
    scope.setLevel('warning');
    Sentry.captureMessage(message);
  });
};

export const trackPerformance = (operation, duration, metadata = {}) => {
  Sentry.addBreadcrumb({
    category: 'performance',
    message: `${operation} completed in ${duration}ms`,
    level: 'info',
    data: {
      operation,
      duration,
      ...metadata
    }
  });
};

// User context management
export const setUserContext = (user) => {
  Sentry.setUser({
    id: user.id,
    email: user.email,
    username: user.username
  });
};

export const clearUserContext = () => {
  Sentry.setUser(null);
};

// Custom tags for different components
export const tagError = (tags) => {
  Sentry.withScope((scope) => {
    Object.entries(tags).forEach(([key, value]) => {
      scope.setTag(key, value);
    });
  });
};

// Transaction monitoring for critical operations
export const startTransaction = (name, operation) => {
  return Sentry.startTransaction({
    name,
    op: operation
  });
};

export default {
  initializeSentry,
  trackError,
  trackWarning,
  trackPerformance,
  setUserContext,
  clearUserContext,
  tagError,
  startTransaction
};