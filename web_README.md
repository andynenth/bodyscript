# BodyScript Web MVP

## Quick Start (30 seconds)

### 1. Start the Backend API
```bash
cd web/backend
source ../../venv_3.9/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

### 2. Open the Frontend
Open `web/frontend/index.html` in your browser

Or serve it with Python:
```bash
cd web/frontend
python3 -m http.server 3000
# Then open http://localhost:3000
```

### 3. Upload a Video
1. Drag and drop a video file (or click to browse)
2. Click "Start Processing"
3. Wait 2-3 minutes for processing
4. Download the result with skeleton overlay

## Features

✅ **Working Features:**
- Video upload (up to 100MB)
- Automatic trimming to 15 seconds
- Pose detection with MediaPipe
- Skeleton overlay visualization
- Progress tracking
- Download processed video
- Download pose data as CSV

## API Endpoints

- `POST /api/upload` - Upload video for processing
- `GET /api/status/{job_id}` - Check processing status
- `GET /api/download/{job_id}/video` - Download result video
- `GET /api/download/{job_id}/csv` - Download pose data
- `GET /health` - Health check

## Architecture

```
Frontend (HTML/JS)
    ↓
FastAPI Backend
    ↓
MediaPipeFastSmart Processor
    ↓
Output Video with Skeleton
```

## Processing Stats

- **Speed**: ~5-6 FPS processing
- **Quality**: 87-95% detection accuracy
- **Time**: 2-3 minutes for 15-second video
- **Mode**: Fast (6 strategies per frame)

## File Structure

```
web/
├── backend/
│   ├── app.py              # FastAPI server
│   ├── process_wrapper.py  # Video processing logic
│   └── requirements.txt    # Python dependencies
├── frontend/
│   └── index.html          # Web interface
└── temp/                   # Temporary processing files
```

## Requirements

- Python 3.9 (MediaPipe requirement)
- FFmpeg (for video processing)
- 4GB RAM minimum
- 2GB free disk space

## Troubleshooting

**Problem**: "Module not found" error
```bash
pip install fastapi uvicorn python-multipart aiofiles
```

**Problem**: Video processing fails
- Check video is MP4, AVI, MOV, or MKV
- Ensure video is less than 100MB
- Try a shorter video (< 15 seconds)

**Problem**: API not responding
- Check server is running on port 8000
- Try: `curl http://localhost:8000/health`

## Demo Instructions

For portfolio demonstration:

1. Have the backend running before demo
2. Use a pre-tested 10-second video
3. Show the upload → processing → result flow
4. Download and play the skeleton overlay video
5. Explain the architecture and technology stack

## Technology Stack

- **Backend**: FastAPI, Python 3.9
- **Processing**: MediaPipe, OpenCV
- **Frontend**: Vanilla JavaScript, TailwindCSS
- **Video**: FFmpeg for trimming/encoding

## Performance

Current implementation on test video (dance.mp4):
- Input: 13.6 seconds, 404 frames
- Processing time: 72 seconds
- Output quality: 87.7% average detection
- Output size: 7.2MB with overlay

## Next Steps for Production

1. Add Celery for proper job queue
2. Add PostgreSQL for job persistence
3. Deploy to cloud services (Render, Railway)
4. Add WebSocket for real-time updates
5. Implement user authentication
6. Add batch processing support

## License

Portfolio project - MIT License