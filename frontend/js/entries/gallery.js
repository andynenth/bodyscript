/**
 * Gallery Page Entry Point
 *
 * This is the main entry point for the gallery page.
 * It imports the main application features and the gallery-specific functionality.
 */

// Import global application setup
import '../main.js';

// Import gallery-specific CSS
import '@css/pages/gallery.css';

// Import the existing gallery functionality
// This will work with both the refactored modules and the legacy system
import '../pages/gallery-page.js';

// Import gallery components that should be available
import '@components/VideoHoverPreview.js';
import '@utils/LazyLoader.js';
import '@utils/TouchHandler.js';

// Gallery-specific initialization
document.addEventListener('DOMContentLoaded', () => {
  window.BodyScript.utils.log('Gallery page loaded');

  // Emit gallery-ready event for other modules
  window.BodyScript.events.emit('gallery-ready');

  // Set up gallery-specific features
  setupGalleryFeatures();
});

/**
 * Set up gallery-specific features
 */
function setupGalleryFeatures() {
  // Performance monitoring for gallery
  if (window.BodyScript.config.debug) {
    monitorGalleryPerformance();
  }

  // Gallery keyboard shortcuts
  setupKeyboardShortcuts();

  // Gallery accessibility features
  setupAccessibility();
}

/**
 * Monitor gallery performance
 */
function monitorGalleryPerformance() {
  // Track video load times
  const videoElements = document.querySelectorAll('video');
  videoElements.forEach((video, index) => {
    video.addEventListener('loadstart', () => {
      window.BodyScript.utils.log(`Video ${index} load started`);
    });

    video.addEventListener('canplaythrough', () => {
      window.BodyScript.utils.log(`Video ${index} ready to play`);
    });
  });

  // Track filter performance
  window.BodyScript.events.on('filter-applied', (data) => {
    window.BodyScript.utils.log('Filter applied:', data);
  });
}

/**
 * Setup keyboard shortcuts for gallery
 */
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Only handle if not typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
      return;
    }

    switch (e.key) {
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
        // Quick filter selection (1=all, 2=dance, 3=sports, 4=yoga, 5=martial)
        const filters = ['all', 'dance', 'sports', 'yoga', 'martial'];
        const filterIndex = parseInt(e.key) - 1;
        if (filters[filterIndex] && window.filterVideos) {
          window.filterVideos(filters[filterIndex]);
          e.preventDefault();
        }
        break;

      case 'Escape':
        // Close any open modals or reset to all filter
        if (window.filterVideos) {
          window.filterVideos('all');
        }
        break;

      case 'r':
      case 'R':
        // Refresh gallery
        if (e.ctrlKey || e.metaKey) {
          location.reload();
        }
        break;
    }
  });
}

/**
 * Setup accessibility features
 */
function setupAccessibility() {
  // Announce filter changes to screen readers
  window.BodyScript.events.on('filter-applied', (data) => {
    announceToScreenReader(`Filtered to show ${data.count} ${data.filter} videos`);
  });

  // Add ARIA labels to dynamically created elements
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          enhanceAccessibility(node);
        }
      });
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

/**
 * Announce text to screen readers
 */
function announceToScreenReader(text) {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.textContent = text;

  document.body.appendChild(announcement);

  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}

/**
 * Enhance accessibility for dynamically added elements
 */
function enhanceAccessibility(element) {
  // Add ARIA labels to video cards
  if (element.classList?.contains('video-card')) {
    const title = element.querySelector('.video-name-overlay')?.textContent;
    if (title) {
      element.setAttribute('aria-label', `Play video: ${title}`);
      element.setAttribute('role', 'button');
    }
  }

  // Add ARIA labels to filter buttons
  if (element.classList?.contains('filter-btn')) {
    const filter = element.dataset.filter;
    if (filter) {
      element.setAttribute('aria-label', `Filter by ${filter}`);
    }
  }
}