# BodyScript Web Server Guide

## 🚀 Starting the Web Server

The web server provides a browser-based interface for the Creative Platform. Here's how to use it:

### Prerequisites

First, make sure you have the required dependencies installed:

```bash
# Option 1: Install just web dependencies
pip install fastapi uvicorn python-multipart aiofiles

# Option 2: Install all creative platform dependencies
pip install -r requirements_creative.txt
```

### Starting the Server

There are three ways to start the web server:

#### Method 1: Using the start script (Easiest)
```bash
python start_web_server.py
```

#### Method 2: Using the creative analyzer
```bash
python creative_pose_analyzer.py --web
```

#### Method 3: Direct module execution
```bash
python -m uvicorn creative.web.app:app --reload
```

### Accessing the Application

Once the server is running, you'll see:
```
==============================
🎨 BodyScript Creative Platform
==============================

Starting web server...

Access the application at:
  Web UI: http://localhost:8000/ui
  API Docs: http://localhost:8000/docs

Press Ctrl+C to stop the server
==============================
```

Open your web browser and go to:
- **Web Interface**: http://localhost:8000/ui - User-friendly interface
- **API Documentation**: http://localhost:8000/docs - Interactive API explorer
- **API Root**: http://localhost:8000/ - API information

### Using the Web Interface

1. **Upload Video**
   - Click "Choose File" and select your video (MP4, AVI, MOV, MKV)
   - Click "Upload" to send to server

2. **Configure Processing**
   - Choose artistic style (Realistic, Anime, Cartoon, Minimalist, Athletic)
   - Adjust smoothing strength (0-1)
   - Enable holistic detection for hands and face (optional)

3. **Process Video**
   - Click "Process Video" to start
   - Watch the progress bar for status updates

4. **Download Results**
   - Once complete, download in your preferred format:
     - JSON - Web-friendly animation data
     - CSV - Spreadsheet-compatible data
     - BVH - Motion capture format
     - FBX - 3D software format

### Using the API

The REST API allows programmatic access:

```python
import requests

# Upload video
with open('video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/upload',
        files={'file': f}
    )
video_id = response.json()['video_id']

# Process video
response = requests.post(
    'http://localhost:8000/process',
    json={
        'video_id': video_id,
        'style': 'anime',
        'animation_smoothing': 0.7,
        'export_formats': ['json', 'bvh']
    }
)
job_id = response.json()['job_id']

# Check status
response = requests.get(f'http://localhost:8000/status/{job_id}')
status = response.json()

# Download result
if status['status'] == 'completed':
    output_id = status['result']['output_id']
    response = requests.get(f'http://localhost:8000/export/{output_id}/json')
```

### API Endpoints

- `POST /upload` - Upload video file
- `POST /process` - Process video with options
- `GET /status/{job_id}` - Check processing status
- `POST /style` - Apply style transfer
- `POST /animate` - Apply animation processing
- `GET /export/{output_id}/{format}` - Download results
- `GET /preview/{output_id}` - Get preview data
- `GET /styles` - List available styles
- `GET /ui` - Web interface

### Troubleshooting

**Server won't start:**
- Make sure you're in the bodyscript directory
- Check Python version (3.8-3.11 recommended)
- Install missing dependencies: `pip install fastapi uvicorn`

**Upload fails:**
- Check file size (keep under 100MB for best performance)
- Verify video format (MP4, AVI, MOV, MKV)

**Processing fails:**
- Ensure MediaPipe is installed: `pip install mediapipe==0.10.7`
- Check available disk space for output files

**Can't access web interface:**
- Verify server is running (check terminal)
- Try different browser
- Check if port 8000 is available: `lsof -i :8000`

### Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## 🎨 Features Available in Web Version

- **Style Transfer**: Transform poses to artistic styles
- **Animation Smoothing**: Reduce jitter and create fluid motion
- **Loop Generation**: Create seamless loops
- **Multi-format Export**: JSON, CSV, BVH, FBX
- **Real-time Progress**: Track processing status
- **Preview System**: Quick visualization of results

## 📝 Notes

- The server runs locally on your machine
- No data is sent to external servers
- Processing happens in background - you can upload multiple videos
- Results are stored temporarily in `outputs/` directory
- Uploaded videos are stored in `uploads/` directory

## 🔧 Advanced Configuration

To run on a different port:
```bash
python -m uvicorn creative.web.app:app --port 8080
```

To allow external connections:
```bash
python -m uvicorn creative.web.app:app --host 0.0.0.0 --port 8000
```

To enable auto-reload during development:
```bash
python -m uvicorn creative.web.app:app --reload
```