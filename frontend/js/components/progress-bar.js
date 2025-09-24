// Progress bar component

import { $, setText } from '../utils/dom-helpers.js';
import { generateProgressBar } from '../utils/format-helpers.js';

/**
 * Update progress bar display
 * @param {number} progress - Progress percentage (0-100)
 * @param {string} currentFrame - Current frame being processed
 * @param {string} totalFrames - Total frames to process
 */
export function updateProgress(progress, currentFrame = null, totalFrames = null) {
  const progressBar = $('#progressBar');
  const progressPercent = $('#progressPercent');
  const currentFrameEl = $('#currentFrame');
  const totalFramesEl = $('#totalFrames');

  if (progressBar && progressPercent) {
    // Calculate bar length based on viewport (responsive)
    const isMobile = window.innerWidth < 768;
    const barLength = isMobile ? 30 : 50;

    // Generate and display progress bar
    const bar = generateProgressBar(progress, barLength);
    setText(progressBar, bar);
    setText(progressPercent, `${Math.round(progress)}%`);
  }

  // Update frame counter if provided
  if (currentFrame && currentFrameEl) {
    setText(currentFrameEl, currentFrame);
  }

  if (totalFrames && totalFramesEl) {
    setText(totalFramesEl, totalFrames);
  }
}

/**
 * Show progress animation section
 */
export function showProgressAnimation() {
  const processingAnimation = $('#processingAnimation');
  if (processingAnimation) {
    processingAnimation.classList.remove('hidden');
    processingAnimation.classList.add('show');
  }
}

/**
 * Hide progress animation section
 */
export function hideProgressAnimation() {
  const processingAnimation = $('#processingAnimation');
  if (processingAnimation) {
    processingAnimation.style.display = 'none';
  }
}

/**
 * Reset progress bar to initial state
 */
export function resetProgress() {
  updateProgress(0, '0', '0');
  hideProgressAnimation();
}

/**
 * Initialize progress bar component
 */
export function initProgressBar() {
  // Set initial state
  resetProgress();

  // Add resize listener to adjust bar length
  window.addEventListener('resize', () => {
    // Re-render progress bar on resize
    const currentPercent = $('#progressPercent');
    if (currentPercent) {
      const progress = parseInt(currentPercent.textContent) || 0;
      updateProgress(progress);
    }
  });

  return {
    update: updateProgress,
    show: showProgressAnimation,
    hide: hideProgressAnimation,
    reset: resetProgress
  };
}