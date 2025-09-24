# Migration Guide: Legacy to Modular Architecture

This guide helps developers understand the changes made during the refactoring from legacy code to the new modular architecture, and how to adapt existing code to use the new patterns.

## Overview of Changes

The refactoring transformed BodyScript from a monolithic structure to a modern, modular architecture with clear separation of concerns.

### Key Improvements

1. **Eliminated Code Duplication**: Consolidated duplicate processing logic
2. **Modular JavaScript**: Replaced monolithic scripts with modular components
3. **Abstract Base Classes**: Common interfaces for Python components
4. **Template Method Pattern**: Standardized processing workflows
5. **Better Testing**: Comprehensive test coverage across languages
6. **Improved Documentation**: JSDoc and Python docstrings throughout

## Migration Mapping

### Frontend Changes

#### From: Monolithic Scripts
```javascript
// OLD: Large monolithic gallery-common.js
function loadGallery() {
  // 500+ lines of mixed concerns
  // Data loading, filtering, rendering, events all mixed
}
```

#### To: Modular Architecture
```javascript
// NEW: Modular components with single responsibilities
import { GalleryCore } from './core/GalleryCore.js';
import { GalleryDataStore } from './core/GalleryDataStore.js';
import { FilterManager } from './core/FilterManager.js';

const gallery = new GalleryCore({
  containerSelector: '#videoGrid',
  enableHoverPreview: true,
  enableLazyLoading: true
});

await gallery.initialize();
```

#### Migration Steps for Frontend Code

1. **Replace Direct DOM Manipulation**
   ```javascript
   // OLD
   document.querySelector('.video-grid').innerHTML = generateHTML(videos);

   // NEW
   gallery.render(videos);
   ```

2. **Replace Event Handlers**
   ```javascript
   // OLD
   document.addEventListener('click', handleAllClicks);

   // NEW
   gallery.on('videoSelected', handleVideoSelection);
   ```

3. **Replace Data Loading**
   ```javascript
   // OLD
   fetch('/api/gallery').then(response => {
     // Handle response directly
   });

   // NEW
   const dataStore = new GalleryDataStore();
   const videos = await dataStore.loadFromAPI();
   ```

### Backend Changes

#### From: Tightly Coupled Processing
```python
# OLD: Monolithic processing functions
def process_video_old(video_path):
    # All processing steps mixed together
    # No separation of concerns
    # Duplicate code across different processors
```

#### To: Abstract Base Classes
```python
# NEW: Clean inheritance hierarchy
from cli.src.core.base_processor import BaseVideoProcessor

class MyVideoProcessor(BaseVideoProcessor):
    def _initialize_detector(self):
        # Specific detector initialization

    def _detect_frame(self, frame, frame_idx):
        # Specific frame processing

    # Common methods inherited:
    # - process_video()
    # - export_csv()
    # - export_json()
    # - get_dataframe()
```

#### Migration Steps for Python Code

1. **Replace Custom Processing Classes**
   ```python
   # OLD
   class CustomProcessor:
       def __init__(self):
           # Custom initialization

       def process(self, video):
           # Custom processing logic

   # NEW
   class CustomProcessor(BaseVideoProcessor):
       def _initialize_detector(self):
           # Specific detector setup

       def _detect_frame(self, frame, frame_idx):
           # Frame processing logic
   ```

2. **Use Template Method Pattern**
   ```python
   # OLD
   processor = CustomProcessor()
   processor.load_video(path)
   processor.extract_frames()
   processor.detect_poses()
   processor.export_results()

   # NEW
   processor = CustomProcessor()
   result = processor.process_video(path)  # Template method handles workflow
   ```

3. **Standardized Result Formats**
   ```python
   # OLD
   def process_frame(frame):
       return {"landmarks": [...], "detected": True}  # Custom format

   # NEW
   def _detect_frame(self, frame, frame_idx):
       result = ProcessingResult(frame_idx, timestamp)
       result.detected = True
       result.landmarks = landmarks
       return result  # Standardized format
   ```

## Component Migration Examples

### Gallery Component Migration

#### Before: Legacy Implementation
```javascript
// gallery-common.js (500+ lines)
var galleryData = [];
var currentFilter = 'all';

function loadGallery() {
    fetch('/api/gallery')
        .then(response => response.json())
        .then(data => {
            galleryData = data.videos;
            renderGallery(galleryData);
            setupFilters();
            setupEventHandlers();
        });
}

function renderGallery(videos) {
    var html = '';
    videos.forEach(video => {
        html += generateVideoCard(video);
    });
    document.getElementById('videoGrid').innerHTML = html;
}

function setupFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', filterVideos);
    });
}

// ... 400+ more lines
```

#### After: Modular Implementation
```javascript
// gallery.js (entry point)
import { GalleryCore } from '../core/GalleryCore.js';

const gallery = new GalleryCore({
    containerSelector: '#videoGrid',
    filterSelector: '.filter-btn',
    enableHoverPreview: true,
    enableLazyLoading: true,
    enableTouchSupport: true
});

await gallery.initialize();

// GalleryCore.js (orchestrator)
export class GalleryCore {
    constructor(options = {}) {
        this.dataStore = new GalleryDataStore();
        this.filterManager = new FilterManager({
            renderCallback: (videos) => this.render(videos)
        });
        this.videoModal = new VideoModal();
    }

    async initialize() {
        const videos = await this.dataStore.loadFromAPI();
        this.filterManager.setItems(videos);
        this.render(videos);
    }
}

// GalleryDataStore.js (data management)
export class GalleryDataStore {
    async loadFromAPI() {
        // API loading logic
    }

    getVideoById(id) {
        // Data access logic
    }
}

// FilterManager.js (filtering logic)
export class FilterManager {
    filterBy(category) {
        // Filtering logic
    }
}
```

### Video Processing Migration

#### Before: Duplicate Processing Logic
```python
# Multiple similar classes with duplicate code
class SimplePoseAnalyzer:
    def __init__(self):
        # Custom initialization

    def process_video(self, video_path):
        # Load video metadata - DUPLICATE
        # Extract frames - DUPLICATE
        # Initialize MediaPipe - DUPLICATE
        # Process frames - DUPLICATE
        # Calculate statistics - DUPLICATE
        # Export data - DUPLICATE

class AdvancedPoseAnalyzer:
    def __init__(self):
        # Different initialization

    def process_video(self, video_path):
        # Load video metadata - DUPLICATE
        # Extract frames - DUPLICATE
        # Initialize MediaPipe - DUPLICATE
        # Process frames - DIFFERENT
        # Calculate statistics - DUPLICATE
        # Export data - DUPLICATE
```

#### After: Base Class Hierarchy
```python
# base_processor.py (common functionality)
class BaseVideoProcessor(ABC):
    def process_video(self, video_path):
        """Template method - eliminates duplication"""
        # Step 1: Load metadata (common)
        self.video_metadata = self._load_video_metadata(video_path)

        # Step 2: Initialize detector (abstract)
        detector = self._initialize_detector()

        # Step 3: Extract frames (common)
        frames = self._extract_frames(video_path)

        # Step 4: Process frames (abstract)
        for frame_idx, frame in enumerate(frames):
            result = self._detect_frame(frame, frame_idx)
            self.results_data.append(result)

        # Step 5: Calculate statistics (common)
        self.statistics = self._calculate_statistics(self.results_data)

        return self._format_results()

    @abstractmethod
    def _initialize_detector(self):
        """Subclasses implement specific detector"""
        pass

    @abstractmethod
    def _detect_frame(self, frame, frame_idx):
        """Subclasses implement specific detection"""
        pass

# Specific implementations (no duplication)
class SimplePoseAnalyzer(BaseVideoProcessor):
    def _initialize_detector(self):
        # Simple detector setup

    def _detect_frame(self, frame, frame_idx):
        # Simple detection logic

class AdvancedPoseAnalyzer(BaseVideoProcessor):
    def _initialize_detector(self):
        # Advanced detector setup

    def _detect_frame(self, frame, frame_idx):
        # Advanced detection logic
```

## API Changes

### Frontend API Changes

#### Data Access
```javascript
// OLD
const videos = window.galleryData || [];

// NEW
const dataStore = new GalleryDataStore();
const videos = await dataStore.loadFromAPI();
```

#### Filtering
```javascript
// OLD
function filterVideos(category) {
    const filtered = videos.filter(v => v.category === category);
    renderGallery(filtered);
}

// NEW
gallery.filter(category);  // or
filterManager.filterBy(category);
```

#### Event Handling
```javascript
// OLD
document.addEventListener('click', function(e) {
    if (e.target.matches('.video-card')) {
        // Handle video click
    }
});

// NEW
gallery.on('videoSelected', function(video) {
    // Handle video selection
});
```

### Python API Changes

#### Processing Interface
```python
# OLD
processor = SimplePoseAnalyzer()
processor.detection_confidence = 0.7
processor.tracking_confidence = 0.5
results = processor.process_video("video.mp4")
processor.export_csv("results.csv")

# NEW
processor = SimplePoseAnalyzer(
    detection_confidence=0.7,
    tracking_confidence=0.5
)
results = processor.process_video("video.mp4")
csv_path = processor.export_csv()  # Auto-generated filename
json_path = processor.export_json()  # New comprehensive export
```

#### Configuration
```python
# OLD
from config import Config
config = Config()
config.detection_confidence = 0.7

# NEW
from cli.src.core.base_detector import PoseConfig
config = PoseConfig(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5,
    model_complexity=1
)
processor = MyProcessor(config)
```

## Testing Migration

### From Manual Testing to Automated

#### Before
```python
# Manual testing scripts
if __name__ == "__main__":
    processor = SimplePoseAnalyzer()
    result = processor.process_video("test.mp4")
    print("Success:", result)
```

#### After
```python
# tests/python/unit/test_base_processor.py
import pytest
from cli.src.core.base_processor import BaseVideoProcessor

class TestVideoProcessor(BaseVideoProcessor):
    def _initialize_detector(self):
        return MockDetector()

    def _detect_frame(self, frame, frame_idx):
        return MockResult()

def test_process_video():
    processor = TestVideoProcessor()
    result = processor.process_video("test.mp4")
    assert result['success'] == True
    assert result['total_frames'] > 0
```

### JavaScript Testing
```javascript
// tests/javascript/unit/test-gallery-core.js
import { GalleryCore } from '../../frontend/js/core/GalleryCore.js';
import { describe, it, expect, beforeEach } from 'vitest';

describe('GalleryCore', () => {
    let gallery;

    beforeEach(() => {
        gallery = new GalleryCore({
            containerSelector: '#test-container'
        });
    });

    it('should initialize successfully', async () => {
        await gallery.initialize();
        expect(gallery.initialized).toBe(true);
    });
});
```

## Breaking Changes

### JavaScript Breaking Changes

1. **Global Variables Removed**
   ```javascript
   // OLD
   window.galleryData  // No longer available

   // NEW
   const dataStore = new GalleryDataStore();
   const videos = dataStore.getVideos();
   ```

2. **Function Signatures Changed**
   ```javascript
   // OLD
   loadGallery(containerId, options)

   // NEW
   const gallery = new GalleryCore(options);
   await gallery.initialize();
   ```

3. **Event Names Changed**
   ```javascript
   // OLD
   document.dispatchEvent(new CustomEvent('galleryLoaded'))

   // NEW
   gallery.on('loadingCompleted', handler)
   ```

### Python Breaking Changes

1. **Import Paths Changed**
   ```python
   # OLD
   from pose_analyzer import SimplePoseAnalyzer

   # NEW
   from cli.src.processors.simple_pose_analyzer import SimplePoseAnalyzer
   ```

2. **Configuration Objects**
   ```python
   # OLD
   processor = SimplePoseAnalyzer()
   processor.detection_confidence = 0.7

   # NEW
   config = PoseConfig(min_detection_confidence=0.7)
   processor = SimplePoseAnalyzer(config)
   ```

## Performance Improvements

### Frontend Performance
- **Lazy Loading**: Images loaded only when visible
- **Virtual Scrolling**: Large lists handled efficiently
- **Caching**: API responses cached for 5 minutes
- **Event Delegation**: Single event listener vs multiple

### Backend Performance
- **Template Method**: Eliminates duplicate processing overhead
- **Streaming**: Large file uploads processed in chunks
- **Background Tasks**: Long processing doesn't block UI
- **Memory Management**: Better resource cleanup

## Backward Compatibility

### Compatibility Layer

The migration includes compatibility layers for gradual adoption:

```javascript
// frontend/js/adapters/gallery-common-adapter.js
// Provides backward compatibility for legacy code

// OLD API still works
function loadGallery() {
    // Delegates to new modular implementation
    const gallery = new GalleryCore();
    return gallery.initialize();
}
```

### Feature Flags

```javascript
// Enable new features gradually
const gallery = new GalleryCore({
    enableHoverPreview: true,   // New feature
    enableLazyLoading: true,    // New feature
    enableTouchSupport: false   // Disable if issues
});
```

## Migration Checklist

### For Existing Projects

- [ ] Update import statements
- [ ] Replace direct DOM manipulation with module APIs
- [ ] Update event handling patterns
- [ ] Migrate to new configuration system
- [ ] Add comprehensive tests
- [ ] Update build scripts
- [ ] Verify backward compatibility
- [ ] Update documentation

### For New Development

- [ ] Use modular JavaScript architecture
- [ ] Extend base classes for Python components
- [ ] Follow established patterns
- [ ] Include comprehensive tests from start
- [ ] Use TypeScript-style JSDoc comments
- [ ] Follow naming conventions
- [ ] Document all public APIs

## Getting Help

### Resources
- **Architecture Documentation**: `/docs/ARCHITECTURE.md`
- **API Documentation**: JSDoc comments in source files
- **Test Examples**: `/tests/` directory
- **Example Implementations**: `/cli/examples/` directory

### Common Issues

1. **Module Not Found**: Check import paths match new structure
2. **Configuration Errors**: Use new configuration objects
3. **Event Handler Issues**: Use new event system
4. **Performance Issues**: Enable lazy loading and caching

This migration guide should help you transition from the legacy codebase to the new modular architecture. The new system provides better maintainability, testability, and performance while supporting future enhancements.