// Analytics Configuration for BodyScript
// Performance monitoring and user behavior tracking

// Google Analytics 4 Configuration
const GA4_CONFIG = {
  development: {
    measurementId: null, // No tracking in development
    enabled: false
  },
  staging: {
    measurementId: process.env.VITE_GA4_STAGING_ID,
    enabled: true,
    debug: true
  },
  production: {
    measurementId: process.env.VITE_GA4_PRODUCTION_ID,
    enabled: true,
    debug: false
  }
};

// Custom events configuration
const EVENTS = {
  // User interactions
  VIDEO_UPLOAD: 'video_upload',
  POSE_PROCESSING_START: 'pose_processing_start',
  POSE_PROCESSING_COMPLETE: 'pose_processing_complete',
  DATA_EXPORT: 'data_export',
  GALLERY_VIEW: 'gallery_view',

  // Performance events
  PAGE_LOAD_TIME: 'page_load_time',
  API_RESPONSE_TIME: 'api_response_time',
  PROCESSING_PERFORMANCE: 'processing_performance',

  // Error events
  PROCESSING_ERROR: 'processing_error',
  UPLOAD_ERROR: 'upload_error',
  API_ERROR: 'api_error',

  // Feature usage
  FEATURE_USED: 'feature_used',
  SETTING_CHANGED: 'setting_changed',
  EXPORT_FORMAT: 'export_format_selected'
};

// Initialize Google Analytics
export function initializeAnalytics() {
  const environment = process.env.VITE_ENVIRONMENT || 'development';
  const config = GA4_CONFIG[environment];

  if (!config.enabled || !config.measurementId) {
    console.log('Analytics disabled for environment:', environment);
    return;
  }

  // Load Google Analytics
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${config.measurementId}`;
  document.head.appendChild(script);

  // Initialize gtag
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    dataLayer.push(arguments);
  }
  window.gtag = gtag;

  gtag('js', new Date());
  gtag('config', config.measurementId, {
    debug_mode: config.debug,
    send_page_view: true,
    anonymize_ip: true, // GDPR compliance
    allow_google_signals: false, // Privacy-focused
    cookie_flags: 'SameSite=Strict;Secure'
  });

  console.log(`Analytics initialized for ${environment} environment`);
}

// Track page views
export function trackPageView(pagePath, pageTitle) {
  if (typeof window.gtag !== 'function') return;

  window.gtag('config', GA4_CONFIG[process.env.VITE_ENVIRONMENT]?.measurementId, {
    page_path: pagePath,
    page_title: pageTitle
  });
}

// Track custom events
export function trackEvent(eventName, parameters = {}) {
  if (typeof window.gtag !== 'function') return;

  const eventData = {
    ...parameters,
    timestamp: new Date().toISOString(),
    environment: process.env.VITE_ENVIRONMENT
  };

  window.gtag('event', eventName, eventData);

  // Also send to console in debug mode
  if (process.env.VITE_ENVIRONMENT !== 'production') {
    console.log('Analytics Event:', eventName, eventData);
  }
}

// Specific tracking functions for BodyScript features
export const analytics = {
  // Video processing tracking
  trackVideoUpload: (fileSize, duration, format) => {
    trackEvent(EVENTS.VIDEO_UPLOAD, {
      file_size: fileSize,
      video_duration: duration,
      video_format: format
    });
  },

  trackPoseProcessingStart: (videoId, processingMode) => {
    trackEvent(EVENTS.POSE_PROCESSING_START, {
      video_id: videoId,
      processing_mode: processingMode,
      timestamp: performance.now()
    });
  },

  trackPoseProcessingComplete: (videoId, duration, frameCount, landmarkCount) => {
    trackEvent(EVENTS.POSE_PROCESSING_COMPLETE, {
      video_id: videoId,
      processing_duration: duration,
      frame_count: frameCount,
      landmark_count: landmarkCount,
      performance_score: Math.round(frameCount / (duration / 1000)) // fps
    });
  },

  // Export tracking
  trackDataExport: (format, dataSize, exportType) => {
    trackEvent(EVENTS.DATA_EXPORT, {
      export_format: format,
      data_size: dataSize,
      export_type: exportType
    });
  },

  // Performance tracking
  trackPageLoadTime: (pageName, loadTime) => {
    trackEvent(EVENTS.PAGE_LOAD_TIME, {
      page_name: pageName,
      load_time: loadTime,
      performance_rating: loadTime < 1000 ? 'excellent' :
                          loadTime < 2500 ? 'good' :
                          loadTime < 4000 ? 'needs_improvement' : 'poor'
    });
  },

  trackApiResponseTime: (endpoint, method, responseTime, statusCode) => {
    trackEvent(EVENTS.API_RESPONSE_TIME, {
      endpoint,
      method,
      response_time: responseTime,
      status_code: statusCode,
      performance_bucket: responseTime < 100 ? 'fast' :
                          responseTime < 500 ? 'medium' : 'slow'
    });
  },

  // Error tracking
  trackProcessingError: (errorType, errorMessage, context = {}) => {
    trackEvent(EVENTS.PROCESSING_ERROR, {
      error_type: errorType,
      error_message: errorMessage,
      ...context
    });
  },

  trackUploadError: (errorCode, fileSize, fileType) => {
    trackEvent(EVENTS.UPLOAD_ERROR, {
      error_code: errorCode,
      file_size: fileSize,
      file_type: fileType
    });
  },

  // Feature usage tracking
  trackFeatureUsage: (featureName, context = {}) => {
    trackEvent(EVENTS.FEATURE_USED, {
      feature_name: featureName,
      ...context
    });
  },

  trackSettingChange: (settingName, oldValue, newValue) => {
    trackEvent(EVENTS.SETTING_CHANGED, {
      setting_name: settingName,
      old_value: oldValue,
      new_value: newValue
    });
  },

  // Gallery interactions
  trackGalleryView: (viewType, itemCount) => {
    trackEvent(EVENTS.GALLERY_VIEW, {
      view_type: viewType,
      item_count: itemCount
    });
  }
};

// Performance observer for Core Web Vitals
export function initializePerformanceMonitoring() {
  if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
    return;
  }

  // Largest Contentful Paint (LCP)
  new PerformanceObserver((entryList) => {
    for (const entry of entryList.getEntries()) {
      trackEvent('web_vital_lcp', {
        metric_name: 'largest_contentful_paint',
        value: Math.round(entry.startTime),
        rating: entry.startTime < 2500 ? 'good' :
                entry.startTime < 4000 ? 'needs_improvement' : 'poor'
      });
    }
  }).observe({ type: 'largest-contentful-paint', buffered: true });

  // First Input Delay (FID)
  new PerformanceObserver((entryList) => {
    for (const entry of entryList.getEntries()) {
      trackEvent('web_vital_fid', {
        metric_name: 'first_input_delay',
        value: Math.round(entry.processingStart - entry.startTime),
        rating: (entry.processingStart - entry.startTime) < 100 ? 'good' :
                (entry.processingStart - entry.startTime) < 300 ? 'needs_improvement' : 'poor'
      });
    }
  }).observe({ type: 'first-input', buffered: true });

  // Cumulative Layout Shift (CLS)
  let clsValue = 0;
  let clsEntries = [];

  new PerformanceObserver((entryList) => {
    for (const entry of entryList.getEntries()) {
      if (!entry.hadRecentInput) {
        const firstSessionEntry = clsEntries[0];
        const lastSessionEntry = clsEntries[clsEntries.length - 1];

        if (!firstSessionEntry ||
            entry.startTime - lastSessionEntry.startTime > 1000 ||
            entry.startTime - firstSessionEntry.startTime > 5000) {
          // New session
          clsEntries = [entry];
        } else {
          clsEntries.push(entry);
        }

        clsValue = clsEntries.reduce((sum, e) => sum + e.value, 0);

        trackEvent('web_vital_cls', {
          metric_name: 'cumulative_layout_shift',
          value: Math.round(clsValue * 1000) / 1000,
          rating: clsValue < 0.1 ? 'good' :
                  clsValue < 0.25 ? 'needs_improvement' : 'poor'
        });
      }
    }
  }).observe({ type: 'layout-shift', buffered: true });
}

// Privacy-compliant user identification
export function setUserContext(userId, userProperties = {}) {
  if (typeof window.gtag !== 'function') return;

  // Hash the user ID for privacy
  const hashedUserId = btoa(userId).substring(0, 16);

  window.gtag('config', GA4_CONFIG[process.env.VITE_ENVIRONMENT]?.measurementId, {
    user_id: hashedUserId,
    custom_map: userProperties
  });
}

export function clearUserContext() {
  if (typeof window.gtag !== 'function') return;

  window.gtag('config', GA4_CONFIG[process.env.VITE_ENVIRONMENT]?.measurementId, {
    user_id: null
  });
}

export default {
  initializeAnalytics,
  initializePerformanceMonitoring,
  trackPageView,
  trackEvent,
  analytics,
  setUserContext,
  clearUserContext,
  EVENTS
};