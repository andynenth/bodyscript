/**
 * VideoHoverPreview - Hover-to-preview video functionality
 * Manages video preview on hover with lazy loading and resource cleanup
 */

import { VideoPlayer } from '../core/VideoPlayer.js';

export class VideoHoverPreview {
  constructor(options = {}) {
    this.options = {
      hoverDelay: 500,        // Delay before preview starts (ms)
      previewDuration: 3000,  // How long to play preview (ms)
      selector: '.video-card', // Card selector
      containerSelector: '.video-container', // Container within card
      thumbnailSelector: '.thumbnail', // Thumbnail selector
      previewAttr: 'data-video-preview', // Attribute with preview URL
      cleanupDelay: 1000,    // Delay before cleanup after hover ends
      ...options
    };

    this.previewInstances = new Map();
    this.activePreview = null;
  }

  /**
   * Initialize hover preview for all cards
   */
  initialize() {
    const cards = document.querySelectorAll(this.options.selector);
    cards.forEach(card => this.initializeCard(card));
  }

  /**
   * Initialize hover preview for a single card
   * @param {HTMLElement} card - Video card element
   */
  initializeCard(card) {
    const container = card.querySelector(this.options.containerSelector);
    const thumbnail = card.querySelector(this.options.thumbnailSelector);

    if (!container) return;

    // Skip if already initialized
    if (container.dataset.hoverInitialized === 'true') {
      return;
    }

    // Get preview URL from card or container
    const previewUrl = card.dataset.videoPreview || container.dataset.preview;
    if (!previewUrl) return;

    // Create preview instance
    const previewInstance = {
      card,
      container,
      thumbnail,
      previewUrl,
      videoPlayer: null,
      hoverTimeout: null,
      playbackTimeout: null,
      cleanupTimeout: null,
      isHovering: false
    };

    // Store instance
    this.previewInstances.set(card, previewInstance);

    // Add event listeners
    container.addEventListener('mouseenter', () => this._handleMouseEnter(previewInstance));
    container.addEventListener('mouseleave', () => this._handleMouseLeave(previewInstance));

    // Add touch support
    if ('ontouchstart' in window) {
      this._addTouchSupport(previewInstance);
    }

    // Mark as initialized
    container.dataset.hoverInitialized = 'true';
  }

  /**
   * Handle mouse enter
   * @private
   * @param {Object} instance - Preview instance
   */
  _handleMouseEnter(instance) {
    instance.isHovering = true;

    // Clear any pending cleanup
    clearTimeout(instance.cleanupTimeout);

    // Start preview after delay
    instance.hoverTimeout = setTimeout(async () => {
      if (!instance.isHovering) return;

      await this._startPreview(instance);
    }, this.options.hoverDelay);
  }

  /**
   * Handle mouse leave
   * @private
   * @param {Object} instance - Preview instance
   */
  _handleMouseLeave(instance) {
    instance.isHovering = false;

    // Clear timeouts
    clearTimeout(instance.hoverTimeout);
    clearTimeout(instance.playbackTimeout);

    // Stop preview
    this._stopPreview(instance);

    // Schedule cleanup
    instance.cleanupTimeout = setTimeout(() => {
      if (!instance.isHovering) {
        this._cleanupPreview(instance);
      }
    }, this.options.cleanupDelay);
  }

  /**
   * Start video preview
   * @private
   * @param {Object} instance - Preview instance
   */
  async _startPreview(instance) {
    try {
      // Create video player if needed
      if (!instance.videoPlayer) {
        instance.videoPlayer = new VideoPlayer({
          muted: true,
          loop: true,
          playsInline: true
        });

        await instance.videoPlayer.createPreviewElement(
          instance.previewUrl,
          instance.container
        );
      }

      // Hide thumbnail and show video
      if (instance.thumbnail) {
        instance.thumbnail.style.display = 'none';
      }

      await instance.videoPlayer.play();

      // Set active preview
      this.activePreview = instance;

      // Stop after duration
      instance.playbackTimeout = setTimeout(() => {
        if (instance.videoPlayer) {
          instance.videoPlayer.pause();
        }
      }, this.options.previewDuration);

      // Emit event
      this._emit('previewStarted', instance);

    } catch (error) {
      console.error('Failed to start preview:', error);
      this._showThumbnail(instance);
    }
  }

  /**
   * Stop video preview
   * @private
   * @param {Object} instance - Preview instance
   */
  _stopPreview(instance) {
    if (instance.videoPlayer) {
      instance.videoPlayer.pause();
    }

    this._showThumbnail(instance);

    // Clear active preview
    if (this.activePreview === instance) {
      this.activePreview = null;
    }

    // Emit event
    this._emit('previewStopped', instance);
  }

  /**
   * Clean up preview resources
   * @private
   * @param {Object} instance - Preview instance
   */
  _cleanupPreview(instance) {
    if (instance.videoPlayer && !instance.isHovering) {
      instance.videoPlayer.destroy();
      instance.videoPlayer = null;

      // Emit event
      this._emit('previewCleaned', instance);
    }
  }

  /**
   * Show thumbnail
   * @private
   * @param {Object} instance - Preview instance
   */
  _showThumbnail(instance) {
    if (instance.thumbnail) {
      instance.thumbnail.style.display = 'block';
    }
  }

  /**
   * Add touch support
   * @private
   * @param {Object} instance - Preview instance
   */
  _addTouchSupport(instance) {
    let touchTimer;
    const { card } = instance;

    card.addEventListener('touchstart', (e) => {
      touchTimer = setTimeout(() => {
        this._startPreview(instance);
      }, this.options.hoverDelay);
    }, { passive: true });

    card.addEventListener('touchend', () => {
      clearTimeout(touchTimer);
      this._stopPreview(instance);

      // Clean up after delay
      setTimeout(() => {
        this._cleanupPreview(instance);
      }, this.options.cleanupDelay);
    }, { passive: true });

    card.addEventListener('touchcancel', () => {
      clearTimeout(touchTimer);
      this._stopPreview(instance);
    }, { passive: true });
  }

  /**
   * Refresh hover preview for new cards
   * @param {HTMLElement} [container] - Container to search within
   */
  refresh(container = document) {
    const cards = container.querySelectorAll(this.options.selector);
    cards.forEach(card => {
      if (!this.previewInstances.has(card)) {
        this.initializeCard(card);
      }
    });
  }

  /**
   * Stop all active previews
   */
  stopAll() {
    this.previewInstances.forEach(instance => {
      this._stopPreview(instance);
      this._cleanupPreview(instance);
    });
  }

  /**
   * Destroy and clean up
   */
  destroy() {
    // Stop all previews
    this.stopAll();

    // Clear all instances
    this.previewInstances.forEach(instance => {
      // Clear timeouts
      clearTimeout(instance.hoverTimeout);
      clearTimeout(instance.playbackTimeout);
      clearTimeout(instance.cleanupTimeout);

      // Destroy video player
      if (instance.videoPlayer) {
        instance.videoPlayer.destroy();
      }

      // Remove data attribute
      if (instance.container) {
        delete instance.container.dataset.hoverInitialized;
      }
    });

    // Clear map
    this.previewInstances.clear();
    this.activePreview = null;
  }

  /**
   * Get active preview instance
   * @returns {Object|null}
   */
  getActivePreview() {
    return this.activePreview;
  }

  /**
   * Set option
   * @param {string} key - Option key
   * @param {*} value - Option value
   */
  setOption(key, value) {
    if (key in this.options) {
      this.options[key] = value;
    }
  }

  /**
   * Event handling (simplified)
   * @private
   */
  _emit(event, data) {
    // Could be extended with proper event emitter
    if (window.dispatchEvent) {
      window.dispatchEvent(new CustomEvent(`videohoverpreview:${event}`, { detail: data }));
    }
  }
}