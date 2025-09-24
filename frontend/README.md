# Frontend Architecture - BodyScript

## Overview
This frontend is built with a modular architecture separating HTML structure, CSS styling, and JavaScript functionality. The refactoring reduced upload.html from 1,741 to 191 lines (89% reduction) and index.html from 820 to 80 lines (90% reduction) while preserving all functionality.

## File Structure

```
frontend/
├── css/
│   ├── base/               # Foundation styles
│   │   ├── reset.css       # CSS reset and base styles
│   │   ├── variables.css   # CSS custom properties (colors, sizes)
│   │   └── typography.css  # Font definitions and text styles
│   ├── components/         # Reusable component styles
│   │   ├── terminal.css    # Terminal window styling
│   │   ├── buttons.css     # All button variants
│   │   ├── progress.css    # Progress bars and status
│   │   ├── forms.css       # File upload and dropzone
│   │   └── modal.css       # Modal and video player
│   ├── pages/              # Page-specific styles
│   │   ├── upload.css      # Upload page specific
│   │   └── gallery.css     # Gallery page specific
│   └── main.css            # Import orchestrator
├── js/
│   ├── config.js           # API configuration
│   ├── api/                # API communication layer
│   │   └── upload.js       # Video upload and status APIs
│   ├── components/         # Component logic
│   │   ├── progress-bar.js      # Progress bar updates
│   │   ├── file-handler.js      # File selection/validation
│   │   ├── video-modal.js       # Video modal player
│   │   └── status-updater.js    # Processing status updates
│   ├── pages/              # Page controllers
│   │   ├── upload-page.js  # Upload page initialization
│   │   └── gallery-page.js # Gallery page initialization
│   └── utils/              # Utility functions
│       ├── dom-helpers.js  # DOM manipulation utilities
│       └── format-helpers.js # File size/duration formatting
├── assets/                 # Shared assets
│   ├── gallery-common.css  # Shared gallery styles
│   └── gallery-common.js   # Shared gallery functionality
├── upload.html             # Upload page (191 lines)
├── index.html              # Gallery page (80 lines)
└── admin.html              # Admin dashboard

```

## Architecture Principles

### CSS Architecture
- **Layered approach**: Base → Components → Pages
- **CSS Custom Properties**: All colors and sizes use variables
- **Component isolation**: Each component is self-contained
- **Import orchestration**: main.css controls import order
- **Mobile-first responsive**: Media queries optimize for mobile

### JavaScript Architecture
- **ES6 Modules**: Clean import/export syntax
- **Separation of concerns**: API, components, utilities separated
- **Event-driven**: Page controllers initialize components
- **Progressive enhancement**: Core functionality works without JS
- **Error handling**: Graceful degradation on failures

## CSS Class Naming Conventions

### Terminal Theme Classes
- `.terminal-*`: Terminal window components
- `.ascii-*`: ASCII art and decorative elements
- `.status-*`: Processing status indicators

### Component Classes
- `.btn-*`: Button variants
- `.modal-*`: Modal dialog components
- `.progress-*`: Progress indicators
- `.drop-*`: Drag-and-drop areas

### Utility Classes
- `.hidden`: Hide elements
- `.show`: Display elements
- `.active`: Active state
- `.disabled`: Disabled state

## JavaScript Module Structure

### API Modules (`/js/api/`)
Export async functions that return promises:
```javascript
export async function uploadVideo(file, onProgress) { }
export async function checkStatus(jobId) { }
```

### Component Modules (`/js/components/`)
Export initialization functions and update methods:
```javascript
export function initFileHandler() { }
export function updateProgress(percent) { }
```

### Page Controllers (`/js/pages/`)
Import dependencies and initialize on DOM ready:
```javascript
import { uploadVideo } from '../api/upload.js';
document.addEventListener('DOMContentLoaded', init);
```

### Utility Modules (`/js/utils/`)
Export pure utility functions:
```javascript
export function formatFileSize(bytes) { }
export function $(selector) { }
```

## Maintenance Guidelines

### Adding New Features
1. Create new component files (don't modify existing unless directly related)
2. Follow established module patterns
3. Add styles to appropriate layer (base/component/page)
4. Initialize in page controller

### Modifying Styles
1. Check variables.css first for existing custom properties
2. Add new variables rather than hard-coding values
3. Keep component styles isolated
4. Test mobile view after changes

### Updating JavaScript
1. Maintain module boundaries
2. Export only necessary functions
3. Handle errors gracefully
4. Test complete user flow

### Performance Optimization
1. CSS is loaded via single main.css import
2. JavaScript modules load on-demand
3. Images lazy-load where appropriate
4. Minimize API calls with caching

## Testing Checklist

### Desktop Testing
- [ ] File upload via drag-and-drop
- [ ] File upload via button click
- [ ] Upload progress display
- [ ] Video playback in modal
- [ ] Download functionality
- [ ] Gallery filtering
- [ ] Responsive at all viewport sizes

### Mobile Testing (< 768px)
- [ ] Touch targets ≥ 44px
- [ ] No horizontal scroll
- [ ] Readable without zoom
- [ ] Buttons stack vertically
- [ ] Progress bar fits screen
- [ ] Video modal responsive

### Cross-Browser
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari
- [ ] Mobile browsers

## Common Issues & Solutions

### Module Loading Errors
- Ensure `type="module"` on script tags
- Check relative import paths
- Verify file extensions in imports

### CSS Not Applied
- Check import order in main.css
- Clear browser cache
- Verify file paths are correct

### Mobile Layout Issues
- Test with device emulation
- Check viewport meta tag
- Review media query breakpoints

## Development Workflow

1. **Local Development**
   ```bash
   # Start local server
   python -m http.server 8001
   # Or use any static server
   ```

2. **Making Changes**
   - Edit appropriate module
   - Test in browser immediately
   - Check mobile view
   - Test complete user flow

3. **Before Deployment**
   - Run through testing checklist
   - Check console for errors
   - Verify API configuration
   - Test on actual mobile device

## API Configuration

The frontend expects an API server at the URL specified in `config.js`:
```javascript
window.API_URL = 'http://localhost:8000';
```

Update this for different environments:
- Development: `http://localhost:8000`
- Staging: `https://staging-api.example.com`
- Production: `https://api.example.com`

## Browser Support

- Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- Mobile browsers (iOS Safari 14+, Chrome Mobile 90+)
- ES6 module support required
- CSS Grid and Flexbox support required

## Contact & Support

For questions about the frontend architecture or to report issues, please refer to the main project documentation or contact the development team.