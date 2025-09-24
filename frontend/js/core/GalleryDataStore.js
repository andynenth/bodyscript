/**
 * GalleryDataStore - Centralized data management for gallery videos
 * Handles data loading from API, caching, and fallback to sample data
 */

export class GalleryDataStore {
  constructor(options = {}) {
    this.options = {
      apiUrl: window.API_URL || 'http://localhost:8000',
      cacheTimeout: 5 * 60 * 1000, // 5 minutes
      useSampleData: true,
      ...options
    };

    this.videos = [];
    this.cache = null;
    this.cacheTimestamp = null;
    this.loading = false;
    this.listeners = new Map();
  }

  /**
   * Load videos from API or cache
   * @returns {Promise<Array>} Array of videos
   */
  async loadFromAPI() {
    // Return cached data if still valid
    if (this._isCacheValid()) {
      return this.cache;
    }

    // Prevent multiple simultaneous loads
    if (this.loading) {
      return this.videos;
    }

    this.loading = true;
    this._emit('loadingStarted');

    try {
      // Only try API on localhost
      if (this._isLocalhost()) {
        const response = await fetch(`${this.options.apiUrl}/api/gallery`);

        if (response.ok) {
          const data = await response.json();

          if (data.videos && data.videos.length > 0) {
            // Fix URLs to use backend API URL
            this.videos = data.videos.map(video => this._normalizeVideo(video));

            // Update cache
            this._updateCache(this.videos);

            this.loading = false;
            this._emit('loadingCompleted', this.videos);
            return this.videos;
          }
        }
      }
    } catch (error) {
      console.log('Could not load gallery from API:', error);
      this._emit('loadingError', error);
    }

    // Fall back to sample data
    if (this.options.useSampleData) {
      this.videos = this.getSampleData();
      this._updateCache(this.videos);
    }

    this.loading = false;
    this._emit('loadingCompleted', this.videos);
    return this.videos;
  }

  /**
   * Get videos (from cache or empty array)
   * @returns {Array} Array of videos
   */
  getVideos() {
    return [...this.videos];
  }

  /**
   * Get single video by ID
   * @param {number|string} id - Video ID
   * @returns {Object|null} Video object or null
   */
  getVideoById(id) {
    return this.videos.find(v => v.id == id) || null;
  }

  /**
   * Get videos by category
   * @param {string} category - Category name
   * @returns {Array} Filtered videos
   */
  getVideosByCategory(category) {
    if (category === 'all') {
      return [...this.videos];
    }
    return this.videos.filter(v => v.category === category);
  }

  /**
   * Add video to store
   * @param {Object} video - Video object
   */
  addVideo(video) {
    const normalized = this._normalizeVideo(video);
    this.videos.push(normalized);
    this._updateCache(this.videos);
    this._emit('videoAdded', normalized);
  }

  /**
   * Update video in store
   * @param {number|string} id - Video ID
   * @param {Object} updates - Updates to apply
   */
  updateVideo(id, updates) {
    const index = this.videos.findIndex(v => v.id == id);
    if (index > -1) {
      this.videos[index] = {
        ...this.videos[index],
        ...updates
      };
      this._updateCache(this.videos);
      this._emit('videoUpdated', this.videos[index]);
    }
  }

  /**
   * Remove video from store
   * @param {number|string} id - Video ID
   */
  removeVideo(id) {
    const index = this.videos.findIndex(v => v.id == id);
    if (index > -1) {
      const removed = this.videos.splice(index, 1)[0];
      this._updateCache(this.videos);
      this._emit('videoRemoved', removed);
    }
  }

  /**
   * Clear all videos
   */
  clear() {
    this.videos = [];
    this.cache = null;
    this.cacheTimestamp = null;
    this._emit('cleared');
  }

  /**
   * Get sample data
   * @returns {Array} Sample videos
   */
  getSampleData() {
    return [
      {
        id: 1,
        title: "Contemporary Dance",
        category: "dance",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Dance",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 98.2,
        views: "2.3M",
        likes: "12.3k",
        comments: 234,
        duration: "0:45",
        username: "@dance_pro",
        tags: ["#bodyscript", "#posedetection", "#dance"]
      },
      {
        id: 2,
        title: "Martial Arts Form",
        category: "sports",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Martial+Arts",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 95.1,
        views: "1.8M",
        likes: "8.9k",
        comments: 189,
        duration: "0:38",
        username: "@martial_master",
        tags: ["#bodyscript", "#martialarts", "#sports"]
      },
      {
        id: 3,
        title: "Parkour Sequence",
        category: "sports",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Parkour",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 92.3,
        views: "3.1M",
        likes: "15.2k",
        comments: 445,
        duration: "0:52",
        username: "@parkour_ace",
        tags: ["#bodyscript", "#parkour", "#movement"]
      },
      {
        id: 4,
        title: "Yoga Flow",
        category: "yoga",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Yoga",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 96.8,
        views: "890k",
        likes: "7.2k",
        comments: 156,
        duration: "1:20",
        username: "@yoga_master",
        tags: ["#bodyscript", "#yoga", "#wellness"]
      },
      {
        id: 5,
        title: "Ballet Performance",
        category: "dance",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Ballet",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 94.5,
        views: "1.5M",
        likes: "9.8k",
        comments: 267,
        duration: "1:05",
        username: "@ballet_artist",
        tags: ["#bodyscript", "#ballet", "#classical"]
      },
      {
        id: 6,
        title: "Hip Hop Freestyle",
        category: "dance",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Hip+Hop",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 93.7,
        views: "4.2M",
        likes: "22.1k",
        comments: 892,
        duration: "0:35",
        username: "@hiphop_king",
        tags: ["#bodyscript", "#hiphop", "#freestyle"]
      },
      {
        id: 7,
        title: "Tai Chi Practice",
        category: "martial",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Tai+Chi",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 97.1,
        views: "670k",
        likes: "5.4k",
        comments: 98,
        duration: "1:15",
        username: "@taichi_master",
        tags: ["#bodyscript", "#taichi", "#mindfulness"]
      },
      {
        id: 8,
        title: "Boxing Training",
        category: "sports",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Boxing",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 91.8,
        views: "2.7M",
        likes: "14.3k",
        comments: 523,
        duration: "0:42",
        username: "@boxing_coach",
        tags: ["#bodyscript", "#boxing", "#training"]
      },
      {
        id: 9,
        title: "Salsa Dancing",
        category: "dance",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Salsa",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 95.6,
        views: "1.1M",
        likes: "8.7k",
        comments: 201,
        duration: "0:55",
        username: "@salsa_dancer",
        tags: ["#bodyscript", "#salsa", "#latin"]
      },
      {
        id: 10,
        title: "Gymnastics Routine",
        category: "sports",
        thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Gymnastics",
        preview: "sample-preview.mp4",
        full: "sample-full.mp4",
        accuracy: 94.2,
        views: "3.5M",
        likes: "18.6k",
        comments: 612,
        duration: "0:48",
        username: "@gym_star",
        tags: ["#bodyscript", "#gymnastics", "#sports"]
      }
    ];
  }

  /**
   * Normalize video data
   * @private
   * @param {Object} video - Raw video data
   * @returns {Object} Normalized video
   */
  _normalizeVideo(video) {
    return {
      ...video,
      thumbnail: this._resolveUrl(video.thumbnail),
      preview: this._resolveUrl(video.preview),
      full: this._resolveUrl(video.full)
    };
  }

  /**
   * Resolve URL with API prefix if needed
   * @private
   * @param {string} url - URL to resolve
   * @returns {string} Resolved URL
   */
  _resolveUrl(url) {
    if (!url) return '';

    // Already absolute URL
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }

    // Relative URL needing API prefix
    if (url.startsWith('/')) {
      return `${this.options.apiUrl}${url}`;
    }

    return url;
  }

  /**
   * Check if running on localhost
   * @private
   * @returns {boolean}
   */
  _isLocalhost() {
    const hostname = window.location.hostname;
    return hostname === 'localhost' || hostname === '127.0.0.1';
  }

  /**
   * Check if cache is still valid
   * @private
   * @returns {boolean}
   */
  _isCacheValid() {
    if (!this.cache || !this.cacheTimestamp) {
      return false;
    }

    const now = Date.now();
    return (now - this.cacheTimestamp) < this.options.cacheTimeout;
  }

  /**
   * Update cache
   * @private
   * @param {Array} data - Data to cache
   */
  _updateCache(data) {
    this.cache = [...data];
    this.cacheTimestamp = Date.now();
  }

  /**
   * Add event listener
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  on(event, handler) {
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
    if (!this.listeners.has(event)) return;

    const handlers = this.listeners.get(event);
    const index = handlers.indexOf(handler);
    if (index > -1) {
      handlers.splice(index, 1);
    }
  }

  /**
   * Emit event
   * @private
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  _emit(event, data) {
    if (!this.listeners.has(event)) return;

    this.listeners.get(event).forEach(handler => {
      handler(data);
    });
  }
}