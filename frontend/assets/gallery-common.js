/* =====================================================================
   BODYSCRIPT GALLERY - COMMON JAVASCRIPT
   Shared functionality for all gallery options
   ===================================================================== */

// Load gallery data dynamically
let GALLERY_VIDEOS = [];

// Sample fallback data
const SAMPLE_VIDEOS = [
  {
    id: 1,
    title: "Contemporary Dance",
    category: "dance",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Dance",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 98.2,
    views: "2.3M",
    likes: "12.3k",
    comments: 234,
    duration: "0:45",
    username: "@dance_pro",
    tags: ["#bodyscript", "#posedetection", "#dance"]
  },
  {
    id: 2,
    title: "Martial Arts Form",
    category: "sports",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Martial+Arts",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 95.1,
    views: "1.8M",
    likes: "8.9k",
    comments: 189,
    duration: "0:38",
    username: "@martial_master",
    tags: ["#bodyscript", "#martialarts", "#sports"]
  },
  {
    id: 3,
    title: "Parkour Sequence",
    category: "sports",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Parkour",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 92.3,
    views: "3.1M",
    likes: "15.2k",
    comments: 445,
    duration: "0:52",
    username: "@parkour_ace",
    tags: ["#bodyscript", "#parkour", "#movement"]
  },
  {
    id: 4,
    title: "Yoga Flow",
    category: "yoga",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Yoga",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 96.8,
    views: "890k",
    likes: "7.2k",
    comments: 156,
    duration: "1:20",
    username: "@yoga_master",
    tags: ["#bodyscript", "#yoga", "#wellness"]
  },
  {
    id: 5,
    title: "Ballet Performance",
    category: "dance",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Ballet",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 94.5,
    views: "1.5M",
    likes: "9.8k",
    comments: 267,
    duration: "1:05",
    username: "@ballet_artist",
    tags: ["#bodyscript", "#ballet", "#classical"]
  },
  {
    id: 6,
    title: "Hip Hop Freestyle",
    category: "dance",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Hip+Hop",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 93.7,
    views: "4.2M",
    likes: "22.1k",
    comments: 892,
    duration: "0:35",
    username: "@hiphop_king",
    tags: ["#bodyscript", "#hiphop", "#freestyle"]
  },
  {
    id: 7,
    title: "Tai Chi Practice",
    category: "martial",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Tai+Chi",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 97.1,
    views: "670k",
    likes: "5.4k",
    comments: 98,
    duration: "1:15",
    username: "@taichi_master",
    tags: ["#bodyscript", "#taichi", "#mindfulness"]
  },
  {
    id: 8,
    title: "Boxing Training",
    category: "sports",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Boxing",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 91.8,
    views: "2.7M",
    likes: "14.3k",
    comments: 523,
    duration: "0:42",
    username: "@boxing_coach",
    tags: ["#bodyscript", "#boxing", "#training"]
  },
  {
    id: 9,
    title: "Salsa Dancing",
    category: "dance",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Salsa",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 95.6,
    views: "1.1M",
    likes: "8.7k",
    comments: 201,
    duration: "0:55",
    username: "@salsa_dancer",
    tags: ["#bodyscript", "#salsa", "#latin"]
  },
  {
    id: 10,
    title: "Gymnastics Routine",
    category: "sports",
    thumbnail: "https://via.placeholder.com/405x720/1a1a1a/666?text=Gymnastics",
    preview: "sample-preview.mp4",
    full: "sample-full.mp4",
    accuracy: 94.2,
    views: "3.5M",
    likes: "18.6k",
    comments: 612,
    duration: "0:48",
    username: "@gym_star",
    tags: ["#bodyscript", "#gymnastics", "#sports"]
  }
];

// Current filter state
let currentFilter = 'all';
let currentVideos = [];

// Hover preview functionality with lazy loading
function initializeHoverPreview() {
  document.querySelectorAll('.video-card').forEach(card => {
    const container = card.querySelector('.video-container');
    const thumbnail = card.querySelector('.thumbnail');

    let hoverTimeout;
    let playbackTimeout;
    let previewVideo = null;
    let isCreating = false;

    container.addEventListener('mouseenter', () => {
      clearTimeout(hoverTimeout);
      hoverTimeout = setTimeout(() => {
        // Create video element on-demand if it doesn't exist
        if (!previewVideo && !isCreating) {
          const previewUrl = card.dataset.videoPreview;
          if (!previewUrl) {
            console.log('[HOVER] No preview URL found on card:', card);
            return;
          }

          isCreating = true;
          console.log('[HOVER] Creating video element for:', previewUrl);

          // Check if URL needs API_URL prefix
          let fullPreviewUrl = previewUrl;
          if (previewUrl.startsWith('/api/')) {
            fullPreviewUrl = `${window.API_URL || 'http://localhost:8000'}${previewUrl}`;
            console.log('[HOVER] Adjusted preview URL to:', fullPreviewUrl);
          }

          previewVideo = document.createElement('video');
          previewVideo.className = 'preview-video';
          previewVideo.muted = true;
          previewVideo.loop = true;
          previewVideo.playsInline = true;
          previewVideo.preload = 'auto';
          previewVideo.style.display = 'none';
          previewVideo.style.position = 'absolute';
          previewVideo.style.top = '0';
          previewVideo.style.left = '0';
          previewVideo.style.width = '100%';
          previewVideo.style.height = '100%';
          previewVideo.style.objectFit = 'cover';
          previewVideo.style.zIndex = '10';  // Ensure it's above the thumbnail

          const source = document.createElement('source');
          source.src = fullPreviewUrl;
          source.type = 'video/mp4';
          previewVideo.appendChild(source);

          container.appendChild(previewVideo);
          console.log('[HOVER] Video element added to container');

          // Add error handler
          previewVideo.addEventListener('error', (e) => {
            console.error('[HOVER] Video error:', e);
            console.error('[HOVER] Video error detail:', previewVideo.error);
            isCreating = false;
          });

          // Wait for video to be ready then play
          previewVideo.addEventListener('canplay', function onCanPlay() {
            console.log('[HOVER] Video can play, hover state:', container.matches(':hover'));
            previewVideo.removeEventListener('canplay', onCanPlay);
            isCreating = false;

            // Only play if still hovering
            if (container.matches(':hover')) {
              console.log('[HOVER] Attempting to play video');
              thumbnail.style.display = 'none';
              previewVideo.style.display = 'block';
              previewVideo.currentTime = 0;
              previewVideo.play().then(() => {
                console.log('[HOVER] Video playing successfully');
              }).catch(err => {
                console.error('[HOVER] Play failed:', err);
                thumbnail.style.display = 'block';
                previewVideo.style.display = 'none';
              });
            }
          });

          // Load the video
          previewVideo.load();
        } else if (previewVideo && !isCreating) {
          // Video already exists, just play it
          thumbnail.style.display = 'none';
          previewVideo.style.display = 'block';
          previewVideo.currentTime = 0;
          previewVideo.play().catch(err => {
            console.log('[HOVER] Play failed:', err);
            thumbnail.style.display = 'block';
            previewVideo.style.display = 'none';
          });
        }

        // Stop after 3 seconds
        playbackTimeout = setTimeout(() => {
          if (previewVideo) {
            previewVideo.pause();
            previewVideo.currentTime = 0;
          }
        }, 3000);
      }, 500); // 500ms delay before preview starts
    });

    container.addEventListener('mouseleave', () => {
      clearTimeout(hoverTimeout);
      clearTimeout(playbackTimeout);

      if (previewVideo) {
        // Pause and reset video
        previewVideo.pause();
        previewVideo.currentTime = 0;
        previewVideo.style.display = 'none';
      }

      // Show thumbnail again
      thumbnail.style.display = 'block';

      // Clean up video element after a delay to free resources
      setTimeout(() => {
        if (previewVideo && !container.matches(':hover')) {
          previewVideo.remove();
          previewVideo = null;
        }
      }, 1000);
    });
  });
}

// Full screen player
function initializeFullScreenPlayer() {
  // Create modal if it doesn't exist
  if (!document.querySelector('.modal')) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
      <div class="modal-content">
        <button class="modal-close">×</button>
        <video class="modal-video" controls>
          <source src="" type="video/mp4">
        </video>
      </div>
    `;
    document.body.appendChild(modal);
  }

  const modal = document.querySelector('.modal');
  const modalVideo = modal.querySelector('.modal-video');
  const modalClose = modal.querySelector('.modal-close');

  // Open modal on card click
  document.querySelectorAll('.video-card').forEach(card => {
    card.addEventListener('click', (e) => {
      // Don't open modal if clicking on buttons or tags
      if (e.target.closest('button') || e.target.classList.contains('tag')) return;

      // Use dataset attributes instead of looking up in array
      const videoFull = card.dataset.videoFull;
      const videoTitle = card.dataset.videoTitle;

      console.log('[MODAL] Opening video:', videoTitle, 'URL:', videoFull);

      if (videoFull) {
        modalVideo.src = videoFull;
        modal.classList.add('active');
        modalVideo.play().catch(err => {
          console.error('[MODAL] Failed to play video:', err);
        });
      } else {
        console.error('[MODAL] No video URL found on card');
      }
    });
  });

  // Close modal
  modalClose.addEventListener('click', () => {
    modal.classList.remove('active');
    modalVideo.pause();
    modalVideo.src = '';
  });

  // Close on background click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('active');
      modalVideo.pause();
      modalVideo.src = '';
    }
  });

  // Close on ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('active')) {
      modal.classList.remove('active');
      modalVideo.pause();
      modalVideo.src = '';
    }
  });
}

// Filter functionality
function initializeFilters() {
  const filterButtons = document.querySelectorAll('.filter-btn');

  filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      // Update active state
      filterButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Filter videos
      const filter = btn.dataset.filter;
      filterVideos(filter);
    });
  });
}

function filterVideos(filter) {
  currentFilter = filter;

  if (filter === 'all') {
    currentVideos = [...GALLERY_VIDEOS];
  } else {
    currentVideos = GALLERY_VIDEOS.filter(v => v.category === filter);
  }

  // Re-render gallery
  renderGallery();
}

// Load gallery data from API or use samples
async function loadGalleryData() {
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Try to load from local API
    try {
      const response = await fetch(`${window.API_URL || 'http://localhost:8000'}/api/gallery`);
      if (response.ok) {
        const data = await response.json();
        if (data.videos && data.videos.length > 0) {
          // Fix URLs to use backend API URL
          GALLERY_VIDEOS = data.videos.map(video => ({
            ...video,
            thumbnail: video.thumbnail.startsWith('/') ? `${window.API_URL}${video.thumbnail}` : video.thumbnail,
            preview: video.preview.startsWith('/') ? `${window.API_URL}${video.preview}` : video.preview,
            full: video.full.startsWith('/') ? `${window.API_URL}${video.full}` : video.full
          }));
          console.log('Loaded', GALLERY_VIDEOS.length, 'videos from local API');
          currentVideos = [...GALLERY_VIDEOS];
          // Update window references
          window.GALLERY_VIDEOS = GALLERY_VIDEOS;
          window.currentVideos = currentVideos;
          return;
        }
      }
    } catch (error) {
      console.log('Could not load gallery from API:', error);
    }
  }

  // Fall back to sample data
  GALLERY_VIDEOS = SAMPLE_VIDEOS;
  currentVideos = [...GALLERY_VIDEOS];
  // Update window references
  window.GALLERY_VIDEOS = GALLERY_VIDEOS;
  window.currentVideos = currentVideos;
}

// Render gallery (to be implemented in each option)
function renderGallery() {
  // This will be overridden in each gallery option
  console.log('Rendering gallery with', currentVideos.length, 'videos');
}

// Intersection Observer for lazy loading
function initializeLazyLoading() {
  const options = {
    root: null,
    rootMargin: '50px',
    threshold: 0.01
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const card = entry.target;
        const thumbnail = card.querySelector('.thumbnail');
        const video = card.querySelector('.preview-video');

        // Load thumbnail if it has data-src
        if (thumbnail && thumbnail.dataset.src) {
          thumbnail.src = thumbnail.dataset.src;
          thumbnail.removeAttribute('data-src');
        }

        // Preload video
        if (video && video.dataset.src) {
          video.src = video.dataset.src;
          video.removeAttribute('data-src');
        }

        observer.unobserve(card);
      }
    });
  }, options);

  document.querySelectorAll('.video-card').forEach(card => {
    observer.observe(card);
  });
}

// Touch support for mobile
function initializeTouchSupport() {
  if ('ontouchstart' in window) {
    let touchTimer;

    document.querySelectorAll('.video-card').forEach(card => {
      const video = card.querySelector('.preview-video');
      const thumbnail = card.querySelector('.thumbnail');

      card.addEventListener('touchstart', (e) => {
        touchTimer = setTimeout(() => {
          // Show preview on long press
          thumbnail.style.display = 'none';
          video.style.display = 'block';
          video.play().catch(() => {});
        }, 500);
      });

      card.addEventListener('touchend', () => {
        clearTimeout(touchTimer);
        // Hide preview
        video.pause();
        video.currentTime = 0;
        video.style.display = 'none';
        thumbnail.style.display = 'block';
      });
    });
  }
}

// Format numbers (12345 -> 12.3k)
function formatNumber(num) {
  if (typeof num === 'string') return num;

  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k';
  }
  return num.toString();
}

// Initialize everything
function initializeGallery() {
  initializeHoverPreview();
  // Don't initialize duplicate modal if page has its own
  if (!document.querySelector('.video-modal')) {
    initializeFullScreenPlayer();
  }
  initializeFilters();
  initializeLazyLoading();
  initializeTouchSupport();
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeGallery);
} else {
  initializeGallery();
}

// Export for use in individual gallery pages
window.GalleryCommon = {
  SAMPLE_VIDEOS,
  currentVideos,
  formatNumber,
  filterVideos,
  renderGallery,
  initializeGallery
};

// Also expose the main data arrays to window
window.GALLERY_VIDEOS = GALLERY_VIDEOS;
window.currentVideos = currentVideos;
window.loadGalleryData = loadGalleryData;