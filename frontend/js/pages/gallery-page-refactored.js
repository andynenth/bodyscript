/**
 * Gallery Page Controller - Refactored Version
 * Uses new modular architecture instead of duplicating functionality
 */

import { GalleryCore } from '../core/GalleryCore.js';
import { $, $$, addClass, removeClass } from '../utils/dom-helpers.js';

// Create gallery instance
const gallery = new GalleryCore({
  containerSelector: '#videoGrid',
  cardSelector: '.terminal-card',
  filterSelector: '.terminal-filter',
  enableHoverPreview: true,
  enableLazyLoading: true,
  enableTouchSupport: true,
  renderCallback: renderTerminalGallery
});

/**
 * Custom render function for terminal-style gallery
 * This is the ONLY page-specific logic we need to keep
 */
function renderTerminalGallery(videos) {
  const grid = $('#videoGrid');
  if (!grid) return;

  grid.innerHTML = '';

  // Render gallery with terminal-specific styling
  videos.forEach(video => {
    const card = createTerminalCard(video);
    grid.appendChild(card);
  });

  // Refresh gallery features for new elements
  gallery._refreshFeatures();
}

/**
 * Create terminal-style video card
 * @param {Object} video - Video data
 * @returns {HTMLElement} Card element
 */
function createTerminalCard(video) {
  const card = document.createElement('div');
  card.className = 'terminal-card video-card';
  card.dataset.videoId = video.id;
  card.dataset.videoPreview = video.preview;
  card.dataset.videoFull = video.full;
  card.dataset.videoTitle = video.title || video.id;

  // Determine accuracy class
  let accuracyClass = 'accuracy-high';
  if (video.accuracy < 90) accuracyClass = 'accuracy-medium';
  if (video.accuracy < 80) accuracyClass = 'accuracy-low';

  // Add category tag if it exists
  const categoryTag = video.category ?
    `<span class="tag" data-category="${video.category}">#${video.category}</span>` : '';

  card.innerHTML = `
    <div class="video-container ratio-9-16" data-preview="${video.preview}">
      <img class="thumbnail"
           src="${video.thumbnail}"
           alt="${video.title}"
           loading="lazy">
      <div class="ascii-play">▶</div>
      <div class="video-name-overlay">${video.title || video.id}</div>
      ${categoryTag ? `<div class="video-category-tag">${categoryTag}</div>` : ''}
    </div>
  `;

  return card;
}

/**
 * Initialize gallery page
 */
async function initializePage() {
  console.log('Initializing refactored gallery page...');

  try {
    // Check API health if available
    if (window.checkAPIHealth) {
      await window.checkAPIHealth(true);
    }

    // Initialize gallery
    await gallery.initialize();

    // Expose functions to window for onclick handlers in HTML
    window.filterByCategory = (category) => gallery.filterManager.filterByCategory(category);
    window.clearCategoryFilter = () => gallery.filterManager.clearFilter();
    window.filterVideos = (filter) => gallery.filter(filter);

    console.log('Gallery page initialized successfully');
  } catch (error) {
    console.error('Failed to initialize gallery:', error);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePage);
} else {
  initializePage();
}

// Export for potential use in other modules
export { gallery, renderTerminalGallery };