# BodyScript - Simple Pose Estimation System

A simple, research-focused pose estimation system for extracting human skeletal data from videos.

## ⚠️ Important Note

This project requires MediaPipe, which currently supports Python 3.8-3.11. If you're using Python 3.13+, the system will use a placeholder implementation for development purposes. For production use, please use Python 3.8-3.11.

## Features

- 📹 Process video files (MP4, AVI, MOV, WMV)
- 🦴 Extract 33 body pose landmarks per frame
- 📊 Export data to CSV and JSON formats
- 🎥 Create skeleton overlay videos
- 📈 Generate visualizations and statistics
- 📋 Batch process multiple videos
- 🔍 Calculate joint angles for biomechanical analysis

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

### Basic Video Processing

```python
from simple_pose_analyzer import SimplePoseAnalyzer

# Create analyzer
analyzer = SimplePoseAnalyzer(detection_confidence=0.5)

# Process video
results = analyzer.process_video("video.mp4")

# Export data
analyzer.export_csv("pose_data.csv")
analyzer.create_overlay_video("video.mp4")
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

```
bodyscript/
├── core/                    # Core modules
│   ├── video_loader.py     # Video processing
│   ├── pose_detector.py    # Pose detection
│   ├── data_exporter.py    # Data export
│   └── config.py           # Configuration
├── utils/                   # Utilities
│   └── visualization.py    # Plotting functions
├── examples/               # Example scripts
├── output/                 # Default output directory
└── simple_pose_analyzer.py # Main interface
```

## Configuration

Edit `core/config.py` to adjust:
- Detection confidence thresholds
- Output video settings
- File size limits
- Processing parameters

## Performance

- **Processing Speed**: 1-2x real-time (depends on resolution)
- **Memory Usage**: <2GB for typical videos
- **Detection Rate**: >80% on good quality videos
- **Supported Resolution**: 480p to 1080p
- **Max Video Duration**: 10 minutes (configurable)

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

## Future Enhancements

- Hand pose detection (21 landmarks per hand)
- Face landmarks (468 points)
- Real-time processing
- Web interface
- 3D pose estimation

## Contributing

Feel free to submit issues or enhancement requests!

## License

This project is for research and educational purposes.