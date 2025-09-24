// Event helper utilities for better performance

/**
 * Detect if passive event listeners are supported
 */
let passiveSupported = false;
try {
  const options = {
    get passive() {
      passiveSupported = true;
      return false;
    }
  };
  window.addEventListener("test", null, options);
  window.removeEventListener("test", null, options);
} catch (err) {
  passiveSupported = false;
}

/**
 * Get event options with passive flag for scroll-blocking events
 * @param {boolean} passive - Whether the event should be passive
 * @returns {Object|boolean} Event options or false for older browsers
 */
export function getPassiveOptions(passive = true) {
  return passiveSupported ? { passive } : false;
}

/**
 * Add event listener with passive option for better scroll performance
 * @param {Element} element - Target element
 * @param {string} event - Event name
 * @param {Function} handler - Event handler
 * @param {boolean} passive - Whether to use passive mode (default true for touch/wheel events)
 */
export function addPassiveEventListener(element, event, handler, passive = null) {
  // Auto-detect if passive should be used based on event type
  if (passive === null) {
    const scrollBlockingEvents = ['touchstart', 'touchmove', 'touchend', 'wheel', 'mousewheel'];
    passive = scrollBlockingEvents.includes(event);
  }

  element.addEventListener(event, handler, getPassiveOptions(passive));
}

/**
 * Remove event listener with passive option
 * @param {Element} element - Target element
 * @param {string} event - Event name
 * @param {Function} handler - Event handler
 * @param {boolean} passive - Whether passive mode was used
 */
export function removePassiveEventListener(element, event, handler, passive = null) {
  if (passive === null) {
    const scrollBlockingEvents = ['touchstart', 'touchmove', 'touchend', 'wheel', 'mousewheel'];
    passive = scrollBlockingEvents.includes(event);
  }

  element.removeEventListener(event, handler, getPassiveOptions(passive));
}