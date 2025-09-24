// Upload API module

// Get API URL from config or use default
const API_URL = window.API_URL || 'http://localhost:8000';

/**
 * Upload a video file to the server for processing
 * @param {File} file - The video file to upload
 * @param {Function} onProgress - Optional progress callback
 * @returns {Promise<Object>} Upload response with job_id
 */
export async function uploadVideo(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/api/upload`, {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error('Upload failed: ' + errorText);
  }

  return response.json();
}

/**
 * Check the processing status of a job
 * @param {string} jobId - The job ID to check
 * @returns {Promise<Object>} Status response
 */
export async function checkStatus(jobId) {
  const response = await fetch(`${API_URL}/api/status/${jobId}`);

  if (!response.ok) {
    throw new Error('Failed to get status');
  }

  return response.json();
}

/**
 * Cancel a processing job
 * @param {string} jobId - The job ID to cancel
 * @returns {Promise<void>}
 */
export async function cancelJob(jobId) {
  try {
    await fetch(`${API_URL}/api/cancel/${jobId}`, {
      method: 'POST'
    });
  } catch (error) {
    // Best effort - don't throw on cancel errors
    console.error('Failed to cancel job:', error);
  }
}

/**
 * Cancel job using beacon (for page unload)
 * @param {string} jobId - The job ID to cancel
 */
export function cancelJobBeacon(jobId) {
  const cancelUrl = `${API_URL}/api/cancel/${jobId}`;
  navigator.sendBeacon(cancelUrl);
}

/**
 * Get download URLs for job results
 * @param {string} jobId - The job ID
 * @returns {Object} Download URLs
 */
export function getDownloadUrls(jobId) {
  return {
    video: `${API_URL}/api/download/${jobId}/video`,
    csv: `${API_URL}/api/download/${jobId}/csv`,
    json: `${API_URL}/api/download/${jobId}/json` // Future support
  };
}

/**
 * Check API health status
 * @param {boolean} throwOnError - Whether to throw on error
 * @returns {Promise<Object>} Health status
 */
export async function checkAPIHealth(throwOnError = true) {
  // Use window function if available (from config.js)
  if (window.checkAPIHealth) {
    return window.checkAPIHealth(throwOnError);
  }

  // Fallback implementation
  try {
    const response = await fetch(`${API_URL}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok && throwOnError) {
      throw new Error('API health check failed');
    }

    const data = await response.json();
    return {
      healthy: true,
      coldStart: data.cold_start || false,
      uptime: data.uptime || 0,
      ...data
    };
  } catch (error) {
    if (throwOnError) throw error;
    return { healthy: false, coldStart: false, uptime: 0 };
  }
}

/**
 * Poll job status until completion
 * @param {string} jobId - The job ID to poll
 * @param {Function} onProgress - Progress callback
 * @param {number} interval - Poll interval in milliseconds
 * @returns {Promise<Object>} Final status
 */
export async function pollJobStatus(jobId, onProgress, interval = 1000) {
  while (true) {
    const status = await checkStatus(jobId);

    if (onProgress) {
      onProgress(status);
    }

    if (status.status === 'completed') {
      return status;
    }

    if (status.status === 'failed' || status.status === 'cancelled') {
      throw new Error(status.error || `Job ${status.status}`);
    }

    // Wait before next poll
    await new Promise(resolve => setTimeout(resolve, interval));
  }
}

/**
 * Download a file from URL
 * @param {string} url - The download URL
 * @param {string} filename - The filename to save as
 */
export function downloadFile(url, filename) {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
}