/**
 * TouchHandler - Touch support utility for mobile interactions
 * Handles touch gestures, long press, swipe detection
 */

export class TouchHandler {
  constructor(options = {}) {
    this.options = {
      longPressDelay: 500,      // Time for long press (ms)
      swipeThreshold: 50,       // Minimum distance for swipe (px)
      swipeTimeout: 500,        // Maximum time for swipe (ms)
      doubleTapDelay: 300,      // Maximum delay between taps
      preventDefault: false,     // Prevent default touch behavior
      passive: true,            // Use passive listeners for better performance
      ...options
    };

    this.handlers = new Map();
    this.touches = new Map();
  }

  /**
   * Add touch support to element
   * @param {HTMLElement} element - Element to add touch support to
   * @param {Object} callbacks - Touch event callbacks
   */
  addTouchSupport(element, callbacks = {}) {
    if (!element || this.handlers.has(element)) return;

    const touchData = {
      startX: 0,
      startY: 0,
      startTime: 0,
      longPressTimer: null,
      tapTimer: null,
      tapCount: 0,
      isLongPress: false,
      isSwiping: false
    };

    // Create event handlers
    const handlers = {
      touchstart: (e) => this._handleTouchStart(e, element, touchData, callbacks),
      touchmove: (e) => this._handleTouchMove(e, element, touchData, callbacks),
      touchend: (e) => this._handleTouchEnd(e, element, touchData, callbacks),
      touchcancel: (e) => this._handleTouchCancel(e, element, touchData, callbacks)
    };

    // Add event listeners
    const listenerOptions = {
      passive: this.options.passive,
      capture: false
    };

    Object.entries(handlers).forEach(([event, handler]) => {
      element.addEventListener(event, handler, listenerOptions);
    });

    // Store for cleanup
    this.handlers.set(element, handlers);
    this.touches.set(element, touchData);
  }

  /**
   * Handle touch start
   * @private
   */
  _handleTouchStart(e, element, touchData, callbacks) {
    if (this.options.preventDefault) {
      e.preventDefault();
    }

    const touch = e.touches[0];
    touchData.startX = touch.clientX;
    touchData.startY = touch.clientY;
    touchData.startTime = Date.now();
    touchData.isLongPress = false;
    touchData.isSwiping = false;

    // Handle tap counting for double tap
    if (touchData.tapTimer) {
      clearTimeout(touchData.tapTimer);
      touchData.tapCount++;
    } else {
      touchData.tapCount = 1;
    }

    // Start long press timer
    touchData.longPressTimer = setTimeout(() => {
      touchData.isLongPress = true;
      if (callbacks.onLongPress) {
        callbacks.onLongPress(e, { element, x: touch.clientX, y: touch.clientY });
      }
    }, this.options.longPressDelay);

    // Call touch start callback
    if (callbacks.onTouchStart) {
      callbacks.onTouchStart(e, { element, x: touch.clientX, y: touch.clientY });
    }
  }

  /**
   * Handle touch move
   * @private
   */
  _handleTouchMove(e, element, touchData, callbacks) {
    if (!touchData.startTime) return;

    const touch = e.touches[0];
    const deltaX = touch.clientX - touchData.startX;
    const deltaY = touch.clientY - touchData.startY;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    // Cancel long press if moved too much
    if (distance > 10 && touchData.longPressTimer) {
      clearTimeout(touchData.longPressTimer);
      touchData.longPressTimer = null;
    }

    // Detect swipe
    if (distance > this.options.swipeThreshold) {
      touchData.isSwiping = true;
    }

    // Call move callback
    if (callbacks.onTouchMove) {
      callbacks.onTouchMove(e, {
        element,
        x: touch.clientX,
        y: touch.clientY,
        deltaX,
        deltaY,
        distance
      });
    }
  }

  /**
   * Handle touch end
   * @private
   */
  _handleTouchEnd(e, element, touchData, callbacks) {
    if (!touchData.startTime) return;

    // Clear long press timer
    if (touchData.longPressTimer) {
      clearTimeout(touchData.longPressTimer);
      touchData.longPressTimer = null;
    }

    const endTime = Date.now();
    const duration = endTime - touchData.startTime;

    // Get end position
    const touch = e.changedTouches[0];
    const deltaX = touch.clientX - touchData.startX;
    const deltaY = touch.clientY - touchData.startY;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    // Handle different gestures
    if (touchData.isLongPress) {
      // Long press already handled
      if (callbacks.onLongPressEnd) {
        callbacks.onLongPressEnd(e, { element });
      }
    } else if (touchData.isSwiping && duration < this.options.swipeTimeout) {
      // Detect swipe direction
      const direction = this._getSwipeDirection(deltaX, deltaY);

      if (callbacks.onSwipe) {
        callbacks.onSwipe(e, {
          element,
          direction,
          distance,
          duration,
          deltaX,
          deltaY
        });
      }

      // Call specific swipe direction callbacks
      const swipeCallback = callbacks[`onSwipe${direction.charAt(0).toUpperCase() + direction.slice(1)}`];
      if (swipeCallback) {
        swipeCallback(e, { element, distance, duration });
      }
    } else if (distance < 10) {
      // Handle tap
      if (touchData.tapCount === 2) {
        // Double tap
        if (callbacks.onDoubleTap) {
          callbacks.onDoubleTap(e, { element, x: touch.clientX, y: touch.clientY });
        }
        touchData.tapCount = 0;
      } else {
        // Single tap (wait to see if it becomes double tap)
        touchData.tapTimer = setTimeout(() => {
          if (touchData.tapCount === 1 && callbacks.onTap) {
            callbacks.onTap(e, { element, x: touch.clientX, y: touch.clientY });
          }
          touchData.tapCount = 0;
          touchData.tapTimer = null;
        }, this.options.doubleTapDelay);
      }
    }

    // Call touch end callback
    if (callbacks.onTouchEnd) {
      callbacks.onTouchEnd(e, {
        element,
        duration,
        distance
      });
    }

    // Reset touch data
    touchData.startTime = 0;
    touchData.isLongPress = false;
    touchData.isSwiping = false;
  }

  /**
   * Handle touch cancel
   * @private
   */
  _handleTouchCancel(e, element, touchData, callbacks) {
    // Clear timers
    if (touchData.longPressTimer) {
      clearTimeout(touchData.longPressTimer);
      touchData.longPressTimer = null;
    }

    if (touchData.tapTimer) {
      clearTimeout(touchData.tapTimer);
      touchData.tapTimer = null;
    }

    // Reset touch data
    touchData.startTime = 0;
    touchData.tapCount = 0;
    touchData.isLongPress = false;
    touchData.isSwiping = false;

    // Call cancel callback
    if (callbacks.onTouchCancel) {
      callbacks.onTouchCancel(e, { element });
    }
  }

  /**
   * Get swipe direction
   * @private
   */
  _getSwipeDirection(deltaX, deltaY) {
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);

    if (absX > absY) {
      return deltaX > 0 ? 'right' : 'left';
    } else {
      return deltaY > 0 ? 'down' : 'up';
    }
  }

  /**
   * Remove touch support from element
   * @param {HTMLElement} element - Element to remove touch support from
   */
  removeTouchSupport(element) {
    const handlers = this.handlers.get(element);
    const touchData = this.touches.get(element);

    if (handlers) {
      // Remove event listeners
      Object.entries(handlers).forEach(([event, handler]) => {
        element.removeEventListener(event, handler);
      });

      // Clear timers
      if (touchData) {
        if (touchData.longPressTimer) {
          clearTimeout(touchData.longPressTimer);
        }
        if (touchData.tapTimer) {
          clearTimeout(touchData.tapTimer);
        }
      }

      // Clean up
      this.handlers.delete(element);
      this.touches.delete(element);
    }
  }

  /**
   * Add pinch gesture support
   * @param {HTMLElement} element - Element to add pinch support to
   * @param {Function} onPinch - Pinch callback
   */
  addPinchSupport(element, onPinch) {
    let initialDistance = 0;
    let currentScale = 1;

    const handleTouchStart = (e) => {
      if (e.touches.length === 2) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        initialDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
      }
    };

    const handleTouchMove = (e) => {
      if (e.touches.length === 2 && initialDistance > 0) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const currentDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );

        currentScale = currentDistance / initialDistance;

        if (onPinch) {
          onPinch(e, {
            element,
            scale: currentScale,
            distance: currentDistance
          });
        }
      }
    };

    element.addEventListener('touchstart', handleTouchStart, { passive: true });
    element.addEventListener('touchmove', handleTouchMove, { passive: true });

    // Store for cleanup
    if (!this.handlers.has(element)) {
      this.handlers.set(element, {});
    }
    const handlers = this.handlers.get(element);
    handlers.pinchStart = handleTouchStart;
    handlers.pinchMove = handleTouchMove;
  }

  /**
   * Destroy and clean up
   */
  destroy() {
    // Remove all touch support
    this.handlers.forEach((handlers, element) => {
      this.removeTouchSupport(element);
    });

    // Clear maps
    this.handlers.clear();
    this.touches.clear();
  }

  /**
   * Check if touch is supported
   * @static
   * @returns {boolean}
   */
  static isSupported() {
    return 'ontouchstart' in window ||
           navigator.maxTouchPoints > 0 ||
           navigator.msMaxTouchPoints > 0;
  }
}