# BodyScript Video Gallery - 3 Design Options

## Overview
All options include:
- **Gallery Page**: Showcase skeleton overlay results
- **Demo Page**: User upload functionality
- **9:16 Ratio**: Vertical video format (like TikTok/Reels)
- **Hover Preview**: 3-second autoplay on hover
- **Click to Play**: Full-screen modal player

---

## Option 1: Terminal Grid Gallery
**Theme**: Developer-focused, code aesthetic

### Gallery Page Layout
```
┌─────────────────────────────────────────────┐
│  [Terminal Header]                          │
│  $ bodyscript showcase --filter=dance      │
│                                            │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐     │
│  │9:16│ │9:16│ │9:16│ │9:16│ │9:16│     │
│  │vid │ │vid │ │vid │ │vid │ │vid │     │
│  └────┘ └────┘ └────┘ └────┘ └────┘     │
│  dance  martial parkour yoga  ballet      │
│  98.2%  95.1%  92.3%  96.8%  94.5%       │
│                                            │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐     │
│  │9:16│ │9:16│ │9:16│ │9:16│ │9:16│     │
│  └────┘ └────┘ └────┘ └────┘ └────┘     │
└─────────────────────────────────────────────┘
```

### Features
- **Terminal-style header** with command prompt
- **5 columns grid** on desktop, 3 on tablet, 1 on mobile
- **Monospace labels** with detection accuracy percentage
- **Green glow effect** on hover (terminal green: #27c93f)
- **ASCII progress bar** during hover preview load

### Video Card HTML Structure
```html
<div class="terminal-card">
  <div class="video-container ratio-9-16">
    <video class="preview-video" muted loop>
      <source src="dance-preview.mp4" type="video/mp4">
    </video>
    <img class="thumbnail" src="dance-thumb.jpg" alt="Dance">
    <div class="hover-indicator">
      <span class="ascii-play">▶</span>
    </div>
  </div>
  <div class="terminal-info">
    <span class="filename">dance_overlay.mp4</span>
    <span class="accuracy">98.2% detected</span>
    <div class="ascii-bar">████████░░</div>
  </div>
</div>
```

### CSS Styling
```css
.terminal-card {
  background: var(--bg-terminal);
  border: 1px solid var(--border-secondary);
  border-radius: 4px;
  font-family: var(--font-mono);
}

.ratio-9-16 {
  aspect-ratio: 9/16;
  position: relative;
  overflow: hidden;
  background: #0a0a0a;
}

.terminal-card:hover {
  border-color: var(--text-terminal-green);
  box-shadow: 0 0 20px rgba(39, 201, 63, 0.3);
}

.terminal-card:hover .preview-video {
  display: block;
  animation: glitch 0.1s;
}

@keyframes glitch {
  0%, 100% { transform: translate(0); }
  20% { transform: translate(-1px, 1px); }
  40% { transform: translate(1px, -1px); }
  60% { transform: translate(-1px, 0); }
}
```

---

## Option 2: Premium Glass Cards
**Theme**: Modern, elegant, glassmorphism

### Gallery Page Layout
```
┌─────────────────────────────────────────────┐
│  BodyScript Gallery                        │
│  ─────────────────                         │
│  Showcase of AI-Powered Pose Detection     │
│                                            │
│  [All] [Dance] [Sports] [Yoga] [Combat]    │
│                                            │
│  ╭────╮ ╭────╮ ╭────╮ ╭────╮             │
│  │9:16│ │9:16│ │9:16│ │9:16│             │
│  │ ◆  │ │ ◆  │ │ ◆  │ │ ◆  │             │
│  ╰────╯ ╰────╯ ╰────╯ ╰────╯             │
│  Contemporary  Ballet  Hip-Hop  Salsa      │
│  2.3M views    1.8M    3.1M    890K       │
│                                            │
│  ╭────╮ ╭────╮ ╭────╮ ╭────╮             │
│  │9:16│ │9:16│ │9:16│ │9:16│             │
│  ╰────╯ ╰────╯ ╰────╯ ╰────╯             │
└─────────────────────────────────────────────┘
```

### Features
- **Glass morphism cards** with blur backdrop
- **4 columns grid** with generous spacing
- **Smooth gradient borders** (green to teal)
- **Floating play button** with premium feel
- **View count** like social platforms
- **Category filters** with smooth transitions

### Video Card HTML Structure
```html
<div class="glass-card">
  <div class="gradient-border"></div>
  <div class="video-wrapper ratio-9-16">
    <video class="preview-video" muted>
      <source src="preview.mp4" type="video/mp4">
    </video>
    <img class="thumbnail" src="thumb.jpg" loading="lazy">
    <div class="play-overlay">
      <div class="play-button">
        <svg><!-- play icon --></svg>
      </div>
    </div>
    <div class="video-badge">
      <span class="quality">4K</span>
      <span class="duration">0:45</span>
    </div>
  </div>
  <div class="card-info">
    <h3 class="video-title">Contemporary Dance</h3>
    <p class="video-stats">
      <span>2.3M views</span>
      <span>•</span>
      <span>98% accuracy</span>
    </p>
  </div>
</div>
```

### CSS Styling
```css
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
  position: relative;
}

.gradient-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #22c55e, #10b981);
  opacity: 0;
  transition: opacity 0.3s;
}

.glass-card:hover .gradient-border {
  opacity: 1;
}

.glass-card:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-4px);
  box-shadow:
    0 20px 40px rgba(0, 0, 0, 0.2),
    0 0 40px rgba(34, 197, 94, 0.1);
}

.play-button {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #22c55e, #10b981);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.glass-card:hover .play-button {
  transform: scale(1.1);
  box-shadow: 0 0 30px rgba(34, 197, 94, 0.5);
}
```

---

## Option 3: TikTok-Style Infinite Scroll
**Theme**: Social media inspired, mobile-first

### Gallery Page Layout
```
┌─────────────────────────────────────────────┐
│  BodyScript                    [Try Demo]  │
│  ─────────────────────────────────────────  │
│                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │          │ │          │ │          │  │
│  │   9:16   │ │   9:16   │ │   9:16   │  │
│  │          │ │          │ │          │  │
│  │  ▶ LIVE  │ │          │ │          │  │
│  │          │ │          │ │          │  │
│  │    ♥     │ │    ♥     │ │    ♥     │  │
│  │   12.3k  │ │   8.9k   │ │   15.2k  │  │
│  │    💬    │ │    💬    │ │    💬    │  │
│  │   234    │ │   189    │ │   445    │  │
│  │    ↗     │ │    ↗     │ │    ↗     │  │
│  └──────────┘ └──────────┘ └──────────┘  │
│  @dance_pro   @yoga_master @parkour_ace   │
│                                            │
│  ↓ Scroll for more                        │
└─────────────────────────────────────────────┘
```

### Features
- **3 columns** on desktop, single column on mobile
- **Infinite scroll** with lazy loading
- **Social interactions** (like, comment, share buttons)
- **Live indicator** for currently playing
- **Username tags** for attribution
- **Smooth autoplay** on scroll into view
- **Swipe gestures** on mobile

### Video Card HTML Structure
```html
<div class="tiktok-card">
  <div class="video-container ratio-9-16">
    <video class="main-video"
           muted
           loop
           playsinline
           data-autoplay>
      <source src="video.mp4" type="video/mp4">
    </video>

    <div class="overlay-gradient"></div>

    <div class="video-info">
      <div class="creator">
        <img class="avatar" src="avatar.jpg" alt="">
        <span class="username">@dance_pro</span>
        <button class="follow-btn">Follow</button>
      </div>

      <div class="description">
        <p>Contemporary dance with 98.2% pose accuracy</p>
        <div class="tags">
          <span>#bodyscript</span>
          <span>#posedetection</span>
          <span>#dance</span>
        </div>
      </div>
    </div>

    <div class="interaction-buttons">
      <button class="interaction-btn">
        <span class="icon">♥</span>
        <span class="count">12.3k</span>
      </button>
      <button class="interaction-btn">
        <span class="icon">💬</span>
        <span class="count">234</span>
      </button>
      <button class="interaction-btn">
        <span class="icon">↗</span>
        <span class="count">Share</span>
      </button>
    </div>

    <div class="progress-bar">
      <div class="progress-fill"></div>
    </div>
  </div>
</div>
```

### CSS Styling
```css
.tiktok-card {
  background: #000;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.ratio-9-16 {
  aspect-ratio: 9/16;
  position: relative;
  background: #111;
}

.overlay-gradient {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
  pointer-events: none;
}

.video-info {
  position: absolute;
  bottom: 20px;
  left: 20px;
  right: 60px;
  color: white;
  z-index: 2;
}

.interaction-buttons {
  position: absolute;
  right: 10px;
  bottom: 80px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 3;
}

.interaction-btn {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(8px);
  border: none;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.interaction-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}

.interaction-btn:active {
  transform: scale(0.95);
}

.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(255, 255, 255, 0.2);
}

.progress-fill {
  height: 100%;
  background: var(--color-success);
  width: 0%;
  transition: width linear;
}

/* Auto-play on scroll into view */
.tiktok-card.in-view .main-video {
  display: block;
}

.tiktok-card.in-view .progress-fill {
  animation: progress 3s linear;
}

@keyframes progress {
  from { width: 0%; }
  to { width: 100%; }
}
```

---

## Demo Upload Page (Shared Across All Options)

### Layout
```
┌─────────────────────────────────────────────┐
│  Try BodyScript Demo                       │
│  ─────────────────────                     │
│                                            │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐                 │
│  │                       │                 │
│  │    Drop Video Here    │                 │
│  │         or            │                 │
│  │    [Choose File]      │                 │
│  │                       │                 │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘                 │
│                                            │
│  Requirements:                             │
│  • Max 15 seconds                          │
│  • MP4 format                              │
│  • Max 50MB                                │
│                                            │
│  [Process Video]                           │
│                                            │
│  ┌─────────────────────┐                  │
│  │ Processing Steps:   │                  │
│  │ 1. Upload ✓         │                  │
│  │ 2. Extract frames   │                  │
│  │ 3. Detect poses     │                  │
│  │ 4. Generate overlay │                  │
│  │ 5. Download result  │                  │
│  └─────────────────────┘                  │
└─────────────────────────────────────────────┘
```

---

## Implementation Notes

### Hover Preview JavaScript
```javascript
// Common hover preview logic for all options
document.querySelectorAll('.video-container').forEach(container => {
  const video = container.querySelector('.preview-video');
  const thumbnail = container.querySelector('.thumbnail');
  let hoverTimeout;

  container.addEventListener('mouseenter', () => {
    hoverTimeout = setTimeout(() => {
      thumbnail.style.display = 'none';
      video.style.display = 'block';
      video.currentTime = 0;
      video.play();

      // Stop after 3 seconds
      setTimeout(() => {
        if (!video.paused) {
          video.pause();
          video.currentTime = 0;
        }
      }, 3000);
    }, 500); // 500ms delay before preview starts
  });

  container.addEventListener('mouseleave', () => {
    clearTimeout(hoverTimeout);
    video.pause();
    video.style.display = 'none';
    thumbnail.style.display = 'block';
  });

  container.addEventListener('click', () => {
    openFullScreenPlayer(video.src);
  });
});
```

### Mobile Optimizations
```css
@media (max-width: 768px) {
  /* Stack videos vertically on mobile */
  .video-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  /* Touch interactions instead of hover */
  .video-container:active .preview-video {
    display: block;
  }

  /* Larger interaction buttons for touch */
  .interaction-btn {
    width: 56px;
    height: 56px;
  }
}
```

### Performance Considerations
1. **Lazy loading**: Load videos only when scrolled into view
2. **Thumbnail first**: Show static image, load video on hover
3. **CDN delivery**: Host videos on CDN for fast delivery
4. **Adaptive quality**: Serve different qualities based on connection
5. **Intersection Observer**: For infinite scroll and autoplay

---

## Recommendation

**For Portfolio/Showcase**: **Option 2 (Premium Glass Cards)**
- Most visually impressive
- Professional appearance
- Good balance of style and functionality
- Fits the existing design system best

**For Developer Audience**: **Option 1 (Terminal Grid)**
- Unique and memorable
- Shows technical expertise
- Fits the coding theme of the project

**For Maximum Engagement**: **Option 3 (TikTok-Style)**
- Most familiar UX pattern
- Best for mobile users
- Encourages longer browsing sessions

---

## Next Steps

1. Choose preferred option
2. I'll create the full HTML/CSS/JS implementation
3. Add sample videos (you provide later)
4. Connect to backend API for demo uploads
5. Deploy to production

Each option can be implemented in ~2-3 hours with full functionality.