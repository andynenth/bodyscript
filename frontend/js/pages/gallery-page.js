// Gallery page controller

import { $, $$, addClass, removeClass, createElement } from '../utils/dom-helpers.js';

// Gallery state
let currentVideos = [];
let allVideos = [];
let activeCategory = null;
let galleryFullyInitialized = false;

/**
 * Render the terminal gallery
 */
function renderTerminalGallery() {
  const grid = $('#videoGrid');
  if (!grid) return;

  grid.innerHTML = '';

  // Render gallery with current videos
  currentVideos.forEach(video => {
    const card = createElement('div', 'terminal-card video-card');
    card.dataset.videoId = video.id;

    // Determine accuracy class
    let accuracyClass = 'accuracy-high';
    if (video.accuracy < 90) accuracyClass = 'accuracy-medium';
    if (video.accuracy < 80) accuracyClass = 'accuracy-low';

    // Add category tag if it exists
    const categoryTag = video.category ?
      `<span class="tag" onclick="filterByCategory('${video.category}')">#${video.category}</span>` : '';

    // Don't create video element initially, just store the preview URL
    card.innerHTML = `
      <div class="video-container ratio-9-16" data-preview="${video.preview}">
        <img class="thumbnail" src="${video.thumbnail}" alt="${video.title}">
        <div class="ascii-play">▶</div>
        <div class="video-name-overlay">${video.title || video.id}</div>
        ${categoryTag ? `<div class="video-category-tag">${categoryTag}</div>` : ''}
      </div>
    `;

    // Store video data on the card for later use
    card.dataset.videoPreview = video.preview;
    card.dataset.videoFull = video.full;
    card.dataset.videoTitle = video.title || video.id;

    grid.appendChild(card);
  });

  // Initialize interactions after render
  setTimeout(() => {
    if (window.GalleryCommon && window.GalleryCommon.initializeHoverPreview) {
      window.GalleryCommon.initializeHoverPreview();
    }
  }, 100);
}

/**
 * Filter videos by category
 */
function filterVideos(filter) {
  // Clear any active category tag filter
  activeCategory = null;
  const activeFilter = $('#activeFilter');
  if (activeFilter) {
    removeClass(activeFilter, 'show');
  }

  // Apply the filter
  if (filter === 'all') {
    currentVideos = [...window.GALLERY_VIDEOS];
  } else {
    currentVideos = window.GALLERY_VIDEOS.filter(v => v.category === filter);
  }

  // Re-render
  renderTerminalGallery();
}

/**
 * Filter by category tag
 */
function filterByCategory(category) {
  activeCategory = category;

  // Create or update active filter display
  let activeFilter = $('#activeFilter');
  if (!activeFilter) {
    activeFilter = createElement('div');
    activeFilter.id = 'activeFilter';
    activeFilter.className = 'active-filter';
    activeFilter.innerHTML = `
      Filtering by: <span id="filterTag"></span>
      <button class="clear-filter" onclick="clearCategoryFilter()">Clear</button>
    `;
    const nav = $('.terminal-nav');
    nav.parentElement.insertBefore(activeFilter, nav.nextSibling);
  }

  $('#filterTag').textContent = `#${category}`;
  addClass(activeFilter, 'show');

  // Filter videos
  currentVideos = window.GALLERY_VIDEOS.filter(video =>
    video.category === category
  );

  // Update nav buttons
  $$('.filter-btn').forEach(btn => {
    removeClass(btn, 'active');
    if (btn.dataset.filter === category) {
      addClass(btn, 'active');
    }
  });

  renderTerminalGallery();
}

/**
 * Clear category filter
 */
function clearCategoryFilter() {
  activeCategory = null;

  const activeFilter = $('#activeFilter');
  if (activeFilter) {
    removeClass(activeFilter, 'show');
  }

  // Restore all videos
  currentVideos = [...window.GALLERY_VIDEOS];

  // Reset nav buttons
  $$('.filter-btn').forEach(btn => {
    removeClass(btn, 'active');
    if (btn.dataset.filter === 'all') {
      addClass(btn, 'active');
    }
  });

  renderTerminalGallery();
}

/**
 * Initialize video modal player
 */
function initializeVideoModal() {
  // Create modal if it doesn't exist
  if (!$('.video-modal')) {
    const modal = createElement('div', 'video-modal');
    modal.innerHTML = `
      <div class="modal-content">
        <button class="modal-close">×</button>
        <video class="modal-video" controls controlsList="nodownload">
          <source src="" type="video/mp4">
        </video>
        <div class="modal-title"></div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  const modal = $('.video-modal');
  const modalVideo = modal.querySelector('.modal-video');
  const modalClose = modal.querySelector('.modal-close');
  const modalTitle = modal.querySelector('.modal-title');

  // Handle clicks on video cards
  document.addEventListener('click', (e) => {
    const card = e.target.closest('.terminal-card');
    if (card && !e.target.closest('button')) {
      const videoId = card.dataset.videoId;
      const video = currentVideos.find(v => v.id == videoId);

      if (video) {
        modalVideo.src = video.full;
        modalTitle.textContent = `> Playing: ${video.title || video.id}`;
        addClass(modal, 'active');
        modalVideo.play();
      }
    }
  });

  // Close modal handlers
  modalClose.addEventListener('click', () => {
    removeClass(modal, 'active');
    modalVideo.pause();
    modalVideo.src = '';
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      removeClass(modal, 'active');
      modalVideo.pause();
      modalVideo.src = '';
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      removeClass(modal, 'active');
      modalVideo.pause();
      modalVideo.src = '';
    }
  });
}

/**
 * Initialize filter buttons
 */
function initializeFilters() {
  $$('.filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const filter = e.target.dataset.filter;

      // Update active state
      $$('.filter-btn').forEach(b => removeClass(b, 'active'));
      addClass(e.target, 'active');

      filterVideos(filter);
    });
  });
}

/**
 * Initialize gallery page
 */
async function initializeGallery() {
  console.log('Initializing gallery...');

  // Initialize video modal
  initializeVideoModal();

  // Initialize filters
  initializeFilters();

  // Check if GalleryCommon exists and override its render function
  if (window.GalleryCommon) {
    window.GalleryCommon.renderGallery = renderTerminalGallery;
  }

  // Expose functions to window for onclick handlers
  window.filterByCategory = filterByCategory;
  window.clearCategoryFilter = clearCategoryFilter;
  window.filterVideos = filterVideos;
  window.currentVideos = currentVideos;

  // Wait for DOM content and gallery data
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadGalleryData);
  } else {
    await loadGalleryData();
  }
}

/**
 * Load gallery data
 */
async function loadGalleryData() {
  try {
    // Check API health
    if (window.checkAPIHealth) {
      await window.checkAPIHealth(true);
    }

    // Load gallery data
    if (window.loadGalleryData) {
      await window.loadGalleryData();

      // Store videos
      currentVideos = window.currentVideos || [];
      allVideos = [...currentVideos];

      // Render gallery
      renderTerminalGallery();

      // Initialize gallery features only once
      if (!galleryFullyInitialized) {
        if (window.GalleryCommon) {
          window.GalleryCommon.initializeFilters();
          window.GalleryCommon.initializeLazyLoading();
          window.GalleryCommon.initializeTouchSupport();
        }
        galleryFullyInitialized = true;
      }
    }
  } catch (error) {
    console.error('Error loading gallery data:', error);
  }
}

// Initialize when module loads
initializeGallery();