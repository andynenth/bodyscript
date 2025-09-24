# CSS Architecture Documentation - BodyScript

## Overview
The CSS architecture follows a modular, component-based approach with clear separation of concerns. All styles are organized into logical layers that build upon each other.

## Architecture Layers

### 1. Base Layer (`/css/base/`)
Foundation styles that other layers build upon.

#### variables.css
Defines all CSS custom properties used throughout the application:
```css
:root {
  /* Colors */
  --primary-color: #27c93f;          /* Terminal green */
  --bg-primary: #0a0a0a;             /* Main background */
  --bg-secondary: #1a1a1a;           /* Secondary background */
  --text-primary: #e8e8e8;           /* Primary text */
  --text-secondary: #a8a8a8;         /* Secondary text */
  --border-primary: #333;            /* Primary borders */

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 2rem;

  /* Typography */
  --font-mono: 'JetBrains Mono', 'Consolas', monospace;
  --font-size-base: 14px;

  /* Animations */
  --transition-speed: 0.3s;
}
```

#### reset.css
Normalizes default browser styles:
- Box-sizing: border-box for all elements
- Removes default margins and paddings
- Sets base font and background

#### typography.css
Typography system and font definitions:
- Font family declarations
- Heading scales
- Text utilities
- Monospace formatting for terminal theme

### 2. Components Layer (`/css/components/`)
Reusable UI component styles that can be used across pages.

#### terminal.css
Terminal window styling for the retro aesthetic:
- `.terminal-container`: Main terminal wrapper
- `.terminal-window`: Window frame
- `.terminal-header`: Window title bar
- `.terminal-dots`: Red, yellow, green window controls
- `.terminal-body`: Content area
- Includes mobile responsiveness (hides dots < 768px)

#### buttons.css
All button variants and states:
- `.btn-primary`: Main action buttons
- `.btn-secondary`: Secondary actions
- `.terminal-btn`: Terminal-styled buttons
- `.process-btn`: Upload processing button
- Hover states with glow effects
- Disabled states
- Mobile touch target optimization (min 44px)

#### progress.css
Progress indicators and status displays:
- `.progress-container`: Progress wrapper
- `.progress-bar-ascii`: ASCII-style progress bar
- `.progress-percent`: Percentage display
- `.status-component`: Status message area
- `.status-icon`: Animated status indicators
- Mobile width adjustments (30 chars on mobile)

#### forms.css
Form elements and file upload:
- `.drop-zone`: Drag-and-drop area
- `.file-display`: Selected file information
- `.file-header`: File metadata display
- `.status-badge`: File status indicators
- Drag-over visual feedback
- Mobile-optimized layouts

#### modal.css
Modal dialogs and video player:
- `.video-modal`: Full-screen overlay
- `.modal-content`: Content wrapper
- `.modal-video`: Video element styling
- `.modal-close`: Close button
- `.video-player-container`: Video preview
- Responsive video sizing

### 3. Pages Layer (`/css/pages/`)
Page-specific styles that aren't reusable components.

#### upload.css
Upload page specific styles:
- Processing animations
- Results display section
- Download components
- Mobile-specific overrides
- ASCII art positioning

#### gallery.css
Gallery page specific styles:
- Video grid layout (5 columns desktop, responsive)
- Category filtering
- Terminal navigation
- Video card hover effects
- Stats display

### 4. Main Orchestrator (`/css/main.css`)
Controls the import order and cascade:
```css
/* Base - Must load first */
@import './base/variables.css';
@import './base/reset.css';
@import './base/typography.css';

/* Components - Can load in any order */
@import './components/terminal.css';
@import './components/buttons.css';
@import './components/progress.css';
@import './components/forms.css';
@import './components/modal.css';

/* Pages load separately in HTML */
```

## Responsive Design Strategy

### Breakpoints
```css
/* Desktop first approach */
@media (max-width: 1200px) { /* Large tablets */ }
@media (max-width: 968px)  { /* Tablets */ }
@media (max-width: 768px)  { /* Mobile landscape */ }
@media (max-width: 640px)  { /* Mobile portrait */ }
@media (max-width: 480px)  { /* Small mobile */ }
```

### Mobile Optimizations
- Touch targets minimum 44px
- Buttons stack vertically
- Progress bar width reduced
- Terminal decorations hidden
- Font sizes adjusted for readability
- No horizontal scroll

## Animation Guidelines

### Transitions
Standard timing for consistency:
```css
transition: all 0.3s ease;
transition: opacity 0.2s ease-in-out;
transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
```

### Terminal Effects
- Glitch animations for hover states
- Pulse effects for loading states
- Typewriter text animations
- ASCII spinner rotations

## Color System

### Semantic Colors
```css
/* Status Colors */
--success-color: #27c93f;  /* Green - success */
--warning-color: #ffbd2e;  /* Yellow - warning */
--error-color: #ff5f56;    /* Red - error */
--info-color: #5eaeff;     /* Blue - info */

/* Terminal Theme */
--text-terminal-green: #27c93f;
--terminal-amber: #ffbd2e;
--terminal-red: #ff5f56;
```

### Color Usage
- Primary actions: Green (#27c93f)
- Hover states: 10% opacity overlays
- Disabled: 50% opacity
- Backgrounds: Dark grays (#0a0a0a, #1a1a1a)

## Naming Conventions

### BEM-inspired Structure
```css
.component {}           /* Block */
.component-element {}   /* Element */
.component--modifier {} /* Modifier */
```

### Examples
```css
.terminal-window {}        /* Block */
.terminal-header {}        /* Element */
.terminal-window--active {} /* Modifier */
```

### Utility Classes
```css
.hidden { display: none; }
.show { display: block; }
.active { /* active state */ }
.disabled { /* disabled state */ }
```

## Performance Considerations

### CSS Optimization
1. **Single main import**: Reduces HTTP requests
2. **CSS variables**: Centralized theming
3. **Minimal specificity**: Avoid deep nesting
4. **Hardware acceleration**: Use transform for animations

### Loading Strategy
```html
<!-- Critical CSS in main.css -->
<link rel="stylesheet" href="css/main.css">
<!-- Page-specific CSS -->
<link rel="stylesheet" href="css/pages/upload.css">
```

## Maintenance Tips

### Adding New Components
1. Create new file in `/css/components/`
2. Follow existing naming patterns
3. Add import to main.css
4. Document any new variables

### Modifying Existing Styles
1. Check if variable exists first
2. Consider impact on other components
3. Test mobile view
4. Update documentation

### Debugging CSS Issues
1. Check import order
2. Verify file paths
3. Clear browser cache
4. Use browser DevTools
5. Check specificity conflicts

## Browser Compatibility

### Required Features
- CSS Custom Properties (CSS Variables)
- CSS Grid Layout
- Flexbox
- CSS Transforms
- CSS Animations
- Media Queries

### Vendor Prefixes
Minimal prefixes needed for modern browsers:
```css
-webkit-transform: /* Safari */
-webkit-animation: /* Safari */
```

## Testing Checklist

### Visual Regression
- [ ] Components render correctly
- [ ] Hover states work
- [ ] Active states visible
- [ ] Disabled states clear
- [ ] Animations smooth

### Responsive Testing
- [ ] Desktop (1920px)
- [ ] Laptop (1366px)
- [ ] Tablet (768px)
- [ ] Mobile (375px)
- [ ] Landscape orientation

### Cross-browser
- [ ] Chrome/Edge (Blink)
- [ ] Firefox (Gecko)
- [ ] Safari (WebKit)

## Common Patterns

### Card Components
```css
.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: 4px;
  padding: var(--spacing-md);
}
```

### Terminal Elements
```css
.terminal-element {
  font-family: var(--font-mono);
  color: var(--text-terminal-green);
  text-shadow: 0 0 5px rgba(39, 201, 63, 0.5);
}
```

### Interactive States
```css
.interactive:hover {
  border-color: var(--primary-color);
  box-shadow: 0 0 10px rgba(39, 201, 63, 0.3);
}
```

## Future Considerations

### Potential Improvements
- CSS-in-JS for dynamic theming
- PostCSS for advanced processing
- CSS Modules for true isolation
- Custom properties for user themes
- Dark/light mode toggle

### Scalability
- Component library approach ready
- Easy to add new themes
- Modular structure supports growth
- Performance optimized for expansion