/**
 * VideoModal - Video-specific modal extending base Modal
 * Handles video playback in a modal window with controls
 */

import { Modal } from './Modal.js';
import { VideoPlayer } from './VideoPlayer.js';

export class VideoModal extends Modal {
  constructor(options = {}) {
    super({
      className: 'video-modal',
      ...options
    });

    this.videoPlayer = new VideoPlayer({
      muted: false,  // Allow sound in modal
      loop: false,   // Don't loop in modal
      controls: true // Show controls
    });

    this.videoElement = null;
    this.videoTitle = null;
    this.currentVideo = null;
  }

  /**
   * Create video modal content
   * @private
   */
  _createVideoContent() {
    // Create video element
    this.videoElement = document.createElement('video');
    this.videoElement.className = 'modal-video';
    this.videoElement.controls = true;
    this.videoElement.controlsList = 'nodownload';

    // Create source element
    const source = document.createElement('source');
    source.type = 'video/mp4';
    this.videoElement.appendChild(source);

    // Create title element
    this.videoTitle = document.createElement('div');
    this.videoTitle.className = 'modal-title';

    // Set content
    const content = document.createElement('div');
    content.className = 'modal-content';
    content.appendChild(this.videoElement);
    content.appendChild(this.videoTitle);

    this.setContent(content);
  }

  /**
   * Play video in modal
   * @param {Object} videoData - Video data object
   * @param {string} videoData.src - Video source URL
   * @param {string} [videoData.title] - Video title
   * @param {string} [videoData.thumbnail] - Thumbnail URL
   */
  playVideo(videoData) {
    if (!this.videoElement) {
      this._createVideoContent();
    }

    this.currentVideo = videoData;

    // Set video source
    const source = this.videoElement.querySelector('source');
    source.src = this._resolveVideoUrl(videoData.src || videoData.full);

    // Set title
    if (this.videoTitle && videoData.title) {
      this.videoTitle.textContent = `> Playing: ${videoData.title}`;
    }

    // Open modal
    this.open();

    // Play video
    this.videoElement.load();
    this.videoElement.play().catch(error => {
      console.error('Failed to play video:', error);
    });
  }

  /**
   * Open modal with video
   * @param {Object|string} content - Video data or content
   */
  open(content) {
    // If content is video data, play it
    if (content && typeof content === 'object' && (content.src || content.full)) {
      this.playVideo(content);
      return;
    }

    super.open(content);
  }

  /**
   * Close modal and stop video
   */
  close() {
    // Pause video
    if (this.videoElement) {
      this.videoElement.pause();
      this.videoElement.currentTime = 0;

      // Clear source to free resources
      const source = this.videoElement.querySelector('source');
      if (source) {
        source.src = '';
      }
    }

    // Clear current video
    this.currentVideo = null;

    super.close();
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

    // For relative URLs starting with /
    if (url.startsWith('/') && !url.startsWith('//')) {
      return `${window.API_URL || ''}${url}`;
    }

    return url;
  }

  /**
   * Get current video data
   * @returns {Object|null}
   */
  getCurrentVideo() {
    return this.currentVideo;
  }

  /**
   * Set video title
   * @param {string} title - Title text
   */
  setTitle(title) {
    if (this.videoTitle) {
      this.videoTitle.textContent = title;
    }
  }

  /**
   * Toggle play/pause
   */
  togglePlayPause() {
    if (!this.videoElement) return;

    if (this.videoElement.paused) {
      this.videoElement.play();
    } else {
      this.videoElement.pause();
    }
  }

  /**
   * Check if video is playing
   * @returns {boolean}
   */
  isPlaying() {
    return this.videoElement && !this.videoElement.paused && !this.videoElement.ended;
  }

  /**
   * Set video volume
   * @param {number} volume - Volume level (0-1)
   */
  setVolume(volume) {
    if (this.videoElement) {
      this.videoElement.volume = Math.max(0, Math.min(1, volume));
    }
  }

  /**
   * Mute/unmute video
   * @param {boolean} [muted] - Mute state
   */
  toggleMute(muted) {
    if (this.videoElement) {
      this.videoElement.muted = muted !== undefined ? muted : !this.videoElement.muted;
    }
  }

  /**
   * Seek to time
   * @param {number} time - Time in seconds
   */
  seekTo(time) {
    if (this.videoElement) {
      this.videoElement.currentTime = time;
    }
  }

  /**
   * Get video element
   * @returns {HTMLVideoElement|null}
   */
  getVideoElement() {
    return this.videoElement;
  }

  /**
   * Destroy modal and clean up
   */
  destroy() {
    // Clean up video
    if (this.videoElement) {
      this.videoElement.pause();
      this.videoElement.src = '';
    }

    // Clean up video player
    this.videoPlayer.destroy();

    // Call parent destroy
    super.destroy();

    // Clear references
    this.videoElement = null;
    this.videoTitle = null;
    this.currentVideo = null;
  }
}