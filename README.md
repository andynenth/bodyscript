# BodyScript - Simple Pose Estimation System

A simple, research-focused pose estimation system for extracting human skeletal data from videos.

## ⚠️ Important Note

This project requires MediaPipe, which currently supports Python 3.8-3.11. If you're using Python 3.13+, the system will use a placeholder implementation for development purposes. For production use, please use Python 3.8-3.11.

## Features

### Core Processing
- 📹 Process video files (MP4, AVI, MOV, WMV)
- 🦴 Extract 33 body pose landmarks per frame
- 📊 Export data to CSV and JSON formats
- 🎥 Create skeleton overlay videos
- 📈 Generate visualizations and statistics
- 📋 Batch process multiple videos
- 🔍 Calculate joint angles for biomechanical analysis

### Web Interface
- 🌐 Modern web gallery for video browsing
- 🎯 Interactive filtering and search
- 📱 Mobile-responsive design with touch support
- 🚀 Lazy loading and performance optimization
- 🎮 Video hover previews and modal playback
- ☁️ Cloud storage integration (R2)

### Architecture
- 🏗️ Modular JavaScript architecture (no frameworks)
- 🐍 Abstract base classes for Python components
- 🧪 Comprehensive testing (unit, integration, E2E)
- 📚 Complete API documentation with JSDoc/docstrings
- 🔄 Template method pattern eliminates code duplication

## Development Guidelines

### Version Control Best Practices

- **Use Git branches for backups and experiments** - Never create backup directories (e.g., `frontend_backup_*`)
- **Feature branches** - Create feature branches for major changes
- **Clean working directory** - Keep the repository clean, use `.gitignore` for temporary files

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd bodyscript

# Create virtual environment (Python 3.8-3.11 recommended)
python -m venv venv

# Activate environment
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements_mvp.txt

# For Python 3.13+ (without MediaPipe)
pip install opencv-python pandas numpy matplotlib tqdm
```

### 2. Test Installation

```bash
python examples/test_installation.py
```

### 3. Process Your First Video

```bash
# Process a single video
python examples/process_video_simple.py path/to/your/video.mp4

# Or use the main analyzer directly
python simple_pose_analyzer.py
```

## Usage Examples

### Basic Video Processing (CLI)

```python
# Using the new modular architecture
from cli.src.core.base_processor import BaseVideoProcessor
from cli.examples.process_video_simple import SimplePoseAnalyzer

# Create analyzer with configuration
analyzer = SimplePoseAnalyzer(
    detection_confidence=0.5,
    tracking_confidence=0.5,
    output_dir="my_output"
)

# Process video using template method pattern
result = analyzer.process_video("video.mp4")

# Export data (auto-generated filenames)
csv_path = analyzer.export_csv()
json_path = analyzer.export_json()
df = analyzer.get_dataframe()
```

### Web Interface Usage

```javascript
// Using the new modular frontend architecture
import { GalleryCore } from './js/core/GalleryCore.js';

// Initialize gallery with features
const gallery = new GalleryCore({
    containerSelector: '#videoGrid',
    enableHoverPreview: true,
    enableLazyLoading: true,
    enableTouchSupport: true
});

// Initialize and load data
await gallery.initialize();

// Use gallery API
gallery.filter('dance');
gallery.search('yoga');
gallery.sort('accuracy', 'desc');
```

### Batch Processing

```bash
# Process all videos in a folder
python examples/batch_process_videos.py /path/to/video/folder/
```

### Webcam Test

```bash
# Test with webcam (real-time)
python examples/webcam_pose_test.py
```

## Output Files

After processing, you'll find:
- `pose_data_*.csv` - Frame-by-frame landmark coordinates
- `pose_analysis_*.json` - Comprehensive analysis data
- `skeleton_overlay_*.mp4` - Video with pose overlay
- `summary_report_*.txt` - Processing statistics
- Various visualization plots (trajectories, confidence, heatmaps)

## CSV Data Format

```csv
frame_id,timestamp,landmark_id,landmark_name,x,y,z,visibility,confidence
0,0.000,0,nose,0.501,0.298,0.012,0.95,0.95
...
```

## Project Structure

BodyScript uses a modern, modular architecture with clear separation of concerns:

```
bodyscript/
├── frontend/               # Web UI (Modular JavaScript)
│   ├── js/
│   │   ├── core/          # Core business logic modules
│   │   ├── components/    # Reusable UI components
│   │   ├── utils/         # Utility functions
│   │   └── entries/       # Page-specific implementations
│   ├── css/               # Modular stylesheets
│   └── assets/            # Static assets
│
├── backend/                # FastAPI Web Service
│   ├── app.py             # Main FastAPI application
│   ├── process_wrapper.py # Video processing orchestrator
│   ├── admin_routes.py    # Gallery management
│   └── storage_r2.py      # Cloud storage integration
│
├── cli/                    # Command Line Interface
│   ├── src/
│   │   ├── core/          # Abstract base classes
│   │   ├── video/         # Video processing modules
│   │   └── config/        # Configuration management
│   ├── utils/             # Shared utilities
│   ├── examples/          # Usage examples
│   └── scripts/           # Utility scripts
│
├── tests/                  # Comprehensive test suite
│   ├── python/            # Python tests (unit & integration)
│   ├── javascript/        # JavaScript tests
│   └── e2e/               # End-to-end tests
│
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md    # System architecture
│   ├── MIGRATION_GUIDE.md # Legacy migration guide
│   └── technical_*.md     # Technical references
│
└── output/                 # Default output directory
```

## Configuration

### CLI Configuration

```python
# Using configuration objects
from cli.src.core.base_detector import PoseConfig

config = PoseConfig(
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    enable_segmentation=False,
    smooth_landmarks=True
)

processor = MyProcessor(config)
```

### Web Configuration

```javascript
// Environment-based configuration
// .env.development or .env.production
API_URL=http://localhost:8000
ENABLE_DEBUG=true
ENABLE_SAMPLE_DATA=true
```

### Build Configuration

Configuration files:
- `.env.{environment}` - Environment variables
- `cli/src/config/settings.py` - Python configuration
- `vite.config.js` - Build system configuration
- `package.json` - Node.js dependencies

## Performance

### Processing Performance
- **Processing Speed**: 1-2x real-time (depends on resolution)
- **Memory Usage**: <2GB for typical videos
- **Detection Rate**: >80% on good quality videos
- **Supported Resolution**: 480p to 1080p
- **Max Video Duration**: 10 minutes (configurable)

### Web Performance
- **Lazy Loading**: Images loaded on demand
- **Caching**: API responses cached (5-minute TTL)
- **Virtual Scrolling**: Handles large video galleries
- **Progressive Enhancement**: Core functionality works without advanced features
- **Mobile Optimization**: Touch gestures and responsive design

## Troubleshooting

### "No module named mediapipe"
- Use Python 3.8-3.11 for MediaPipe support
- For Python 3.13+, the system uses placeholder detection

### Low detection rate
- Ensure good lighting in video
- Try lowering detection confidence: `SimplePoseAnalyzer(detection_confidence=0.3)`
- Check video quality (minimum 480p recommended)

### Memory errors
- Process shorter videos or reduce resolution
- Increase batch size in config.py
- Close other applications

## Limitations

- Body pose only (no hands/face in MVP version)
- Single or multiple person detection
- Works best with clear, well-lit videos
- Requires Python 3.8-3.11 for full functionality

## Architecture & Development

### Key Design Patterns
- **Template Method**: Common processing workflow with customizable steps
- **Abstract Factory**: Different pose detector implementations
- **Observer Pattern**: Event-driven communication between modules
- **Module Pattern**: Clean JavaScript modules with clear APIs

### Development Workflow
```bash
# Development setup
npm run dev          # Start development servers
npm run test         # Run all tests
npm run build        # Build for production

# Python development
python -m pytest tests/python/  # Run Python tests
python cli/examples/process_video_simple.py video.mp4
```

### Documentation
- **Architecture Overview**: `/docs/ARCHITECTURE.md`
- **Migration Guide**: `/docs/MIGRATION_GUIDE.md`
- **API Documentation**: Inline JSDoc and Python docstrings
- **Build Documentation**: `/README-BUILD.md`

## Future Enhancements

- Hand pose detection (21 landmarks per hand)
- Face landmarks (468 points)
- Real-time processing with WebRTC
- AI-powered movement analysis
- 3D pose estimation
- Advanced biomechanical analytics

## Contributing

Feel free to submit issues or enhancement requests!

## License

This project is for research and educational purposes.