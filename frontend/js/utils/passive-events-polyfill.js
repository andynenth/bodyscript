// Passive Events Polyfill
// Automatically makes scroll-blocking events passive for better performance

(function() {
  // Only run if passive is supported
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

  if (!passiveSupported) return;

  // Events that should be passive by default
  const passiveEvents = ['touchstart', 'touchmove', 'wheel', 'mousewheel'];

  // Store original addEventListener
  const originalAddEventListener = EventTarget.prototype.addEventListener;

  // Override addEventListener
  EventTarget.prototype.addEventListener = function(type, listener, options) {
    // If it's a scroll-blocking event and no options specified, make it passive
    if (passiveEvents.includes(type) && (options === undefined || options === false || options === true)) {
      options = { passive: true, capture: options === true };
    }

    // For dragover, we can't make it passive since preventDefault is needed
    if (type === 'dragover' && typeof options === 'object') {
      options.passive = false;
    }

    return originalAddEventListener.call(this, type, listener, options);
  };
})();