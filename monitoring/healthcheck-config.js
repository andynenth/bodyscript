// Health Check Configuration for BodyScript
// Comprehensive system health monitoring

export const HEALTH_CHECK_CONFIG = {
  endpoints: {
    frontend: '/',
    api: '/api/health',
    database: '/api/health/database',
    storage: '/api/health/storage',
    processing: '/api/health/pose',
    cache: '/api/health/cache'
  },

  intervals: {
    critical: 30000,    // 30 seconds for critical services
    standard: 60000,    // 1 minute for standard checks
    extended: 300000    // 5 minutes for extended checks
  },

  timeouts: {
    fast: 5000,         // 5 seconds
    standard: 10000,    // 10 seconds
    slow: 30000         // 30 seconds for processing checks
  },

  thresholds: {
    response_time: {
      excellent: 200,
      good: 500,
      acceptable: 1000,
      poor: 2000
    },
    error_rate: {
      excellent: 0.001,  // 0.1%
      good: 0.01,        // 1%
      acceptable: 0.05,  // 5%
      critical: 0.1      // 10%
    }
  }
};

class HealthCheckManager {
  constructor() {
    this.checks = new Map();
    this.results = new Map();
    this.listeners = new Set();
    this.isRunning = false;
  }

  // Register a health check
  registerCheck(name, config) {
    this.checks.set(name, {
      name,
      url: config.url,
      method: config.method || 'GET',
      timeout: config.timeout || HEALTH_CHECK_CONFIG.timeouts.standard,
      interval: config.interval || HEALTH_CHECK_CONFIG.intervals.standard,
      critical: config.critical || false,
      headers: config.headers || {},
      validator: config.validator || this.defaultValidator,
      lastCheck: null,
      intervalId: null
    });
  }

  // Default response validator
  defaultValidator(response, responseTime) {
    return {
      healthy: response.ok,
      status: response.status,
      responseTime,
      message: response.ok ? 'OK' : `HTTP ${response.status}`,
      data: null
    };
  }

  // Specific validators for different endpoints
  static validators = {
    api: async (response, responseTime) => {
      if (!response.ok) {
        return {
          healthy: false,
          status: response.status,
          responseTime,
          message: `API unhealthy: HTTP ${response.status}`,
          data: null
        };
      }

      try {
        const data = await response.json();
        return {
          healthy: data.status === 'healthy',
          status: response.status,
          responseTime,
          message: data.message || 'OK',
          data: {
            version: data.version,
            uptime: data.uptime,
            environment: data.environment
          }
        };
      } catch (error) {
        return {
          healthy: false,
          status: response.status,
          responseTime,
          message: 'Invalid JSON response',
          data: null
        };
      }
    },

    database: async (response, responseTime) => {
      if (!response.ok) {
        return {
          healthy: false,
          status: response.status,
          responseTime,
          message: `Database check failed: HTTP ${response.status}`,
          data: null
        };
      }

      try {
        const data = await response.json();
        return {
          healthy: data.database.connected && data.database.responseTime < 100,
          status: response.status,
          responseTime,
          message: data.database.connected ? 'Connected' : 'Disconnected',
          data: {
            connected: data.database.connected,
            responseTime: data.database.responseTime,
            connections: data.database.connections,
            version: data.database.version
          }
        };
      } catch (error) {
        return {
          healthy: false,
          status: response.status,
          responseTime,
          message: 'Database health check failed',
          data: null
        };
      }
    },

    processing: async (response, responseTime) => {
      if (!response.ok) {
        return {
          healthy: false,
          status: response.status,
          responseTime,
          message: `Pose processing check failed: HTTP ${response.status}`,
          data: null
        };
      }

      try {
        const data = await response.json();
        const processingHealthy = data.mediapipe.initialized &&
                                 data.mediapipe.modelLoaded &&
                                 data.processing.queueSize < 10;

        return {
          healthy: processingHealthy,
          status: response.status,
          responseTime,
          message: processingHealthy ? 'Processing ready' : 'Processing degraded',
          data: {
            mediapipe: data.mediapipe,
            processing: data.processing,
            memory: data.memory
          }
        };
      } catch (error) {
        return {
          healthy: false,
          status: response.status,
          responseTime,
          message: 'Processing health check failed',
          data: null
        };
      }
    }
  };

  // Perform a single health check
  async performCheck(checkConfig) {
    const startTime = performance.now();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), checkConfig.timeout);

      const response = await fetch(checkConfig.url, {
        method: checkConfig.method,
        headers: checkConfig.headers,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      const responseTime = Math.round(performance.now() - startTime);

      const result = await checkConfig.validator(response, responseTime);

      return {
        ...result,
        timestamp: new Date().toISOString(),
        checkName: checkConfig.name
      };

    } catch (error) {
      const responseTime = Math.round(performance.now() - startTime);

      return {
        healthy: false,
        status: 0,
        responseTime,
        message: error.name === 'AbortError' ? 'Timeout' : error.message,
        data: null,
        timestamp: new Date().toISOString(),
        checkName: checkConfig.name
      };
    }
  }

  // Start monitoring
  start() {
    if (this.isRunning) return;

    this.isRunning = true;

    for (const [name, config] of this.checks) {
      // Perform initial check
      this.performCheck(config).then(result => {
        this.handleResult(name, result);
      });

      // Schedule recurring checks
      config.intervalId = setInterval(async () => {
        const result = await this.performCheck(config);
        this.handleResult(name, result);
      }, config.interval);
    }

    console.log('Health check monitoring started');
  }

  // Stop monitoring
  stop() {
    if (!this.isRunning) return;

    for (const [name, config] of this.checks) {
      if (config.intervalId) {
        clearInterval(config.intervalId);
        config.intervalId = null;
      }
    }

    this.isRunning = false;
    console.log('Health check monitoring stopped');
  }

  // Handle check result
  handleResult(checkName, result) {
    const previous = this.results.get(checkName);
    this.results.set(checkName, result);

    // Update check config
    const config = this.checks.get(checkName);
    if (config) {
      config.lastCheck = result.timestamp;
    }

    // Notify listeners
    this.notifyListeners(checkName, result, previous);

    // Log significant changes
    if (!previous || previous.healthy !== result.healthy) {
      const status = result.healthy ? 'HEALTHY' : 'UNHEALTHY';
      console.log(`Health Check [${checkName}]: ${status} - ${result.message}`);

      // Send alert for critical services
      if (config && config.critical && !result.healthy) {
        this.sendAlert(checkName, result);
      }
    }
  }

  // Add result listener
  addListener(callback) {
    this.listeners.add(callback);
  }

  // Remove result listener
  removeListener(callback) {
    this.listeners.delete(callback);
  }

  // Notify all listeners
  notifyListeners(checkName, result, previous) {
    for (const callback of this.listeners) {
      try {
        callback(checkName, result, previous);
      } catch (error) {
        console.error('Health check listener error:', error);
      }
    }
  }

  // Send alert for critical failures
  async sendAlert(checkName, result) {
    const alertData = {
      service: 'BodyScript',
      check: checkName,
      status: 'CRITICAL',
      message: result.message,
      timestamp: result.timestamp,
      responseTime: result.responseTime,
      environment: process.env.VITE_ENVIRONMENT
    };

    try {
      // Send to monitoring service
      await fetch('/api/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(alertData)
      });
    } catch (error) {
      console.error('Failed to send alert:', error);
    }
  }

  // Get current system health summary
  getHealthSummary() {
    const checks = Array.from(this.results.values());
    const critical = checks.filter(c => this.checks.get(c.checkName)?.critical);

    const healthyChecks = checks.filter(c => c.healthy).length;
    const totalChecks = checks.length;
    const criticalUnhealthy = critical.filter(c => !c.healthy).length;

    const averageResponseTime = checks.length > 0
      ? Math.round(checks.reduce((sum, c) => sum + c.responseTime, 0) / checks.length)
      : 0;

    return {
      overall: criticalUnhealthy === 0 && healthyChecks === totalChecks ? 'healthy' :
               criticalUnhealthy > 0 ? 'critical' : 'degraded',
      healthy: healthyChecks,
      total: totalChecks,
      criticalFailures: criticalUnhealthy,
      averageResponseTime,
      timestamp: new Date().toISOString(),
      checks: Object.fromEntries(this.results)
    };
  }
}

// Initialize default health checks
export function initializeHealthChecks(baseUrl = '') {
  const healthCheck = new HealthCheckManager();

  // Register standard checks
  healthCheck.registerCheck('frontend', {
    url: `${baseUrl}/`,
    timeout: HEALTH_CHECK_CONFIG.timeouts.fast,
    interval: HEALTH_CHECK_CONFIG.intervals.standard,
    critical: true
  });

  healthCheck.registerCheck('api', {
    url: `${baseUrl}/api/health`,
    timeout: HEALTH_CHECK_CONFIG.timeouts.standard,
    interval: HEALTH_CHECK_CONFIG.intervals.critical,
    critical: true,
    validator: HealthCheckManager.validators.api
  });

  healthCheck.registerCheck('database', {
    url: `${baseUrl}/api/health/database`,
    timeout: HEALTH_CHECK_CONFIG.timeouts.standard,
    interval: HEALTH_CHECK_CONFIG.intervals.standard,
    critical: true,
    validator: HealthCheckManager.validators.database
  });

  healthCheck.registerCheck('processing', {
    url: `${baseUrl}/api/health/pose`,
    timeout: HEALTH_CHECK_CONFIG.timeouts.slow,
    interval: HEALTH_CHECK_CONFIG.intervals.extended,
    critical: false,
    validator: HealthCheckManager.validators.processing
  });

  return healthCheck;
}

export { HealthCheckManager };
export default { HealthCheckManager, initializeHealthChecks, HEALTH_CHECK_CONFIG };