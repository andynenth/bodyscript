# Configuration Modules

This directory contains configuration and constants used throughout the JavaScript application.

## Files

- **constants.js** - Application-wide constants (API endpoints, limits, etc.)
- **settings.js** - Default settings and configurations
- **api-config.js** - API-related configuration

## Usage

```javascript
import { API_URL, MAX_VIDEO_SIZE } from './config/constants.js';
import { defaultSettings } from './config/settings.js';
```

## Guidelines

- Use UPPER_CASE for constants
- Group related configurations together
- Export as named exports for tree-shaking
- No side effects in configuration files