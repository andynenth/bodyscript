/**
 * Gallery Common Adapter - Backward compatibility layer
 * Maps old gallery-common.js API to new modular system
 *
 * DEPRECATION NOTICE: This adapter provides backward compatibility for legacy code.
 * Please migrate to the new modular API (GalleryCore) as soon as possible.
 */

import { GalleryCore } from '../core/GalleryCore.js';

// Create global instance
const galleryCore = new GalleryCore({
  containerSelector: '#videoGrid',
  cardSelector: '.video-card',
  filterSelector: '.filter-btn',
  renderCallback: () => {
    // Call legacy renderGallery if it exists
    if (typeof window.renderGallery === 'function') {
      window.renderGallery();
    }
  }
});

// Legacy global variables (deprecated)
window.GALLERY_VIDEOS = [];
window.currentVideos = [];
window.currentFilter = 'all';
window.galleryInitialized = false;

/**
 * Initialize hover preview (legacy)
 * @deprecated Use GalleryCore.enableHoverPreview()
 */
function initializeHoverPreview() {
  console.warn('[DEPRECATED] initializeHoverPreview() is deprecated. Use GalleryCore methods.');

  if (!galleryCore.hoverPreview) {
    galleryCore.enableHoverPreview(true);
  }
}

/**
 * Initialize full screen player (legacy)
 * @deprecated Modal is automatically initialized in GalleryCore
 */
function initializeFullScreenPlayer() {
  console.warn('[DEPRECATED] initializeFullScreenPlayer() is deprecated. Modal is auto-initialized.');
  // No-op - modal is already initialized in GalleryCore
}

/**
 * Initialize filters (legacy)
 * @deprecated Filters are automatically initialized in GalleryCore
 */
function initializeFilters() {
  console.warn('[DEPRECATED] initializeFilters() is deprecated. Filters are auto-initialized.');
  // No-op - filters are already initialized in GalleryCore
}

/**
 * Filter videos (legacy)
 * @deprecated Use GalleryCore.filter()
 */
function filterVideos(filter) {
  console.warn('[DEPRECATED] filterVideos() is deprecated. Use GalleryCore.filter().');

  window.currentFilter = filter;
  galleryCore.filter(filter);

  // Update legacy variables
  window.currentVideos = galleryCore.getVideos();
}

/**
 * Load gallery data (legacy)
 * @deprecated Use GalleryCore.initialize()
 */
async function loadGalleryData() {
  console.warn('[DEPRECATED] loadGalleryData() is deprecated. Use GalleryCore.initialize().');

  try {
    await galleryCore.initialize();

    // Update legacy variables
    window.GALLERY_VIDEOS = galleryCore.getAllVideos();
    window.currentVideos = galleryCore.getVideos();

    return window.GALLERY_VIDEOS;
  } catch (error) {
    console.error('Failed to load gallery data:', error);

    // Fall back to sample data
    const sampleData = galleryCore.dataStore.getSampleData();
    window.GALLERY_VIDEOS = sampleData;
    window.currentVideos = sampleData;

    return sampleData;
  }
}

/**
 * Render gallery (legacy)
 * @deprecated Override this in your page-specific code
 */
function renderGallery() {
  console.warn('[DEPRECATED] renderGallery() is deprecated. Override in page-specific code.');

  // This should be overridden by page-specific implementation
  console.log('Rendering gallery with', window.currentVideos.length, 'videos');
}

/**
 * Initialize lazy loading (legacy)
 * @deprecated Lazy loading is automatically initialized in GalleryCore
 */
function initializeLazyLoading() {
  console.warn('[DEPRECATED] initializeLazyLoading() is deprecated. Auto-initialized.');

  if (!galleryCore.lazyLoader) {
    galleryCore.enableLazyLoading(true);
  }
}

/**
 * Initialize touch support (legacy)
 * @deprecated Touch support is automatically initialized in GalleryCore
 */
function initializeTouchSupport() {
  console.warn('[DEPRECATED] initializeTouchSupport() is deprecated. Auto-initialized.');

  if (!galleryCore.touchHandler) {
    galleryCore.enableTouchSupport(true);
  }
}

/**
 * Format number (legacy)
 * @deprecated Import formatNumber from GalleryCore
 */
function formatNumber(num) {
  if (typeof num === 'string') return num;

  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k';
  }
  return num.toString();
}

/**
 * Initialize gallery (legacy)
 * @deprecated Use GalleryCore.initialize()
 */
function initializeGallery() {
  console.warn('[DEPRECATED] initializeGallery() is deprecated. Use GalleryCore.initialize().');

  // Mark as initialized
  window.galleryInitialized = true;

  // Initialize all features (now handled by GalleryCore)
  initializeHoverPreview();
  initializeFullScreenPlayer();
  initializeFilters();
  initializeLazyLoading();
  initializeTouchSupport();
}

// Export legacy API for backward compatibility
window.GalleryCommon = {
  SAMPLE_VIDEOS: galleryCore.dataStore.getSampleData(),
  currentVideos: window.currentVideos,
  formatNumber,
  filterVideos,
  renderGallery,
  initializeGallery,
  initializeHoverPreview,
  initializeFilters,
  initializeLazyLoading,
  initializeTouchSupport
};

// Also expose individual functions to window
window.loadGalleryData = loadGalleryData;
window.filterVideos = filterVideos;
window.renderGallery = renderGallery;
window.formatNumber = formatNumber;
window.initializeGallery = initializeGallery;

// Auto-initialize on DOM ready (legacy behavior)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.info('[Gallery] Using legacy adapter. Please migrate to GalleryCore for better performance.');
  });
} else {
  console.info('[Gallery] Using legacy adapter. Please migrate to GalleryCore for better performance.');
}

// Export for module usage
export {
  galleryCore,
  initializeGallery,
  initializeHoverPreview,
  initializeFullScreenPlayer,
  initializeFilters,
  filterVideos,
  loadGalleryData,
  renderGallery,
  initializeLazyLoading,
  initializeTouchSupport,
  formatNumber
};