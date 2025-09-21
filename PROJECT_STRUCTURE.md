# BodyScript Project Structure

## Overview
This document describes the reorganized structure of the BodyScript project after consolidation from 97+ scattered files.

## Directory Structure

```
bodyscript/
├── src/                    # Production source code
│   ├── core/              # Core modules (existing)
│   ├── processors/        # Main pose detection processors
│   └── video/            # Video processing utilities
│
├── experiments/           # Experimental and test code
│   ├── optimization/     # Optimization experiments
│   │   ├── frame_analysis/    # Frame-by-frame analysis
│   │   ├── recovery/         # Pose recovery approaches
│   │   ├── rotation_fixes/   # Rotation detection fixes
│   │   └── testing/          # Test variations
│   └── visualization/    # Visualization experiments
│
├── scripts/              # Executable scripts
│   ├── pipelines/       # Pipeline shell scripts
│   └── utilities/       # Utility scripts
│
├── data/                # Input data
│   ├── videos/         # Input video files
│   └── frames/         # Temporary frame extraction
│
├── output/              # Generated outputs
│   ├── csv/            # Pose data CSV files
│   ├── videos/         # Generated videos
│   ├── images/         # Comparison images
│   └── reports/        # Analysis reports
│
├── docs/                # Documentation
├── examples/            # Usage examples
├── tests/               # Unit tests
├── web/                 # Web application (future)
└── requirements/        # Dependency files
```

## Key Files

### Production Processors (`src/processors/`)
- `mediapipe_fast_smart.py` - Fast adaptive processor (recommended)
- `mediapipe_final_optimized.py` - High-quality processor
- `unified_optimization.py` - Latest unified approach
- `simple_pose_analyzer.py` - Original MVP implementation

### Video Utilities (`src/video/`)
- `skeleton_overlay.py` - Skeleton video generation
- `frame_extractor.py` - Frame extraction from video

### Pipeline Scripts (`scripts/pipelines/`)
- `run_mediapipe_fast.sh` - Fast processing pipeline
- `run_mediapipe_final.sh` - Quality processing pipeline
- `run_true_frame_analysis.sh` - Frame-by-frame analysis

## Usage Examples

### Process a video with fast mode:
```bash
./scripts/pipelines/run_mediapipe_fast.sh data/videos/dance.mp4 smart
```

### Extract frames:
```python
from src.video.frame_extractor import extract_frames
extract_frames("data/videos/dance.mp4", "data/frames/dance")
```

### Use pose processor:
```python
from src.processors import MediaPipeFastSmart
processor = MediaPipeFastSmart(mode='smart')
results = processor.process_video_fast('data/frames/dance', 'output/csv/dance.csv')
```

## Migration Notes

- **Backups**: Created at `bodyscript_backup_*.tar.gz`
- **Archives**: Frame directories archived at `frame_directories_archive_*.tar.gz`
- **Deprecated**: Old video creation scripts archived in `experiments/optimization/testing/archived_video_creation/`
- **Disk saved**: ~2GB from removing duplicate frame directories

## Development Guidelines

1. Production code goes in `src/`
2. Experiments go in `experiments/`
3. Use `data/frames/` for temporary frame extraction
4. All outputs go to `output/` subdirectories
5. Keep frame directories under 1GB
6. Clean up frames after processing