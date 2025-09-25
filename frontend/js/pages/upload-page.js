// Upload page controller - Main integration module

import {
  uploadVideo,
  checkStatus,
  checkAPIHealth,
  cancelJobBeacon,
  getDownloadUrls,
  downloadFile,
  pollJobStatus
} from '../api/upload.js';

import { initProgressBar, updateProgress, showProgressAnimation } from '../components/progress-bar.js';
import { initFileHandler, getSelectedFile, removeFile } from '../components/file-handler.js';
import { initVideoModal, setupResultVideo } from '../components/video-modal.js';
import {
  initStatusUpdater,
  updateStatus,
  updateStatusStep,
  addOutputLine,
  showResults
} from '../components/status-updater.js';

import { $, addClass, removeClass } from '../utils/dom-helpers.js';
import { formatFileSize } from '../utils/format-helpers.js';

// Store current job ID for downloads
let currentJobId = null;
let processingComplete = false;

/**
 * Process the selected video file
 */
async function processVideo() {
  const selectedFile = getSelectedFile();
  if (!selectedFile) {
    console.log('No file selected');
    return;
  }

  console.log('Selected file:', selectedFile.name, selectedFile.size);
  updateStatus('processing', 'Starting pose detection pipeline', 0);

  showProgressAnimation();
  const processBtn = $('#processBtn');
  if (processBtn) addClass(processBtn, 'hidden');

  processingComplete = false;

  try {
    // Step 1: Upload video
    updateStatus('uploading', 'Uploading video to server...', 0);
    console.log('API URL:', window.API_URL);
    console.log('Upload endpoint:', `${window.API_URL}/api/upload`);

    const uploadData = await uploadVideo(selectedFile);
    currentJobId = uploadData.job_id;

    // Set up cancellation on window close
    const handleBeforeUnload = (e) => {
      if (currentJobId && !processingComplete) {
        cancelJobBeacon(currentJobId);
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    updateStatusStep('step1', true, '[✓] Upload complete');
    updateStatus('processing', 'Extracting frames...', 25);

    // Step 2-5: Poll for status
    let lastStep = 1;

    const finalStatus = await pollJobStatus(currentJobId, (status) => {
      if (status.status === 'processing') {
        const progress = status.progress || 0;
        updateStatus(
          'processing',
          `Processing frame ${status.current_frame || '?'}/${status.total_frames || '?'}`,
          progress
        );

        // Update progress display
        updateProgress(progress, status.current_frame, status.total_frames);

        // Update steps based on progress
        if (progress > 24 && lastStep < 2) {
          updateStatusStep('step2', true, '[✓] Frames extracted');
          lastStep = 2;
        }
        if (progress > 75 && lastStep < 3) {
          updateStatusStep('step3', true, '[✓] Pose detection complete');
          lastStep = 3;
        }
        if (progress > 85 && lastStep < 4) {
          updateStatusStep('step4', true, '[✓] Overlay generated');
          lastStep = 4;
        }
        if (progress > 90 && lastStep < 5) {
          updateStatusStep('step5', true, '[✓] Finalizing output');
          updateStatus('processing', 'Finalizing output...', 95);
          lastStep = 5;
        }
      }
    });

    // Processing complete
    processingComplete = true;
    window.removeEventListener('beforeunload', handleBeforeUnload);

    updateStatusStep('step5', true, '[✓] Processing complete');
    updateStatus('success', 'Processing complete!', 100);

    // Show results
    console.log('Processing complete. Final status:', finalStatus);
    console.log('URLs from status:', finalStatus.urls);
    showResults(finalStatus, selectedFile);
    setupDownloadButtons(finalStatus);

  } catch (error) {
    processingComplete = true;
    updateStatus('error', error.message);

    const processBtn = $('#processBtn');
    if (processBtn) removeClass(processBtn, 'hidden');

    console.error('Processing error:', error);
  }
}

/**
 * Set up download buttons for results
 */
function setupDownloadButtons(status) {
  if (!currentJobId) return;

  // Use URLs from status response if available, otherwise fall back to generated URLs
  const urls = status?.urls || getDownloadUrls(currentJobId);
  const selectedFile = getSelectedFile();

  console.log('Setting up download buttons with URLs:', urls);
  console.log('Video URL to be used:', urls.video);

  // Set up video player
  setupResultVideo(urls.video);

  // Set up download buttons
  const videoBtn = $('#downloadVideo');
  const poseDataBtn = $('#downloadPoseData');

  if (videoBtn) {
    videoBtn.onclick = () => {
      downloadFile(urls.video, `processed_${selectedFile.name}`);
    };
  }

  if (poseDataBtn) {
    poseDataBtn.onclick = () => {
      // Download CSV
      downloadFile(
        urls.csv,
        `pose_data_${selectedFile.name.replace(/\.[^/.]+$/, '')}.csv`
      );
    };
  }
}

/**
 * Initialize the upload page
 */
async function initUploadPage() {
  console.log('Initializing upload page...');

  // Initialize all components
  initStatusUpdater();
  initProgressBar();
  initFileHandler();
  initVideoModal();

  // Set up process button handler
  const processBtn = $('#processBtn');
  if (processBtn) {
    processBtn.addEventListener('click', async () => {
      console.log('Process button clicked');
      const selectedFile = getSelectedFile();

      if (!selectedFile) {
        console.log('No file selected');
        return;
      }

      updateStatus('processing', 'Checking server...');

      // Check API health first
      let health;
      try {
        health = await checkAPIHealth(false);
      } catch (error) {
        console.error('Health check error:', error);
        addOutputLine('[ERROR] Failed to check server status', 'error');
        addOutputLine(`> ${error.message}`, 'error');
        health = { healthy: true, coldStart: false, uptime: 0 };
      }

      // Update status based on health check
      if (health.coldStart) {
        updateStatus('warning', 'Server starting up - this may take 30-60 seconds...');
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      // Process video
      await processVideo();
    });
  }

  // Set up reset button
  const resetBtn = $('#resetBtn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      location.reload();
    });
  }

  // Initial status
  updateStatus('ready', 'Waiting for video upload');
  console.log('Upload page ready');
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initUploadPage);
} else {
  // DOM already loaded
  initUploadPage();
}