# Core Modules

This directory contains the core shared modules that provide fundamental functionality across the application.

## Modules

- **VideoPlayer.js** - Core video playback functionality
- **Modal.js** - Base modal implementation
- **VideoModal.js** - Video-specific modal extending Modal
- **FilterManager.js** - Manages filtering logic for galleries
- **GalleryDataStore.js** - Centralized data management for gallery videos
- **GalleryCore.js** - Main orchestrator that combines all core modules

## Usage

All modules export ES6 classes/functions that can be imported:

```javascript
import { VideoPlayer } from './core/VideoPlayer.js';
import { Modal } from './core/Modal.js';
```

## Guidelines

- Each module should be self-contained with no external dependencies except utilities
- Use ES6 module syntax (import/export)
- Include proper cleanup methods (destroy/dispose)
- Document public API with JSDoc comments