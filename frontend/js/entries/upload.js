/**
 * Upload Page Entry Point
 *
 * This is the main entry point for the upload page.
 * It imports the main application features and the upload-specific functionality.
 */

// Import global application setup
import '../main.js';

// Import upload-specific CSS
import '@css/pages/upload.css';

// Import the existing upload functionality
import '../pages/upload-page.js';

// Import upload-specific components
import '@components/progress-bar.js';
import '@components/file-handler.js';

// Upload-specific initialization
document.addEventListener('DOMContentLoaded', () => {
  window.BodyScript.utils.log('Upload page loaded');

  // Emit upload-ready event for other modules
  window.BodyScript.events.emit('upload-ready');

  // Set up upload-specific features
  setupUploadFeatures();
});

/**
 * Set up upload-specific features
 */
function setupUploadFeatures() {
  // File validation
  setupFileValidation();

  // Upload progress monitoring
  setupProgressMonitoring();

  // Upload keyboard shortcuts
  setupKeyboardShortcuts();

  // Drag and drop enhancements
  setupDragAndDropEnhancements();

  // Upload accessibility features
  setupAccessibility();
}

/**
 * Enhanced file validation
 */
function setupFileValidation() {
  const config = window.BodyScript.config;

  // Extend global validation
  window.BodyScript.validateFile = (file) => {
    const errors = [];

    // File type validation
    if (!config.supportedFormats.includes(file.type)) {
      errors.push(`Unsupported file type: ${file.type}`);
    }

    // File size validation
    if (file.size > config.maxFileSize) {
      errors.push(`File too large: ${window.BodyScript.utils.formatBytes(file.size)} (max: ${window.BodyScript.utils.formatBytes(config.maxFileSize)})`);
    }

    // File name validation
    if (file.name.length > 255) {
      errors.push('File name too long');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  };

  // Listen for file validation events
  window.BodyScript.events.on('file-selected', (file) => {
    const validation = window.BodyScript.validateFile(file);
    window.BodyScript.events.emit('file-validated', { file, validation });
  });
}

/**
 * Enhanced progress monitoring
 */
function setupProgressMonitoring() {
  let startTime = null;
  let lastProgressTime = null;

  window.BodyScript.events.on('upload-start', () => {
    startTime = Date.now();
    lastProgressTime = startTime;
    window.BodyScript.utils.log('Upload started');
  });

  window.BodyScript.events.on('upload-progress', (data) => {
    const now = Date.now();
    const elapsed = now - startTime;
    const progressElapsed = now - lastProgressTime;

    // Calculate speed
    if (progressElapsed > 1000) { // Update every second
      const speed = (data.loaded / elapsed) * 1000; // bytes per second
      window.BodyScript.events.emit('upload-speed', {
        speed,
        speedFormatted: window.BodyScript.utils.formatBytes(speed) + '/s',
      });
      lastProgressTime = now;
    }

    // Estimate remaining time
    if (data.percent > 0) {
      const estimatedTotal = (elapsed / data.percent) * 100;
      const estimatedRemaining = estimatedTotal - elapsed;
      window.BodyScript.events.emit('upload-eta', {
        remaining: estimatedRemaining,
        remainingFormatted: window.BodyScript.utils.formatDuration(estimatedRemaining / 1000),
      });
    }
  });

  window.BodyScript.events.on('upload-complete', () => {
    const totalTime = Date.now() - startTime;
    window.BodyScript.utils.log(`Upload completed in ${totalTime}ms`);
  });
}

/**
 * Setup keyboard shortcuts for upload
 */
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Only handle if not typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
      return;
    }

    switch (e.key) {
      case 'u':
      case 'U':
        // Trigger file input
        if (!e.ctrlKey && !e.metaKey) {
          const fileInput = document.getElementById('fileInput');
          if (fileInput && !fileInput.disabled) {
            fileInput.click();
            e.preventDefault();
          }
        }
        break;

      case 'Enter':
      case ' ':
        // Start processing if file is ready
        const processBtn = document.getElementById('processBtn');
        if (processBtn && !processBtn.disabled && !processBtn.classList.contains('hidden')) {
          processBtn.click();
          e.preventDefault();
        }
        break;

      case 'Escape':
        // Cancel current operation or reset
        const resetBtn = document.getElementById('resetBtn');
        if (resetBtn && !resetBtn.classList.contains('hidden')) {
          resetBtn.click();
          e.preventDefault();
        }
        break;

      case 'd':
      case 'D':
        // Download results (if available)
        if (e.ctrlKey || e.metaKey) {
          const downloadBtn = document.getElementById('downloadVideo');
          if (downloadBtn && !downloadBtn.disabled) {
            downloadBtn.click();
            e.preventDefault();
          }
        }
        break;
    }
  });
}

/**
 * Enhanced drag and drop
 */
function setupDragAndDropEnhancements() {
  const dropZone = document.getElementById('dropZone');
  if (!dropZone) return;

  let dragCounter = 0;

  // Prevent default drag behaviors
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    document.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  // Handle drag enter/leave for visual feedback
  document.addEventListener('dragenter', (e) => {
    dragCounter++;
    if (e.dataTransfer.types.includes('Files')) {
      document.body.classList.add('drag-active');
      dropZone.classList.add('drag-over');
    }
  });

  document.addEventListener('dragleave', () => {
    dragCounter--;
    if (dragCounter === 0) {
      document.body.classList.remove('drag-active');
      dropZone.classList.remove('drag-over');
    }
  });

  // Handle drop
  document.addEventListener('drop', (e) => {
    dragCounter = 0;
    document.body.classList.remove('drag-active');
    dropZone.classList.remove('drag-over');

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      // Only process the first video file
      const videoFile = files.find(file => file.type.startsWith('video/'));
      if (videoFile) {
        window.BodyScript.events.emit('file-selected', videoFile);
      }
    }
  });
}

/**
 * Setup accessibility features
 */
function setupAccessibility() {
  // Announce upload progress to screen readers
  window.BodyScript.events.on('upload-progress', (data) => {
    if (data.percent % 10 === 0) { // Announce every 10%
      announceToScreenReader(`Upload progress: ${data.percent}%`);
    }
  });

  // Announce upload completion
  window.BodyScript.events.on('upload-complete', () => {
    announceToScreenReader('Upload completed successfully');
  });

  // Announce file validation results
  window.BodyScript.events.on('file-validated', ({ validation }) => {
    if (!validation.valid) {
      announceToScreenReader(`File validation failed: ${validation.errors.join(', ')}`);
    }
  });

  // Enhanced focus management
  setupFocusManagement();
}

/**
 * Enhanced focus management for upload flow
 */
function setupFocusManagement() {
  // Focus management for upload states
  window.BodyScript.events.on('file-selected', () => {
    setTimeout(() => {
      const processBtn = document.getElementById('processBtn');
      if (processBtn && !processBtn.classList.contains('hidden')) {
        processBtn.focus();
      }
    }, 100);
  });

  window.BodyScript.events.on('upload-complete', () => {
    setTimeout(() => {
      const downloadBtn = document.getElementById('downloadVideo');
      if (downloadBtn) {
        downloadBtn.focus();
      }
    }, 100);
  });
}

/**
 * Announce text to screen readers
 */
function announceToScreenReader(text) {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.textContent = text;

  document.body.appendChild(announcement);

  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}