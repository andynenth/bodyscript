// Video modal component

import { $, addClass, removeClass } from '../utils/dom-helpers.js';

let modal = null;
let modalVideo = null;
let modalClose = null;
let videoContainer = null;
let resultVideo = null;

/**
 * Open the video modal with the given video source
 * @param {string} videoSrc - The video source URL
 */
export function openModal(videoSrc) {
  if (!modal || !modalVideo) return;

  modalVideo.src = videoSrc;
  addClass(modal, 'active');

  // Pause the small video and play the modal video
  if (resultVideo) {
    resultVideo.pause();
  }

  modalVideo.play().catch(err => {
    console.log('Modal video auto-play prevented:', err);
  });
}

/**
 * Close the video modal
 */
export function closeModal() {
  if (!modal || !modalVideo) return;

  removeClass(modal, 'active');
  modalVideo.pause();
  modalVideo.src = '';

  // Resume the small video
  if (resultVideo) {
    resultVideo.play().catch(err => {
      console.log('Result video auto-play prevented:', err);
    });
  }
}

/**
 * Initialize video modal component
 */
export function initVideoModal() {
  // Get modal elements
  modal = $('.video-modal');
  modalVideo = modal ? modal.querySelector('.modal-video') : null;
  modalClose = modal ? modal.querySelector('.modal-close') : null;
  videoContainer = $('.video-player-container');
  resultVideo = $('#resultVideo');

  if (!modal || !modalVideo || !modalClose) {
    console.warn('Video modal elements not found');
    return null;
  }

  // Click on video container to open modal
  if (videoContainer) {
    videoContainer.addEventListener('click', () => {
      if (resultVideo && resultVideo.src) {
        openModal(resultVideo.src);
      }
    });
  }

  // Close modal handlers
  modalClose.addEventListener('click', closeModal);

  // Click outside modal to close
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  // ESC key to close
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      closeModal();
    }
  });

  return {
    open: openModal,
    close: closeModal
  };
}

/**
 * Set up video player for results
 * @param {string} videoUrl - The video URL
 */
export function setupResultVideo(videoUrl) {
  if (!resultVideo) {
    resultVideo = $('#resultVideo');
  }

  if (resultVideo) {
    resultVideo.src = videoUrl;

    // Ensure video plays automatically
    resultVideo.addEventListener('loadeddata', () => {
      resultVideo.play().catch(err => {
        console.log('Auto-play prevented:', err);
      });
    }, { once: true });
  }
}