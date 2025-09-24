# API Reference

This document provides comprehensive API documentation for BodyScript's modular architecture.

## JavaScript API

### Core Modules

#### GalleryCore

Main orchestrator for gallery functionality. Combines all core modules to provide a clean API.

```javascript
import { GalleryCore } from './core/GalleryCore.js';

const gallery = new GalleryCore(options);
```

**Constructor Options**
```javascript
{
  containerSelector: '#videoGrid',     // Container element selector
  cardSelector: '.video-card',         // Video card selector
  filterSelector: '.filter-btn',       // Filter button selector
  enableHoverPreview: true,            // Enable video hover previews
  enableLazyLoading: true,             // Enable lazy image loading
  enableTouchSupport: true,            // Enable touch gestures
  renderCallback: null                 // Custom render callback
}
```

**Public Methods**

- `async initialize()` - Initialize gallery and load data
- `render(videos)` - Render videos to gallery
- `filter(filter)` - Filter videos by category
- `search(query)` - Search videos by query
- `sort(field, order)` - Sort videos by field
- `async reload()` - Reload gallery data
- `getVideos()` - Get current filtered videos
- `getAllVideos()` - Get all videos
- `openVideo(videoId)` - Open video in modal
- `closeVideo()` - Close video modal
- `destroy()` - Clean up and destroy gallery
- `enableHoverPreview(enabled)` - Toggle hover preview
- `enableLazyLoading(enabled)` - Toggle lazy loading
- `enableTouchSupport(enabled)` - Toggle touch support

**Events**
- `'loadingStarted'` - Data loading started
- `'loadingCompleted'` - Data loading completed
- `'filterChanged'` - Filter changed

#### GalleryDataStore

Centralized data management for gallery videos. Handles data loading, caching, and CRUD operations.

```javascript
import { GalleryDataStore } from './core/GalleryDataStore.js';

const dataStore = new GalleryDataStore(options);
```

**Constructor Options**
```javascript
{
  apiUrl: window.API_URL || 'http://localhost:8000',
  cacheTimeout: 5 * 60 * 1000,         // 5 minutes
  useSampleData: true                   // Fallback to sample data
}
```

**Public Methods**

- `async loadFromAPI()` - Load videos from API or cache
- `getVideos()` - Get all videos (cloned array)
- `getVideoById(id)` - Get single video by ID
- `getVideosByCategory(category)` - Get videos by category
- `addVideo(video)` - Add video to store
- `updateVideo(id, updates)` - Update video in store
- `removeVideo(id)` - Remove video from store
- `clear()` - Clear all videos
- `getSampleData()` - Get sample data for development

**Event Methods**
- `on(event, handler)` - Add event listener
- `off(event, handler)` - Remove event listener

**Events**
- `'loadingStarted'` - API loading started
- `'loadingCompleted'` - API loading completed
- `'loadingError'` - API loading failed
- `'videoAdded'` - Video added to store
- `'videoUpdated'` - Video updated in store
- `'videoRemoved'` - Video removed from store
- `'cleared'` - All videos cleared

#### FilterManager

Manages filtering logic for galleries. Handles category filtering, search, sorting, and state management.

```javascript
import { FilterManager } from './core/FilterManager.js';

const filterManager = new FilterManager(options);
```

**Constructor Options**
```javascript
{
  defaultFilter: 'all',               // Default filter
  renderCallback: null                // Callback for filter changes
}
```

**Public Methods**

- `setItems(items)` - Initialize with items to filter
- `getAllItems()` - Get all items
- `getFilteredItems()` - Get filtered items
- `filterBy(filter)` - Filter items by category
- `filterByCategory(category)` - Filter by specific category
- `clearFilter()` - Clear all filters
- `search(query)` - Search items by query
- `sortItems(sortBy, order)` - Sort items
- `getActiveFilter()` - Get current active filter
- `getActiveCategory()` - Get current active category
- `registerFilterButtons(buttons)` - Register filter button elements
- `getCategories()` - Get available categories
- `getCategoryCounts()` - Get item count by category
- `destroy()` - Clean up and destroy manager

**Event Methods**
- `on(event, handler)` - Add event listener
- `off(event, handler)` - Remove event listener

**Events**
- `'itemsChanged'` - Items collection changed
- `'filterChanged'` - Filter changed
- `'categoryFilterChanged'` - Category filter changed
- `'filterCleared'` - Filter cleared
- `'searchChanged'` - Search changed
- `'sortChanged'` - Sort changed

### Utility Modules

#### LazyLoader

Handles lazy loading of images using Intersection Observer API.

```javascript
import { LazyLoader } from './utils/LazyLoader.js';

const loader = new LazyLoader(options);
```

**Static Methods**
- `LazyLoader.isSupported()` - Check if Intersection Observer is supported

**Public Methods**
- `observe(elements)` - Observe elements for lazy loading
- `unobserve(element)` - Stop observing element
- `disconnect()` - Disconnect observer
- `destroy()` - Clean up and destroy

#### TouchHandler

Handles touch gestures and events for mobile support.

```javascript
import { TouchHandler } from './utils/TouchHandler.js';

const touchHandler = new TouchHandler();
```

**Static Methods**
- `TouchHandler.isSupported()` - Check if touch is supported

**Public Methods**
- `addTouchSupport(element, options)` - Add touch support to element
- `removeTouchSupport(element)` - Remove touch support
- `destroy()` - Clean up all touch handlers

**Touch Options**
```javascript
{
  onTap: (event, data) => {},         // Tap callback
  onLongPress: (event, data) => {},   // Long press callback
  tapDelay: 100,                      // Tap detection delay
  longPressDelay: 500                 // Long press delay
}
```

## Python API

### Core Classes

#### BasePoseDetector

Abstract base class for all pose detection implementations.

```python
from cli.src.core.base_detector import BasePoseDetector, PoseConfig

class MyDetector(BasePoseDetector):
    def detect_pose(self, frame):
        # Implementation
        pass
```

**Configuration**
```python
config = PoseConfig(
    model_complexity=1,                  # Model complexity (0-2)
    min_detection_confidence=0.5,        # Detection confidence (0-1)
    min_tracking_confidence=0.5,         # Tracking confidence (0-1)
    enable_segmentation=False,           # Enable segmentation mask
    smooth_landmarks=True,               # Smooth landmark coordinates
    static_image_mode=False              # Static image processing
)
```

**Abstract Methods**
- `detect_pose(frame: np.ndarray) -> PoseResult` - Detect pose in frame
- `initialize() -> None` - Initialize detector
- `release() -> None` - Release resources

**Public Methods**
- `get_confidence() -> Tuple[float, float]` - Get confidence thresholds
- `set_confidence(detection, tracking)` - Set confidence thresholds
- `process_batch(frames, progress_callback)` - Process multiple frames
- `calculate_pose_quality(result) -> Dict` - Calculate quality metrics
- `filter_landmarks(landmarks, min_visibility)` - Filter by visibility
- `get_landmark_by_name(result, name)` - Get specific landmark
- `calculate_joint_angle(point1, point2, point3)` - Calculate joint angles
- `normalize_landmarks(landmarks, width, height)` - Normalize coordinates
- `denormalize_landmarks(landmarks, width, height)` - Convert to pixels

**Properties**
- `is_initialized: bool` - Check if initialized

**Context Manager Support**
```python
with MyDetector(config) as detector:
    result = detector.detect_pose(frame)
```

#### BaseVideoProcessor

Abstract base class for video processing implementations using template method pattern.

```python
from cli.src.core.base_processor import BaseVideoProcessor

class MyProcessor(BaseVideoProcessor):
    def _initialize_detector(self):
        # Implementation
        pass

    def _detect_frame(self, frame, frame_idx):
        # Implementation
        pass
```

**Constructor Parameters**
```python
processor = MyProcessor(
    output_dir="output",                 # Output directory
    detection_confidence=0.5,            # Detection confidence
    tracking_confidence=0.5              # Tracking confidence
)
```

**Abstract Methods**
- `_initialize_detector() -> Any` - Initialize specific detector
- `_detect_frame(frame, frame_idx) -> ProcessingResult` - Process single frame

**Optional Methods**
- `_preprocess_frame(frame) -> np.ndarray` - Preprocess frame

**Public Methods (Template)**
- `process_video(video_path, show_progress, max_frames) -> Dict` - Main processing method
- `export_csv(output_path) -> str` - Export results to CSV
- `export_json(output_path) -> str` - Export comprehensive results to JSON
- `get_dataframe() -> pd.DataFrame` - Get results as pandas DataFrame
- `get_statistics() -> Dict` - Get processing statistics
- `cleanup()` - Cleanup resources

**Context Manager Support**
```python
with MyProcessor() as processor:
    result = processor.process_video("video.mp4")
```

#### BaseMediaPipeProcessor

Specialized base class for MediaPipe-based processors.

```python
from cli.src.core.base_processor import BaseMediaPipeProcessor

class MyMediaPipeProcessor(BaseMediaPipeProcessor):
    pass  # MediaPipe initialization handled automatically
```

**Constructor Parameters**
```python
processor = MyMediaPipeProcessor(
    output_dir="output",
    detection_confidence=0.5,
    tracking_confidence=0.5,
    model_complexity=1,                  # MediaPipe model complexity
    enable_segmentation=False            # Enable segmentation
)
```

### Data Classes

#### Landmark
```python
@dataclass
class Landmark:
    x: float                    # Normalized x coordinate (0-1)
    y: float                    # Normalized y coordinate (0-1)
    z: float                    # Normalized z coordinate
    visibility: float           # Visibility/confidence score (0-1)
    name: Optional[str] = None  # Landmark name
    id: Optional[int] = None    # Landmark ID
```

#### PoseResult
```python
@dataclass
class PoseResult:
    landmarks: List[Landmark]                    # Detected landmarks
    detected: bool                              # Detection success
    frame_idx: int                              # Frame index
    timestamp: Optional[float] = None           # Frame timestamp
    world_landmarks: Optional[List[Landmark]]   # 3D world coordinates
    segmentation_mask: Optional[np.ndarray]     # Segmentation mask

    @property
    def num_landmarks(self) -> int              # Number of landmarks

    @property
    def detection_confidence(self) -> float     # Average confidence
```

#### ProcessingResult
```python
class ProcessingResult:
    def __init__(self, frame_idx: int, timestamp: float):
        self.frame_idx = frame_idx
        self.timestamp = timestamp
        self.detected = False
        self.landmarks = None
        self.confidence = 0.0
        self.metadata = {}

    def to_dict(self) -> Dict                   # Convert to dictionary
```

#### VideoMetadata
```python
class VideoMetadata:
    def __init__(self, video_path: str = ""):
        self.video_path = video_path
        self.filename = ""
        self.width = 0
        self.height = 0
        self.fps = 0.0
        self.total_frames = 0
        self.duration = 0.0
        self.format = ""
        self.size_mb = 0.0
        self.created_at = datetime.now()

    def to_dict(self) -> Dict                   # Convert to dictionary
```

#### ProcessingStatistics
```python
class ProcessingStatistics:
    def __init__(self):
        self.total_frames = 0
        self.detected_frames = 0
        self.detection_rate = 0.0
        self.average_confidence = 0.0
        self.processing_fps = 0.0
        self.processing_time = 0.0
        self.data_points = 0
        self.quality_metrics = {}
        self.errors = []

    def calculate_derived_metrics(self)         # Calculate derived metrics
    def to_dict(self) -> Dict                   # Convert to dictionary
```

## REST API (Backend)

### Endpoints

#### Gallery Endpoints
```
GET /api/gallery                        # Get all videos
POST /api/upload                         # Upload video
GET /api/video/{video_id}               # Get specific video
DELETE /api/video/{video_id}            # Delete video
GET /api/video/{video_id}/preview       # Get video preview
GET /api/video/{video_id}/thumbnail     # Get video thumbnail
```

#### Processing Endpoints
```
POST /api/process                        # Start video processing
GET /api/process/{job_id}/status        # Get processing status
GET /api/process/{job_id}/result        # Get processing result
DELETE /api/process/{job_id}            # Cancel processing job
```

#### Admin Endpoints
```
GET /admin/gallery                       # Admin gallery view
POST /admin/video/{video_id}/promote    # Promote to gallery
DELETE /admin/video/{video_id}          # Admin delete video
GET /admin/stats                         # System statistics
```

### Response Formats

#### Gallery Response
```json
{
  "videos": [
    {
      "id": 1,
      "title": "Contemporary Dance",
      "category": "dance",
      "thumbnail": "https://example.com/thumb.jpg",
      "preview": "https://example.com/preview.mp4",
      "full": "https://example.com/full.mp4",
      "accuracy": 98.2,
      "views": "2.3M",
      "likes": "12.3k",
      "comments": 234,
      "duration": "0:45",
      "username": "@dance_pro",
      "tags": ["#bodyscript", "#posedetection", "#dance"]
    }
  ],
  "total": 10,
  "categories": ["dance", "sports", "yoga", "martial"]
}
```

#### Processing Status Response
```json
{
  "job_id": "uuid-string",
  "status": "processing",  // pending, processing, completed, failed
  "progress": 45.5,        // Percentage complete
  "message": "Processing frame 456 of 1000",
  "started_at": "2024-01-01T12:00:00Z",
  "estimated_completion": "2024-01-01T12:05:00Z"
}
```

#### Processing Result Response
```json
{
  "success": true,
  "job_id": "uuid-string",
  "video_metadata": {
    "filename": "video.mp4",
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
    "duration": 60.0,
    "total_frames": 1800
  },
  "statistics": {
    "total_frames": 1800,
    "detected_frames": 1750,
    "detection_rate": 0.972,
    "average_confidence": 0.89,
    "processing_fps": 15.5,
    "data_points": 57750
  },
  "exports": {
    "csv_path": "/path/to/results.csv",
    "json_path": "/path/to/results.json",
    "video_path": "/path/to/overlay.mp4"
  }
}
```

## Usage Examples

### JavaScript Usage

```javascript
// Initialize gallery with all features
const gallery = new GalleryCore({
    containerSelector: '#videoGrid',
    enableHoverPreview: true,
    enableLazyLoading: true,
    enableTouchSupport: true
});

// Initialize and set up event handlers
await gallery.initialize();

gallery.on('loadingCompleted', (videos) => {
    console.log(`Loaded ${videos.length} videos`);
});

// Filter and search
gallery.filter('dance');
gallery.search('yoga');
gallery.sort('accuracy', 'desc');

// Manual data management
const dataStore = new GalleryDataStore();
const videos = await dataStore.loadFromAPI();
dataStore.addVideo(newVideo);
dataStore.updateVideo(1, { title: 'New Title' });
```

### Python Usage

```python
# Custom processor implementation
class MyProcessor(BaseVideoProcessor):
    def _initialize_detector(self):
        return MyDetector(self.config)

    def _detect_frame(self, frame, frame_idx):
        result = ProcessingResult(frame_idx, 0.0)
        # Process frame
        return result

# Usage
processor = MyProcessor(
    detection_confidence=0.7,
    tracking_confidence=0.6,
    output_dir="my_results"
)

# Process video
result = processor.process_video("video.mp4")

# Export results
csv_path = processor.export_csv()
json_path = processor.export_json()
df = processor.get_dataframe()

# Statistics
stats = processor.get_statistics()
print(f"Detection rate: {stats['detection_rate']:.1%}")
```

### Configuration Examples

```python
# Pose detection configuration
config = PoseConfig(
    model_complexity=2,                 # Higher accuracy
    min_detection_confidence=0.8,       # Higher threshold
    min_tracking_confidence=0.7,
    enable_segmentation=True,           # Enable body segmentation
    smooth_landmarks=True
)

detector = MyDetector(config)
```

```javascript
// Frontend configuration
const gallery = new GalleryCore({
    containerSelector: '#videoGrid',
    cardSelector: '.video-card',
    filterSelector: '.filter-btn',
    enableHoverPreview: true,
    enableLazyLoading: true,
    enableTouchSupport: window.innerWidth <= 768,  // Mobile only
    renderCallback: (videos) => {
        updateStatistics(videos);
    }
});
```

This API reference provides comprehensive documentation for all public interfaces in the BodyScript modular architecture. Each component is designed to be used independently or as part of the larger system.