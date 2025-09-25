/**
 * BodyScript Frontend Configuration
 * Handles environment-specific settings and keep-alive
 */

const Config = {
  /**
   * Get API URL based on current environment
   */
  getApiUrl: () => {
    console.log('Location info:', {
      hostname: window.location.hostname,
      port: window.location.port,
      protocol: window.location.protocol,
      href: window.location.href
    });

    // Force local API for development
    if (window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1' ||
        window.location.port === '8000' ||
        window.location.protocol === 'file:') {
      console.log('Using LOCAL API');
      return 'http://localhost:8000';
    }
    // Production URL - Update after Render deployment
    console.log('Using PRODUCTION API');
    return 'https://bodyscript-api.onrender.com';
  },

  /**
   * Get gallery data URL (R2 public bucket)
   */
  getGalleryDataUrl: () => {
    // R2 public bucket URL for gallery data
    if (window.location.hostname === 'localhost') {
      return null;  // Use sample data locally for now
    }
    return 'https://bodyscript.andynenth.dev/gallery.json';
  },

  /**
   * Keep-alive configuration to prevent backend sleeping
   */
  keepAlive: {
    enabled: !window.location.hostname.includes('localhost'),
    interval: 600000  // 10 minutes
  },

  /**
   * Wake-up message configuration for better UX
   */
  wakeUpMessage: {
    enabled: !window.location.hostname.includes('localhost'),  // Disable for localhost
    timeout: 65000,  // 65 seconds
    message: '⏳ Waking up server (free tier may take 30-60 seconds)...',
    successMessage: '✅ API Connected and ready',
    errorMessage: '❌ Server is taking too long. Please refresh the page.'
  },

  /**
   * Admin configuration
   */
  admin: {
    enabled: true,
    tokenKey: 'bodyscript_admin_token'  // LocalStorage key for admin token
  }
};

// Set global API URL dynamically based on environment
window.API_URL = (() => {
  const hostname = window.location.hostname;
  const port = window.location.port;
  const protocol = window.location.protocol;

  // Local development
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return `http://localhost:${port || '8000'}`;
  }

  // Production with HTTPS (Nginx reverse proxy handles port 8000 internally)
  if (hostname.includes('bodyscript') || hostname.includes('andynenth')) {
    // Use same protocol as the page (HTTPS) and no port (Nginx handles it)
    return `${protocol}//${hostname}`;
  }

  // Fallback: same origin
  return `${protocol}//${hostname}${port ? ':' + port : ''}`;
})();

console.log('API URL configured as:', window.API_URL);

// Initialize keep-alive mechanism if enabled
if (Config.keepAlive.enabled) {
  console.log('Keep-alive enabled: pinging server every', Config.keepAlive.interval / 1000, 'seconds');

  setInterval(() => {
    fetch(`${window.API_URL}/health`)
      .then(response => {
        if (response.ok) {
          console.log('Keep-alive ping successful');
        }
      })
      .catch(() => {
        console.log('Keep-alive ping failed (server may be sleeping)');
      });
  }, Config.keepAlive.interval);
}

// Health check with wake-up handling
window.checkAPIHealth = async function(showMessage = true) {
  const startTime = Date.now();

  if (showMessage && Config.wakeUpMessage.enabled) {
    // Show wake-up message in UI if element exists
    const statusEl = document.getElementById('api-status');
    if (statusEl) {
      statusEl.innerHTML = `<span class="warning">${Config.wakeUpMessage.message}</span>`;
      statusEl.style.display = 'block';
    }
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), Config.wakeUpMessage.timeout);

    const response = await fetch(`${window.API_URL}/health`, {
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      const responseTime = Date.now() - startTime;

      // API health check successful

      if (showMessage) {
        const statusEl = document.getElementById('api-status');
        if (statusEl) {
          if (data.cold_start) {
            statusEl.innerHTML = '<span class="warning">🔄 Server starting up (cold start detected)</span>';
          } else {
            statusEl.innerHTML = `<span class="success">${Config.wakeUpMessage.successMessage}</span>`;
          }

          // Hide message after 3 seconds
          setTimeout(() => {
            statusEl.style.display = 'none';
          }, 3000);
        }
      }

      return {
        healthy: true,
        coldStart: data.cold_start,
        uptime: data.uptime_seconds
      };
    }
  } catch (error) {
    console.error('Health check failed:', error);

    if (showMessage) {
      const statusEl = document.getElementById('api-status');
      if (statusEl) {
        if (error.name === 'AbortError') {
          statusEl.innerHTML = `<span class="error">${Config.wakeUpMessage.errorMessage}</span>`;
        } else {
          statusEl.innerHTML = '<span class="error">❌ Cannot connect to server</span>';
        }
      }
    }

    return {
      healthy: false,
      error: error.message
    };
  }
};

// Export for use in other scripts
window.Config = Config;