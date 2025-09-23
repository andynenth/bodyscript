/* =====================================================================
   BODYSCRIPT GALLERY - COMMON JAVASCRIPT
   Shared functionality for all gallery options
   ===================================================================== */

// Sample video data (replace with real data later)
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
let currentVideos = [...SAMPLE_VIDEOS];

// Hover preview functionality
function initializeHoverPreview() {
  document.querySelectorAll('.video-card').forEach(card => {
    const container = card.querySelector('.video-container');
    const video = card.querySelector('.preview-video');
    const thumbnail = card.querySelector('.thumbnail');
    const progressBar = card.querySelector('.progress-fill');

    let hoverTimeout;
    let playbackTimeout;

    container.addEventListener('mouseenter', () => {
      hoverTimeout = setTimeout(() => {
        // Show video and hide thumbnail
        thumbnail.style.display = 'none';
        video.style.display = 'block';

        // Reset and play video
        video.currentTime = 0;
        video.play().catch(err => {
          console.log('Autoplay prevented:', err);
          // Fallback to showing thumbnail
          thumbnail.style.display = 'block';
          video.style.display = 'none';
        });

        // Start progress animation
        if (progressBar) {
          progressBar.style.width = '0%';
          progressBar.style.transition = 'none';
          setTimeout(() => {
            progressBar.style.transition = 'width 3s linear';
            progressBar.style.width = '100%';
          }, 50);
        }

        // Stop after 3 seconds
        playbackTimeout = setTimeout(() => {
          video.pause();
          video.currentTime = 0;
        }, 3000);
      }, 500); // 500ms delay before preview starts
    });

    container.addEventListener('mouseleave', () => {
      clearTimeout(hoverTimeout);
      clearTimeout(playbackTimeout);

      // Pause and reset video
      video.pause();
      video.currentTime = 0;

      // Show thumbnail again
      video.style.display = 'none';
      thumbnail.style.display = 'block';

      // Reset progress bar
      if (progressBar) {
        progressBar.style.width = '0%';
      }
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
      // Don't open modal if clicking on buttons
      if (e.target.closest('button')) return;

      const videoId = card.dataset.videoId;
      const video = SAMPLE_VIDEOS.find(v => v.id == videoId);

      if (video) {
        modalVideo.src = video.full;
        modal.classList.add('active');
        modalVideo.play();
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
    currentVideos = [...SAMPLE_VIDEOS];
  } else {
    currentVideos = SAMPLE_VIDEOS.filter(v => v.category === filter);
  }

  // Re-render gallery
  renderGallery();
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
  initializeFullScreenPlayer();
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