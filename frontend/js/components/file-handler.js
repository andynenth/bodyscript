// File handler component

import { $, setText, addClass, removeClass, show, hide } from '../utils/dom-helpers.js';
import { formatFileSize, formatDuration } from '../utils/format-helpers.js';
import { updateStatus } from './status-updater.js';

let selectedFile = null;

/**
 * Get the currently selected file
 * @returns {File|null} The selected file
 */
export function getSelectedFile() {
  return selectedFile;
}

/**
 * Validate file type and size
 * @param {File} file - The file to validate
 * @returns {Object} Validation result
 */
export function validateFile(file) {
  const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo'];
  const maxSize = 50 * 1024 * 1024; // 50MB

  if (!validTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'Invalid file format. Use MP4, MOV, or AVI.'
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: 'File exceeds 50MB limit.'
    };
  }

  return { valid: true };
}

/**
 * Handle file selection
 * @param {File} file - The selected file
 */
export function handleFile(file) {
  updateStatus('processing', `Analyzing file: ${file.name}`);

  // Validate file
  const validation = validateFile(file);
  if (!validation.valid) {
    updateStatus('error', validation.error);
    return;
  }

  selectedFile = file;

  // Display file info
  setText($('#fileName'), file.name);
  setText($('#fileSize'), formatFileSize(file.size));

  // Create video element to get metadata
  const video = document.createElement('video');
  video.src = URL.createObjectURL(file);

  video.addEventListener('loadedmetadata', () => {
    setText($('#fileDuration'), formatDuration(video.duration));
    setText($('#fileResolution'), `${video.videoWidth}x${video.videoHeight}`);

    if (video.duration > 15) {
      updateStatus('warning', 'Video exceeds 15s. Will be trimmed.');
      setTimeout(() => {
        updateStatus('success', `File loaded: ${file.name}`);
      }, 2000);
    } else {
      updateStatus('success', `File loaded: ${file.name}`);
    }

    // Clean up
    URL.revokeObjectURL(video.src);
  });

  // Update UI
  const dropZone = $('#dropZone');
  const fileDisplay = $('#fileDisplay');
  const processBtn = $('#processBtn');

  if (dropZone) addClass(dropZone, 'has-file');
  if (fileDisplay) {
    fileDisplay.style.display = 'block';
    addClass(fileDisplay, 'show');
  }
  if (processBtn) removeClass(processBtn, 'hidden');
}

/**
 * Remove selected file and reset UI
 */
export function removeFile() {
  selectedFile = null;

  const fileDisplay = $('#fileDisplay');
  const dropZone = $('#dropZone');
  const processBtn = $('#processBtn');
  const fileInput = $('#fileInput');

  if (fileDisplay) {
    removeClass(fileDisplay, 'show');
    fileDisplay.style.display = 'none';
  }

  if (dropZone) {
    removeClass(dropZone, 'has-file');
    dropZone.style.display = 'block';
  }

  if (processBtn) addClass(processBtn, 'hidden');
  if (fileInput) fileInput.value = '';

  // Reset file details
  setText($('#fileName'), '');
  setText($('#fileSize'), '');
  setText($('#fileDuration'), '--:--');
  setText($('#fileResolution'), '----x----');
  setText($('#fileFrameRate'), '-- fps');

  updateStatus('ready', 'Waiting for video upload');
}

/**
 * Initialize file handler component
 */
export function initFileHandler() {
  const dropZone = $('#dropZone');
  const fileInput = $('#fileInput');
  const removeBtn = $('#removeBtn');
  const detailsToggle = $('#detailsToggle');
  const fileDetails = $('#fileDetails');

  // Drag and drop handlers
  if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      addClass(dropZone, 'dragover');
    });

    dropZone.addEventListener('dragleave', () => {
      removeClass(dropZone, 'dragover');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      removeClass(dropZone, 'dragover');
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFile(files[0]);
      }
    });
  }

  // File input handler
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
      }
    });
  }

  // Remove button handler
  if (removeBtn) {
    removeBtn.addEventListener('click', removeFile);
  }

  // Details toggle functionality
  if (detailsToggle && fileDetails) {
    detailsToggle.addEventListener('click', () => {
      const isExpanded = !fileDetails.classList.contains('hidden');

      if (isExpanded) {
        addClass(fileDetails, 'hidden');
      } else {
        removeClass(fileDetails, 'hidden');
      }

      toggleClass(detailsToggle, 'expanded');
      detailsToggle.innerHTML = isExpanded ?
        '<span class="toggle-icon">▼</span> Show Details' :
        '<span class="toggle-icon">▼</span> Hide Details';
    });
  }

  return {
    getSelectedFile,
    handleFile,
    removeFile,
    validateFile
  };
}

function toggleClass(element, className) {
  if (!element) return;
  element.classList.toggle(className);
}