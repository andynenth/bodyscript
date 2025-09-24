# BodyScript Architecture Documentation

## Overview

BodyScript is a modern, modular pose estimation system designed for extracting human skeletal data from video content. The architecture follows a layered approach with clear separation of concerns, progressive enhancement capabilities, and comprehensive web integration.

## System Architecture

```
BodyScript Architecture (Layered)
│
├── Frontend (Web UI)
│   ├── Core Modules (Modular JS Architecture)
│   ├── UI Components (Gallery, Upload, Video Player)
│   └── Entry Points (Page-specific implementations)
│
├── Backend (FastAPI Web Service)
│   ├── REST API Endpoints
│   ├── Background Processing
│   └── File Management (Local/R2)
│
├── CLI (Command Line Interface)
│   ├── Core Processing Engine
│   ├── Video Processing Pipeline
│   └── Data Export & Visualization
│
└── Shared Infrastructure
    ├── Configuration Management
    ├── Testing Framework
    └── Build System
```

## Core Design Principles

### 1. Progressive Development
- **MVP First**: Start with basic pose detection (33 landmarks)
- **Research Extension**: Add holistic detection (543 landmarks)
- **Creative Platform**: Future AI-powered features

### 2. Modular Architecture
- **Separation of Concerns**: Each module has a single responsibility
- **Loose Coupling**: Modules communicate through well-defined interfaces
- **High Cohesion**: Related functionality is grouped together

### 3. Interface-Driven Design
- **Abstract Base Classes**: Common interfaces for all implementations
- **Dependency Injection**: Easy testing and implementation swapping
- **Template Method Pattern**: Common workflows with customizable steps

## Module Breakdown

### Frontend Architecture

The frontend follows a modular JavaScript architecture without frameworks:

```
frontend/
├── js/
│   ├── core/                    # Core business logic modules
│   │   ├── GalleryCore.js       # Main gallery orchestrator
│   │   ├── GalleryDataStore.js  # Data management & caching
│   │   ├── FilterManager.js     # Filtering & search logic
│   │   ├── VideoModal.js        # Video playback modal
│   │   └── VideoPlayer.js       # Video player component
│   │
│   ├── components/              # Reusable UI components
│   │   ├── VideoHoverPreview.js # Video preview on hover
│   │   └── status-updater.js    # Upload status updates
│   │
│   ├── utils/                   # Utility functions
│   │   ├── LazyLoader.js        # Image lazy loading
│   │   ├── TouchHandler.js      # Touch gesture support
│   │   ├── dom-helpers.js       # DOM manipulation utilities
│   │   ├── event-helpers.js     # Event handling utilities
│   │   └── format-helpers.js    # Data formatting utilities
│   │
│   ├── adapters/               # Legacy compatibility
│   │   └── gallery-common-adapter.js
│   │
│   └── entries/                # Page-specific entry points
│       ├── gallery.js          # Gallery page implementation
│       └── upload.js           # Upload page implementation
│
├── css/                        # Modular stylesheets
│   ├── core/                   # Core styling system
│   ├── components/             # Component-specific styles
│   └── pages/                  # Page-specific styles
│
└── assets/                     # Static assets
    ├── gallery-common.css      # Shared gallery styles
    └── gallery-common.js       # Legacy compatibility layer
```

#### Key Frontend Patterns

1. **Module Pattern**: Each core module exports a class with clear public API
2. **Observer Pattern**: Events for communication between modules
3. **Strategy Pattern**: Pluggable components (LazyLoader, TouchHandler)
4. **Facade Pattern**: GalleryCore provides simple API over complex subsystems

### Backend Architecture

FastAPI-based web service with clean separation:

```
backend/
├── app.py                      # Main FastAPI application
├── process_wrapper.py          # Video processing orchestrator
├── admin_routes.py            # Gallery management endpoints
├── storage_r2.py              # Cloud storage integration
├── video_utils.py             # Video processing utilities
└── test_local_processing.py   # Local testing utilities
```

#### Backend Components

1. **API Layer**: FastAPI routes handling HTTP requests
2. **Processing Layer**: Video analysis orchestration
3. **Storage Layer**: File management (local/cloud)
4. **Admin Layer**: Content curation and management

### CLI Architecture

Command-line interface with modular processing pipeline:

```
cli/
├── src/
│   ├── core/                   # Core processing engine
│   │   ├── base_detector.py    # Abstract pose detection interface
│   │   ├── base_processor.py   # Abstract video processing interface
│   │   └── consolidation_guide.py # Processing consolidation logic
│   │
│   ├── video/                  # Video processing modules
│   │   ├── frame_extractor.py  # Frame extraction utilities
│   │   └── skeleton_overlay.py # Visualization overlay
│   │
│   └── config/                 # Configuration management
│       └── settings.py         # Application settings
│
├── utils/                      # Utility modules
│   └── visualization.py        # Data visualization tools
│
├── examples/                   # Example implementations
│   ├── process_video_simple.py
│   ├── batch_process_videos.py
│   ├── webcam_pose_test.py
│   └── test_installation.py
│
└── scripts/                    # Utility scripts
    └── utilities/
        └── start_web_server.py
```

#### CLI Design Patterns

1. **Template Method**: `BaseVideoProcessor` defines common workflow
2. **Abstract Factory**: Different detector implementations
3. **Command Pattern**: Example scripts as executable commands
4. **Builder Pattern**: Configuration object construction

## Data Flow Architecture

### Video Processing Pipeline

```
Input Video
    │
    ├── Metadata Extraction
    │   └── Resolution, FPS, Duration
    │
    ├── Frame Extraction
    │   └── Batch processing with progress tracking
    │
    ├── Pose Detection
    │   ├── MediaPipe Processing
    │   ├── Landmark Extraction (33 or 543 points)
    │   └── Confidence Scoring
    │
    ├── Data Processing
    │   ├── Normalization
    │   ├── Quality Assessment
    │   └── Statistical Analysis
    │
    └── Export & Visualization
        ├── CSV Export (frame-by-frame data)
        ├── JSON Export (comprehensive results)
        ├── Video Overlay (skeleton visualization)
        └── Statistics Report
```

### Web Application Data Flow

```
User Upload
    │
    ├── File Upload (Frontend)
    │   └── Progress tracking, validation
    │
    ├── Background Processing (Backend)
    │   ├── Video analysis
    │   ├── Thumbnail generation
    │   └── Storage management
    │
    ├── Gallery Integration
    │   ├── Metadata storage
    │   ├── Preview generation
    │   └── Category assignment
    │
    └── User Access
        ├── Gallery browsing
        ├── Video playback
        └── Data download
```

## Interface Specifications

### Core Python Interfaces

#### BasePoseDetector
```python
class BasePoseDetector(ABC):
    """Abstract interface for pose detection implementations"""

    @abstractmethod
    def detect_pose(self, frame: np.ndarray) -> PoseResult:
        """Detect pose in single frame"""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize detection model"""

    @abstractmethod
    def release(self) -> None:
        """Release resources"""
```

#### BaseVideoProcessor
```python
class BaseVideoProcessor(ABC):
    """Abstract interface for video processing implementations"""

    @abstractmethod
    def _initialize_detector(self) -> Any:
        """Initialize specific detector"""

    @abstractmethod
    def _detect_frame(self, frame: np.ndarray, frame_idx: int) -> ProcessingResult:
        """Process single frame"""

    def process_video(self, video_path: str) -> Dict:
        """Template method for video processing"""
```

### JavaScript Module Interfaces

#### GalleryCore
```javascript
class GalleryCore {
    // Initialization
    async initialize()

    // Data management
    render(videos)
    reload()

    // User interactions
    filter(filter)
    search(query)
    sort(field, order)

    // Video operations
    openVideo(videoId)
    closeVideo()

    // Lifecycle
    destroy()
}
```

#### GalleryDataStore
```javascript
class GalleryDataStore {
    // Data loading
    async loadFromAPI()
    getSampleData()

    // CRUD operations
    getVideos()
    getVideoById(id)
    addVideo(video)
    updateVideo(id, updates)
    removeVideo(id)

    // Events
    on(event, handler)
    off(event, handler)
}
```

## Configuration Management

### Environment-Based Configuration

The system uses environment-specific configuration:

```
Development (.env.development):
- Local API endpoints
- Debug logging enabled
- Sample data fallbacks

Production (.env.production):
- Production API endpoints
- Error logging only
- Real data sources
```

### Configuration Files

```
Configuration Hierarchy:
├── .env.{environment}          # Environment variables
├── cli/src/config/settings.py  # Python configuration
├── package.json                # Node.js dependencies & scripts
├── pyproject.toml             # Python project configuration
└── vite.config.js             # Build system configuration
```

## Testing Architecture

### Multi-Language Testing Strategy

```
tests/
├── python/                     # Python tests
│   ├── unit/                   # Unit tests for core classes
│   │   ├── test_base_detector.py
│   │   └── test_base_processor.py
│   │
│   └── integration/            # Integration tests
│       └── test_video_processing.py
│
├── javascript/                 # JavaScript tests
│   ├── unit/                   # Module unit tests
│   └── integration/            # Feature integration tests
│
└── e2e/                        # End-to-end tests
    └── playwright/             # Browser automation tests
```

#### Testing Patterns

1. **Unit Tests**: Individual module testing with mocks
2. **Integration Tests**: Multi-module workflow testing
3. **E2E Tests**: Full user journey testing
4. **Performance Tests**: Load and speed benchmarking

## Build & Deployment Architecture

### Development Workflow

```
Development Stack:
├── Vite (Frontend build system)
├── FastAPI (Backend development server)
├── Python virtual environment
└── Node.js package management
```

### Build Process

```
Build Pipeline:
├── Asset Processing (Vite)
│   ├── JavaScript bundling
│   ├── CSS processing
│   └── Asset optimization
│
├── Python Environment
│   ├── Dependency installation
│   ├── Virtual environment setup
│   └── CLI tool packaging
│
└── Integration Testing
    ├── Unit test execution
    ├── Integration test suite
    └── E2E test validation
```

### Deployment Options

1. **Local Development**: Full stack on localhost
2. **Render.com**: Production web deployment
3. **CLI Distribution**: Standalone Python package

## Performance Considerations

### Frontend Performance

- **Lazy Loading**: Images loaded on demand
- **Virtual Scrolling**: Large lists handled efficiently
- **Caching**: API responses cached with TTL
- **Progressive Enhancement**: Features enabled based on capability

### Backend Performance

- **Background Processing**: Long-running tasks handled asynchronously
- **Streaming**: Large file uploads handled with streaming
- **Memory Management**: Efficient video processing pipelines
- **Caching**: Results cached to avoid reprocessing

### Processing Performance

- **Batch Processing**: Frames processed in optimized batches
- **Progress Tracking**: Real-time feedback for long operations
- **Memory Optimization**: Large videos processed in chunks
- **GPU Acceleration**: MediaPipe GPU support when available

## Security Considerations

### Frontend Security

- **Input Validation**: File type and size validation
- **CSP Headers**: Content Security Policy implementation
- **CORS Configuration**: Proper origin restrictions

### Backend Security

- **File Upload Security**: Type validation, size limits, scan capabilities
- **API Rate Limiting**: Request throttling and abuse prevention
- **Storage Security**: Secure file handling and access controls

## Monitoring & Observability

### Logging Strategy

```python
# Structured logging across all modules
logger = logging.getLogger(__name__)
logger.info("Processing started", extra={
    "video_path": video_path,
    "processor": self.__class__.__name__
})
```

### Metrics Collection

- **Processing Metrics**: Frame rate, detection accuracy, processing time
- **System Metrics**: Memory usage, disk usage, error rates
- **User Metrics**: Upload success rates, processing completion rates

## Extensibility Points

### Adding New Detection Methods

1. Implement `BasePoseDetector` interface
2. Register in detector factory
3. Add configuration options
4. Update documentation

### Adding New Export Formats

1. Extend `BaseVideoProcessor.export_*` methods
2. Add format-specific serialization
3. Update CLI options
4. Add format documentation

### Adding New UI Components

1. Create component in `frontend/js/components/`
2. Follow existing module patterns
3. Add to main entry points
4. Update style system

## Migration Patterns

The architecture supports gradual migration patterns:

1. **Legacy Compatibility**: Adapters maintain backward compatibility
2. **Feature Toggles**: New features can be enabled incrementally
3. **Progressive Enhancement**: Core functionality works without advanced features
4. **Graceful Degradation**: System remains functional when components fail

This architecture provides a solid foundation for the current MVP while supporting future enhancements and scaling requirements.