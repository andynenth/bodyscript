/**
 * VideoPlayer - Core video playback functionality
 * Handles video element creation, playback controls, and lifecycle management
 */

export class VideoPlayer {
  constructor(options = {}) {
    this.options = {
      muted: true,
      loop: true,
      playsInline: true,
      preload: 'auto',
      ...options
    };

    this.video = null;
    this.source = null;
    this.container = null;
    this.isCreating = false;
    this.listeners = new Map();
  }

  /**
   * Create video element on demand
   * @param {string} src - Video source URL
   * @param {HTMLElement} container - Container element
   * @returns {Promise<HTMLVideoElement>}
   */
  async createPreviewElement(src, container) {
    if (this.video || this.isCreating) {
      return this.video;
    }

    this.isCreating = true;
    this.container = container;

    try {
      // Create video element
      this.video = document.createElement('video');
      this.video.className = 'preview-video';

      // Apply options
      Object.assign(this.video, this.options);

      // Set styles
      Object.assign(this.video.style, {
        display: 'none',
        position: 'absolute',
        top: '0',
        left: '0',
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        zIndex: '10'
      });

      // Create source element
      this.source = document.createElement('source');
      this.source.src = this._resolveVideoUrl(src);
      this.source.type = 'video/mp4';
      this.video.appendChild(this.source);

      // Add to container
      container.appendChild(this.video);

      // Wait for video to be ready
      await this._waitForCanPlay();

      this.isCreating = false;
      return this.video;
    } catch (error) {
      console.error('Failed to create video element:', error);
      this.isCreating = false;
      this.destroy();
      throw error;
    }
  }

  /**
   * Play video with error handling
   * @returns {Promise<void>}
   */
  async play() {
    if (!this.video) {
      throw new Error('Video element not created');
    }

    try {
      this.video.style.display = 'block';
      this.video.currentTime = 0;
      await this.video.play();
    } catch (error) {
      console.error('Failed to play video:', error);
      this.video.style.display = 'none';
      throw error;
    }
  }

  /**
   * Pause video and reset
   */
  pause() {
    if (!this.video) return;

    this.video.pause();
    this.video.currentTime = 0;
    this.video.style.display = 'none';
  }

  /**
   * Show video element without playing
   */
  show() {
    if (this.video) {
      this.video.style.display = 'block';
    }
  }

  /**
   * Hide video element
   */
  hide() {
    if (this.video) {
      this.video.style.display = 'none';
    }
  }

  /**
   * Set video source
   * @param {string} src - Video source URL
   */
  setSrc(src) {
    if (!this.video || !this.source) return;

    this.source.src = this._resolveVideoUrl(src);
    this.video.load();
  }

  /**
   * Add event listener with tracking
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  on(event, handler) {
    if (!this.video) return;

    this.video.addEventListener(event, handler);

    // Track listeners for cleanup
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(handler);
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  off(event, handler) {
    if (!this.video) return;

    this.video.removeEventListener(event, handler);

    // Remove from tracking
    if (this.listeners.has(event)) {
      const handlers = this.listeners.get(event);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Clean up and destroy video element
   */
  destroy() {
    // Pause and reset
    this.pause();

    // Remove all event listeners
    this.listeners.forEach((handlers, event) => {
      handlers.forEach(handler => {
        this.video?.removeEventListener(event, handler);
      });
    });
    this.listeners.clear();

    // Remove from DOM
    if (this.video) {
      this.video.remove();
      this.video = null;
    }

    this.source = null;
    this.container = null;
    this.isCreating = false;
  }

  /**
   * Resolve video URL with API prefix if needed
   * @private
   * @param {string} url - Video URL
   * @returns {string} Resolved URL
   */
  _resolveVideoUrl(url) {
    if (!url) return '';

    // Check if URL needs API_URL prefix
    if (url.startsWith('/api/')) {
      return `${window.API_URL || 'http://localhost:8000'}${url}`;
    }

    return url;
  }

  /**
   * Wait for video to be ready to play
   * @private
   * @returns {Promise<void>}
   */
  _waitForCanPlay() {
    return new Promise((resolve, reject) => {
      if (!this.video) {
        reject(new Error('No video element'));
        return;
      }

      const handleCanPlay = () => {
        this.video.removeEventListener('canplay', handleCanPlay);
        this.video.removeEventListener('error', handleError);
        resolve();
      };

      const handleError = (error) => {
        this.video.removeEventListener('canplay', handleCanPlay);
        this.video.removeEventListener('error', handleError);
        reject(error);
      };

      this.video.addEventListener('canplay', handleCanPlay, { once: true });
      this.video.addEventListener('error', handleError, { once: true });

      // Load the video
      this.video.load();
    });
  }

  /**
   * Get video element
   * @returns {HTMLVideoElement|null}
   */
  getElement() {
    return this.video;
  }

  /**
   * Check if video is playing
   * @returns {boolean}
   */
  isPlaying() {
    return this.video && !this.video.paused && !this.video.ended;
  }

  /**
   * Get video duration
   * @returns {number}
   */
  getDuration() {
    return this.video?.duration || 0;
  }

  /**
   * Get current playback time
   * @returns {number}
   */
  getCurrentTime() {
    return this.video?.currentTime || 0;
  }

  /**
   * Set current playback time
   * @param {number} time - Time in seconds
   */
  setCurrentTime(time) {
    if (this.video) {
      this.video.currentTime = time;
    }
  }
}