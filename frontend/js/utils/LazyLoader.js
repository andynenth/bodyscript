/**
 * LazyLoader - Generic lazy loading utility using Intersection Observer
 * Handles lazy loading of images, videos, and other resources
 */

export class LazyLoader {
  constructor(options = {}) {
    this.options = {
      root: null,               // Viewport by default
      rootMargin: '50px',       // Start loading 50px before visible
      threshold: 0.01,          // 1% visibility triggers loading
      selector: '[data-lazy]',  // Elements to lazy load
      loadedClass: 'lazy-loaded', // Class added after loading
      loadingClass: 'lazy-loading', // Class during loading
      errorClass: 'lazy-error', // Class on error
      ...options
    };

    this.observer = null;
    this.elements = new Set();
    this.loadHandlers = new Map();

    this._createObserver();
  }

  /**
   * Create Intersection Observer
   * @private
   */
  _createObserver() {
    const observerOptions = {
      root: this.options.root,
      rootMargin: this.options.rootMargin,
      threshold: this.options.threshold
    };

    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this._loadElement(entry.target);
        }
      });
    }, observerOptions);
  }

  /**
   * Start observing elements
   * @param {HTMLElement|NodeList|Array|string} elements - Elements or selector
   */
  observe(elements) {
    const elementsArray = this._normalizeElements(elements);

    elementsArray.forEach(element => {
      if (!this.elements.has(element)) {
        this.elements.add(element);
        this.observer.observe(element);
      }
    });
  }

  /**
   * Stop observing elements
   * @param {HTMLElement|NodeList|Array|string} elements - Elements or selector
   */
  unobserve(elements) {
    const elementsArray = this._normalizeElements(elements);

    elementsArray.forEach(element => {
      if (this.elements.has(element)) {
        this.elements.delete(element);
        this.observer.unobserve(element);
        this._removeHandlers(element);
      }
    });
  }

  /**
   * Load element immediately
   * @param {HTMLElement} element - Element to load
   */
  load(element) {
    this._loadElement(element);
  }

  /**
   * Load element resources
   * @private
   * @param {HTMLElement} element - Element to load
   */
  async _loadElement(element) {
    // Stop observing this element
    this.observer.unobserve(element);
    this.elements.delete(element);

    // Add loading class
    element.classList.add(this.options.loadingClass);

    try {
      // Determine element type and load accordingly
      if (element.tagName === 'IMG') {
        await this._loadImage(element);
      } else if (element.tagName === 'VIDEO') {
        await this._loadVideo(element);
      } else if (element.tagName === 'IFRAME') {
        await this._loadIframe(element);
      } else {
        await this._loadGeneric(element);
      }

      // Mark as loaded
      element.classList.remove(this.options.loadingClass);
      element.classList.add(this.options.loadedClass);

      // Emit success event
      this._emit(element, 'loaded');

    } catch (error) {
      // Mark as error
      element.classList.remove(this.options.loadingClass);
      element.classList.add(this.options.errorClass);

      // Emit error event
      this._emit(element, 'error', error);

      console.error('LazyLoader: Failed to load element', element, error);
    }
  }

  /**
   * Load image element
   * @private
   * @param {HTMLImageElement} img - Image element
   */
  _loadImage(img) {
    return new Promise((resolve, reject) => {
      const src = img.dataset.src || img.dataset.lazy;
      const srcset = img.dataset.srcset;

      if (!src) {
        reject(new Error('No lazy source found'));
        return;
      }

      // Create temporary image to preload
      const tempImg = new Image();

      const handlers = {
        load: () => {
          // Apply to actual image
          img.src = src;
          if (srcset) {
            img.srcset = srcset;
          }

          // Clean up data attributes
          delete img.dataset.src;
          delete img.dataset.srcset;
          delete img.dataset.lazy;

          this._removeHandlers(tempImg);
          resolve(img);
        },
        error: (error) => {
          this._removeHandlers(tempImg);
          reject(error);
        }
      };

      // Store handlers for cleanup
      this.loadHandlers.set(tempImg, handlers);

      // Add event listeners
      tempImg.addEventListener('load', handlers.load);
      tempImg.addEventListener('error', handlers.error);

      // Start loading
      if (srcset) {
        tempImg.srcset = srcset;
      }
      tempImg.src = src;
    });
  }

  /**
   * Load video element
   * @private
   * @param {HTMLVideoElement} video - Video element
   */
  _loadVideo(video) {
    return new Promise((resolve, reject) => {
      const src = video.dataset.src || video.dataset.lazy;
      const poster = video.dataset.poster;

      if (!src) {
        reject(new Error('No lazy source found'));
        return;
      }

      const handlers = {
        canplay: () => {
          // Clean up data attributes
          delete video.dataset.src;
          delete video.dataset.poster;
          delete video.dataset.lazy;

          this._removeHandlers(video);
          resolve(video);
        },
        error: (error) => {
          this._removeHandlers(video);
          reject(error);
        }
      };

      // Store handlers for cleanup
      this.loadHandlers.set(video, handlers);

      // Add event listeners
      video.addEventListener('canplay', handlers.canplay, { once: true });
      video.addEventListener('error', handlers.error, { once: true });

      // Apply attributes
      if (poster) {
        video.poster = poster;
      }
      video.src = src;

      // Load the video
      video.load();
    });
  }

  /**
   * Load iframe element
   * @private
   * @param {HTMLIFrameElement} iframe - Iframe element
   */
  _loadIframe(iframe) {
    return new Promise((resolve) => {
      const src = iframe.dataset.src || iframe.dataset.lazy;

      if (src) {
        iframe.src = src;

        // Clean up data attributes
        delete iframe.dataset.src;
        delete iframe.dataset.lazy;
      }

      resolve(iframe);
    });
  }

  /**
   * Load generic element with data-lazy attribute
   * @private
   * @param {HTMLElement} element - Element
   */
  _loadGeneric(element) {
    return new Promise((resolve) => {
      // Handle background images
      const bgImage = element.dataset.bgImage || element.dataset.lazyBg;
      if (bgImage) {
        element.style.backgroundImage = `url(${bgImage})`;
        delete element.dataset.bgImage;
        delete element.dataset.lazyBg;
      }

      // Handle any other data-lazy attributes
      const lazyContent = element.dataset.lazy;
      if (lazyContent) {
        // Could be HTML content or other data
        if (element.dataset.lazyType === 'html') {
          element.innerHTML = lazyContent;
        }
        delete element.dataset.lazy;
        delete element.dataset.lazyType;
      }

      resolve(element);
    });
  }

  /**
   * Normalize elements input
   * @private
   * @param {HTMLElement|NodeList|Array|string} elements - Elements or selector
   * @returns {Array} Array of elements
   */
  _normalizeElements(elements) {
    if (typeof elements === 'string') {
      return Array.from(document.querySelectorAll(elements));
    }

    if (elements instanceof HTMLElement) {
      return [elements];
    }

    if (elements instanceof NodeList || elements instanceof HTMLCollection) {
      return Array.from(elements);
    }

    if (Array.isArray(elements)) {
      return elements;
    }

    return [];
  }

  /**
   * Remove event handlers
   * @private
   * @param {HTMLElement} element - Element
   */
  _removeHandlers(element) {
    const handlers = this.loadHandlers.get(element);
    if (handlers) {
      if (handlers.load) {
        element.removeEventListener('load', handlers.load);
        element.removeEventListener('canplay', handlers.canplay);
      }
      if (handlers.error) {
        element.removeEventListener('error', handlers.error);
      }
      this.loadHandlers.delete(element);
    }
  }

  /**
   * Emit custom event
   * @private
   * @param {HTMLElement} element - Element
   * @param {string} eventType - Event type
   * @param {*} detail - Event detail
   */
  _emit(element, eventType, detail = null) {
    const event = new CustomEvent(`lazy:${eventType}`, {
      detail: { element, ...detail },
      bubbles: true,
      cancelable: true
    });
    element.dispatchEvent(event);
  }

  /**
   * Load all elements immediately
   */
  loadAll() {
    const elements = Array.from(this.elements);
    elements.forEach(element => this._loadElement(element));
  }

  /**
   * Reset lazy loader
   */
  reset() {
    // Unobserve all elements
    this.elements.forEach(element => {
      this.observer.unobserve(element);
    });

    // Clear sets and maps
    this.elements.clear();
    this.loadHandlers.clear();
  }

  /**
   * Destroy lazy loader
   */
  destroy() {
    // Disconnect observer
    if (this.observer) {
      this.observer.disconnect();
      this.observer = null;
    }

    // Clear all handlers
    this.loadHandlers.forEach((handlers, element) => {
      this._removeHandlers(element);
    });

    // Clear sets and maps
    this.elements.clear();
    this.loadHandlers.clear();
  }

  /**
   * Check if browser supports Intersection Observer
   * @static
   * @returns {boolean}
   */
  static isSupported() {
    return 'IntersectionObserver' in window &&
           'IntersectionObserverEntry' in window &&
           'intersectionRatio' in window.IntersectionObserverEntry.prototype;
  }
}