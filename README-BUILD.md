# BodyScript Frontend Build System

This document describes the modern build system setup for the BodyScript frontend, designed to work with the refactored ES6 modules and modular CSS architecture.

## Overview

The build system uses **Vite** as the main bundler, with PostCSS for CSS processing, ESLint for JavaScript linting, and Prettier for code formatting. It supports:

- ✅ ES6 module bundling with proper tree-shaking
- ✅ CSS processing with autoprefixer and nesting
- ✅ Development server with hot reload and API mocking
- ✅ Production builds with optimization and minification
- ✅ Multi-page application support (gallery + upload)
- ✅ Legacy browser support with polyfills
- ✅ Code quality tools (linting, formatting)

## Quick Start

### 1. Setup

```bash
# Install dependencies and setup environment
npm run setup
# or manually:
npm install
```

### 2. Development

```bash
# Start development server (http://localhost:3000)
npm run dev

# Alternative: Use enhanced dev server with mock API
node dev-server.js
```

### 3. Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
bodyscript/
├── frontend/                   # Source files
│   ├── js/
│   │   ├── entries/           # Build entry points
│   │   │   ├── gallery.js     # Gallery page entry
│   │   │   └── upload.js      # Upload page entry
│   │   ├── main.js            # Global application setup
│   │   ├── core/              # Core modules
│   │   ├── components/        # UI components
│   │   ├── utils/             # Utilities
│   │   └── pages/             # Page controllers
│   ├── css/                   # Modular CSS
│   │   ├── main.css           # CSS orchestrator
│   │   ├── base/              # Base styles
│   │   ├── components/        # Component styles
│   │   └── pages/             # Page-specific styles
│   ├── index.html             # Gallery page
│   └── upload.html            # Upload page
├── dist/                      # Build output
├── package.json               # Dependencies and scripts
├── vite.config.js             # Vite configuration
├── postcss.config.js          # PostCSS configuration
├── .eslintrc.js               # ESLint configuration
├── .stylelintrc.js            # Stylelint configuration
└── .prettierrc.js             # Prettier configuration
```

## Available Scripts

### Development
- `npm run dev` - Start development server
- `npm run preview` - Preview production build

### Building
- `npm run build` - Production build
- `npm run build:prod` - Production build with optimizations
- `npm run clean` - Clean build directory

### Code Quality
- `npm run lint:js` - Lint JavaScript files
- `npm run lint:css` - Lint CSS files
- `npm run format` - Format all files with Prettier

### Analysis
- `npm run analyze` - Analyze bundle sizes

## Build Features

### JavaScript Processing

**Module System**: ES6 modules with proper imports/exports
```javascript
// Import from aliased paths
import { $, $$ } from '@utils/dom-helpers.js';
import Modal from '@core/Modal.js';
```

**Code Splitting**: Automatic chunking for optimal loading
- `app-core` - Shared application code
- `gallery` - Gallery-specific modules
- `upload` - Upload-specific modules
- `ui-components` - Shared UI components
- `utils` - Utility functions

**Browser Support**: Transpilation and polyfills for older browsers

### CSS Processing

**Modern CSS Features**:
- CSS nesting syntax
- Custom properties (CSS variables)
- Autoprefixer for vendor prefixes
- Import statements with dependency resolution

**Optimization**:
- Minification in production
- Dead code elimination
- Asset optimization

### Development Server

**Features**:
- Hot module replacement (HMR)
- Mock API endpoints for development
- CORS support
- Backend proxy with fallback
- Source maps for debugging

**Mock API Endpoints**:
- `GET /api/health` - Health check
- `GET /api/gallery` - Gallery data
- `POST /api/upload` - File upload simulation

### Production Optimization

**JavaScript**:
- Minification with Terser
- Tree shaking for smaller bundles
- Console logging removal
- Modern/legacy bundle generation

**CSS**:
- Minification with cssnano
- Unused CSS removal
- Asset optimization

**Assets**:
- Image optimization
- Font optimization
- File hashing for caching

## Configuration

### Environment Variables

Create `.env.development` and `.env.production` files:

```bash
# Development
NODE_ENV=development
VITE_API_BASE_URL=http://localhost:8000
VITE_DEBUG_MODE=true

# Production
NODE_ENV=production
VITE_API_BASE_URL=/api
VITE_DEBUG_MODE=false
```

### Vite Configuration

Key configuration in `vite.config.js`:
- Multi-page app setup
- Alias configuration for clean imports
- Build optimization settings
- Development server with API proxy

### PostCSS Configuration

PostCSS plugins in `postcss.config.js`:
- `postcss-import` - Import resolution
- `postcss-nesting` - CSS nesting syntax
- `postcss-preset-env` - Modern CSS features
- `autoprefixer` - Vendor prefixes
- `cssnano` - Minification (production)

## Build Output

Production builds create:

```
dist/
├── index.html              # Gallery page
├── upload.html             # Upload page
├── assets/
│   ├── css/
│   │   ├── main-[hash].css
│   │   └── pages-[hash].css
│   ├── js/
│   │   ├── app-core-[hash].js
│   │   ├── gallery-[hash].js
│   │   ├── upload-[hash].js
│   │   └── utils-[hash].js
│   └── images/
│       └── [optimized images]
└── [static assets]
```

## Integration with Backend

The frontend build system is designed to work with the Python backend:

**Development**: Vite dev server proxies API calls to `localhost:8000` with fallback to mock responses

**Production**: Built files are served by the backend from the `dist/` directory

**API Integration**: All API calls use the configured base URL and work in both environments

## Debugging

### Development Debugging

Global debug object available in development:
```javascript
// Available in browser console
window.BodyScriptDebug
```

### Build Analysis

Analyze bundle composition:
```bash
npm run build
npm run analyze
```

### Source Maps

Enabled in development for debugging transpiled code.

## Browser Support

**Target Browsers**:
- Chrome/Edge 88+
- Firefox 85+
- Safari 14+
- iOS Safari 14+
- Android Chrome 88+

**Legacy Support**: Automatic polyfills for older browsers via `@vitejs/plugin-legacy`

## Performance

**Bundle Sizes** (typical):
- App core: ~15KB gzipped
- Gallery page: ~25KB gzipped
- Upload page: ~20KB gzipped
- CSS: ~10KB gzipped

**Loading Strategy**:
- Critical CSS inlined
- Non-critical assets lazy loaded
- Module preloading for faster navigation

## Troubleshooting

### Common Issues

1. **Module not found errors**: Check alias configuration in `vite.config.js`
2. **CSS not applying**: Verify import order in `frontend/css/main.css`
3. **API calls failing**: Check proxy configuration and backend availability
4. **Build failures**: Run `npm run clean` and rebuild

### Reset Development Environment

```bash
npm run clean
rm -rf node_modules package-lock.json
npm install
```

## Migration Notes

This build system is designed to work with the existing refactored code:

- **ES6 Modules**: All JavaScript uses modern module syntax
- **CSS Modules**: Modular CSS with proper importing
- **Legacy Compatibility**: Maintains compatibility with existing HTML structure
- **Progressive Enhancement**: New features don't break existing functionality

The build system can be adopted gradually without requiring immediate changes to all existing code.