# Reusable Components

This directory contains reusable UI components and widgets used across different pages.

## Existing Components

- **file-handler.js** - File upload and validation
- **progress-bar.js** - Progress indicator component
- **status-updater.js** - Status message display
- **video-modal.js** - Video player modal (to be refactored)

## New Components (To Be Created)

- **VideoHoverPreview.js** - Hover-to-preview video functionality
- **VideoCard.js** - Video thumbnail card component
- **FilterBar.js** - Category filter UI component

## Component Structure

Each component should:
1. Be a self-contained ES6 class or function
2. Handle its own DOM creation and events
3. Provide clear public API
4. Include destroy/cleanup method
5. Emit custom events for parent communication

## Usage Example

```javascript
import { ProgressBar } from './components/progress-bar.js';

const progress = new ProgressBar({
  container: document.querySelector('#progress-container'),
  max: 100
});

progress.update(50);
progress.destroy();
```

## Guidelines

- One component per file
- Use ES6 classes for stateful components
- Prefix private methods with underscore
- Document public methods with JSDoc
- Include CSS in component file or separate .css with same name