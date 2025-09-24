/**
 * GalleryCore - Main orchestrator for gallery functionality
 * Combines all core modules to provide a clean API
 */

import { GalleryDataStore } from './GalleryDataStore.js';
import { FilterManager } from './FilterManager.js';
import { VideoModal } from './VideoModal.js';
import { VideoHoverPreview } from '../components/VideoHoverPreview.js';
import { LazyLoader } from '../utils/LazyLoader.js';
import { TouchHandler } from '../utils/TouchHandler.js';

export class GalleryCore {
  constructor(options = {}) {
    this.options = {
      containerSelector: '#videoGrid',
      cardSelector: '.video-card',
      filterSelector: '.filter-btn',
      enableHoverPreview: true,
      enableLazyLoading: true,
      enableTouchSupport: true,
      renderCallback: null,
      ...options
    };

    // Initialize modules
    this.dataStore = new GalleryDataStore();
    this.filterManager = new FilterManager({
      renderCallback: (videos) => this.render(videos)
    });
    this.videoModal = new VideoModal();
    this.hoverPreview = null;
    this.lazyLoader = null;
    this.touchHandler = null;

    // State
    this.initialized = false;
    this.container = null;
  }

  /**
   * Initialize gallery
   * @returns {Promise<void>}
   */
  async initialize() {
    if (this.initialized) return;

    // Get container
    this.container = document.querySelector(this.options.containerSelector);
    if (!this.container) {
      throw new Error(`Container ${this.options.containerSelector} not found`);
    }

    // Load data
    const videos = await this.dataStore.loadFromAPI();
    this.filterManager.setItems(videos);

    // Register filter buttons
    const filterButtons = document.querySelectorAll(this.options.filterSelector);
    if (filterButtons.length > 0) {
      this.filterManager.registerFilterButtons(filterButtons);
    }

    // Initial render
    this.render(videos);

    // Initialize features
    this._initializeFeatures();

    // Set up event handlers
    this._setupEventHandlers();

    this.initialized = true;
  }

  /**
   * Render videos to gallery
   * @param {Array} videos - Videos to render
   */
  render(videos) {
    if (!this.container) return;

    // Clear container
    this.container.innerHTML = '';

    // Render each video
    videos.forEach(video => {
      const card = this._createVideoCard(video);
      this.container.appendChild(card);
    });

    // Refresh features for new elements
    this._refreshFeatures();

    // Call custom render callback
    if (this.options.renderCallback) {
      this.options.renderCallback(videos);
    }
  }

  /**
   * Create video card element
   * @private
   * @param {Object} video - Video data
   * @returns {HTMLElement} Card element
   */
  _createVideoCard(video) {
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
   * Initialize optional features
   * @private
   */
  _initializeFeatures() {
    // Hover preview
    if (this.options.enableHoverPreview) {
      this.hoverPreview = new VideoHoverPreview({
        selector: this.options.cardSelector
      });
      this.hoverPreview.initialize();
    }

    // Lazy loading
    if (this.options.enableLazyLoading && LazyLoader.isSupported()) {
      this.lazyLoader = new LazyLoader({
        selector: '.thumbnail[loading="lazy"]'
      });

      const images = document.querySelectorAll('.thumbnail[loading="lazy"]');
      this.lazyLoader.observe(images);
    }

    // Touch support
    if (this.options.enableTouchSupport && TouchHandler.isSupported()) {
      this.touchHandler = new TouchHandler();
      this._addTouchSupport();
    }
  }

  /**
   * Refresh features for new elements
   * @private
   */
  _refreshFeatures() {
    // Refresh hover preview
    if (this.hoverPreview) {
      this.hoverPreview.refresh(this.container);
    }

    // Refresh lazy loading
    if (this.lazyLoader) {
      const images = this.container.querySelectorAll('.thumbnail[loading="lazy"]');
      this.lazyLoader.observe(images);
    }

    // Refresh touch support
    if (this.touchHandler) {
      this._addTouchSupport();
    }
  }

  /**
   * Add touch support to cards
   * @private
   */
  _addTouchSupport() {
    const cards = this.container.querySelectorAll(this.options.cardSelector);

    cards.forEach(card => {
      this.touchHandler.addTouchSupport(card, {
        onTap: (e, data) => {
          // Open modal on tap
          const videoId = card.dataset.videoId;
          const video = this.dataStore.getVideoById(videoId);
          if (video) {
            this.videoModal.playVideo(video);
          }
        },
        onLongPress: (e, data) => {
          // Could trigger preview or other action
          console.log('Long press on video', card.dataset.videoTitle);
        }
      });
    });
  }

  /**
   * Set up event handlers
   * @private
   */
  _setupEventHandlers() {
    // Handle card clicks
    this.container.addEventListener('click', (e) => {
      // Handle category tag clicks
      const tag = e.target.closest('.tag');
      if (tag) {
        const category = tag.dataset.category;
        if (category) {
          this.filterManager.filterByCategory(category);
        }
        return;
      }

      // Handle card clicks (open modal)
      const card = e.target.closest(this.options.cardSelector);
      if (card && !e.target.closest('button')) {
        const videoId = card.dataset.videoId;
        const video = this.dataStore.getVideoById(videoId);
        if (video) {
          this.videoModal.playVideo(video);
        }
      }
    });

    // Listen to filter changes
    this.filterManager.on('filterChanged', (data) => {
      console.log('Filter changed:', data.filter);
    });

    // Listen to data store events
    this.dataStore.on('loadingStarted', () => {
      this.showLoading();
    });

    this.dataStore.on('loadingCompleted', () => {
      this.hideLoading();
    });
  }

  /**
   * Show loading state
   */
  showLoading() {
    const loading = document.querySelector('.terminal-loading');
    if (loading) {
      loading.style.display = 'block';
    }
  }

  /**
   * Hide loading state
   */
  hideLoading() {
    const loading = document.querySelector('.terminal-loading');
    if (loading) {
      loading.style.display = 'none';
    }
  }

  /**
   * Filter videos
   * @param {string} filter - Filter to apply
   */
  filter(filter) {
    this.filterManager.filterBy(filter);
  }

  /**
   * Search videos
   * @param {string} query - Search query
   */
  search(query) {
    this.filterManager.search(query);
  }

  /**
   * Sort videos
   * @param {string} field - Field to sort by
   * @param {string} order - Sort order (asc/desc)
   */
  sort(field, order = 'asc') {
    this.filterManager.sortItems(field, order);
  }

  /**
   * Reload gallery data
   * @returns {Promise<void>}
   */
  async reload() {
    const videos = await this.dataStore.loadFromAPI();
    this.filterManager.setItems(videos);
    this.render(videos);
  }

  /**
   * Get current videos
   * @returns {Array}
   */
  getVideos() {
    return this.filterManager.getFilteredItems();
  }

  /**
   * Get all videos
   * @returns {Array}
   */
  getAllVideos() {
    return this.dataStore.getVideos();
  }

  /**
   * Open video in modal
   * @param {number|string} videoId - Video ID
   */
  openVideo(videoId) {
    const video = this.dataStore.getVideoById(videoId);
    if (video) {
      this.videoModal.playVideo(video);
    }
  }

  /**
   * Close video modal
   */
  closeVideo() {
    this.videoModal.close();
  }

  /**
   * Destroy gallery and clean up
   */
  destroy() {
    // Clean up features
    if (this.hoverPreview) {
      this.hoverPreview.destroy();
    }

    if (this.lazyLoader) {
      this.lazyLoader.destroy();
    }

    if (this.touchHandler) {
      this.touchHandler.destroy();
    }

    // Clean up modules
    this.filterManager.destroy();
    this.videoModal.destroy();
    this.dataStore.clear();

    // Clear container
    if (this.container) {
      this.container.innerHTML = '';
    }

    this.initialized = false;
  }

  /**
   * Enable/disable features
   */
  enableHoverPreview(enabled = true) {
    this.options.enableHoverPreview = enabled;
    if (enabled && !this.hoverPreview) {
      this._initializeFeatures();
    } else if (!enabled && this.hoverPreview) {
      this.hoverPreview.destroy();
      this.hoverPreview = null;
    }
  }

  enableLazyLoading(enabled = true) {
    this.options.enableLazyLoading = enabled;
    if (enabled && !this.lazyLoader) {
      this._initializeFeatures();
    } else if (!enabled && this.lazyLoader) {
      this.lazyLoader.destroy();
      this.lazyLoader = null;
    }
  }

  enableTouchSupport(enabled = true) {
    this.options.enableTouchSupport = enabled;
    if (enabled && !this.touchHandler) {
      this._initializeFeatures();
    } else if (!enabled && this.touchHandler) {
      this.touchHandler.destroy();
      this.touchHandler = null;
    }
  }
}

// Export utility function for number formatting
export function formatNumber(num) {
  if (typeof num === 'string') return num;

  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k';
  }
  return num.toString();
}