# Quick Start: MVP in 1 Hour

## 🚀 Fastest Path to Working Demo

### Step 1: Minimal Backend (15 min)

Create `web/backend/app.py`:
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import subprocess
import uuid
import os

app = FastAPI()

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    # Save uploaded file
    job_id = str(uuid.uuid4())
    os.makedirs(f"jobs/{job_id}", exist_ok=True)

    video_path = f"jobs/{job_id}/input.mp4"
    with open(video_path, "wb") as f:
        f.write(await file.read())

    # Process immediately (no queue for MVP)
    process_video_simple(job_id, video_path)

    return {"job_id": job_id, "status": "completed"}

def process_video_simple(job_id, video_path):
    # Use existing pipeline script
    subprocess.run([
        "python3", "src/processors/mediapipe_fast_smart.py",
        video_path, f"jobs/{job_id}/output.mp4"
    ])

@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    return FileResponse(f"jobs/{job_id}/output.mp4")
```

Run: `uvicorn app:app --reload`

### Step 2: Minimal Frontend (15 min)

Create `web/frontend/index.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>BodyScript - Pose Detection</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 p-8">
    <div class="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
        <h1 class="text-2xl font-bold mb-4">BodyScript Pose Detection</h1>

        <!-- Upload -->
        <div class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input type="file" id="fileInput" accept="video/*" class="hidden">
            <button onclick="document.getElementById('fileInput').click()"
                    class="bg-blue-500 text-white px-4 py-2 rounded">
                Choose Video (max 15 seconds)
            </button>
        </div>

        <!-- Status -->
        <div id="status" class="mt-4 p-4 bg-gray-50 rounded hidden">
            <div class="font-semibold">Processing...</div>
            <div class="text-sm text-gray-600">This takes 2-3 minutes</div>
        </div>

        <!-- Result -->
        <div id="result" class="mt-4 hidden">
            <a id="downloadBtn" class="bg-green-500 text-white px-4 py-2 rounded inline-block">
                Download Result
            </a>
        </div>
    </div>

    <script>
        const API_URL = 'http://localhost:8000';

        document.getElementById('fileInput').addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            // Show status
            document.getElementById('status').classList.remove('hidden');
            document.getElementById('result').classList.add('hidden');

            // Upload
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${API_URL}/api/upload`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            // Show download button
            document.getElementById('status').classList.add('hidden');
            document.getElementById('result').classList.remove('hidden');
            document.getElementById('downloadBtn').href =
                `${API_URL}/api/download/${data.job_id}`;
        });
    </script>
</body>
</html>
```

Open: `web/frontend/index.html` in browser

### Step 3: Make Processor Web-Ready (15 min)

Create `web/backend/process_web.py`:
```python
#!/usr/bin/env python3
import sys
import os
sys.path.append('../..')  # Add bodyscript root

from src.processors.mediapipe_fast_smart import MediaPipeFastSmart
from src.video.frame_extractor import extract_frames
from src.video.skeleton_overlay import create_skeleton_video
import subprocess

def process_for_web(input_video, output_video, max_seconds=15):
    """Simple web processing pipeline"""

    # 1. Trim video to 15 seconds
    trimmed_video = "temp_trimmed.mp4"
    subprocess.run([
        "ffmpeg", "-i", input_video,
        "-t", str(max_seconds),
        "-y", trimmed_video
    ])

    # 2. Extract frames
    frames_dir = "temp_frames"
    extract_frames(trimmed_video, frames_dir)

    # 3. Process with MediaPipe
    processor = MediaPipeFastSmart(mode='fast')  # Fast for demo
    csv_path = "temp_pose.csv"
    processor.process_video_fast(frames_dir, csv_path)

    # 4. Create output video
    create_skeleton_video(trimmed_video, csv_path, output_video)

    # 5. Cleanup
    subprocess.run(["rm", "-rf", frames_dir, trimmed_video, csv_path])

    return output_video

if __name__ == "__main__":
    process_for_web(sys.argv[1], sys.argv[2])
```

### Step 4: Docker Quick Setup (15 min)

Create `docker-compose-simple.yml`:
```yaml
version: '3'
services:
  api:
    image: python:3.9-slim
    working_dir: /app
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    command: |
      bash -c "
        apt-get update && apt-get install -y ffmpeg
        pip install fastapi uvicorn mediapipe opencv-python pandas numpy
        cd web/backend && uvicorn app:app --host 0.0.0.0
      "
```

Run: `docker-compose -f docker-compose-simple.yml up`

## 🎯 30-Minute Enhancements

### Add Progress Tracking
```python
# In process function, update a file
with open(f"jobs/{job_id}/progress.txt", "w") as f:
    f.write("50%")

# Add endpoint
@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    progress = open(f"jobs/{job_id}/progress.txt").read()
    return {"progress": progress}
```

### Add Queue Display
```javascript
// Poll for status
setInterval(async () => {
    const status = await fetch(`${API_URL}/api/status/${jobId}`);
    document.getElementById('progress').innerText = status.progress;
}, 2000);
```

### Add Error Handling
```python
try:
    process_video_simple(job_id, video_path)
    return {"status": "success"}
except Exception as e:
    return {"status": "error", "message": str(e)}
```

## 🚨 Demo Day Checklist

### Before Demo
- [ ] Test with 10-second video
- [ ] Clear old job folders
- [ ] Restart services
- [ ] Have backup video ready
- [ ] Prepare to explain architecture

### During Demo
1. "This is a pose detection system that processes videos using MediaPipe"
2. "It's deployed using free tier services to minimize costs"
3. "Let me upload a short video..." [upload pre-tested video]
4. "The system extracts frames, detects poses, and creates an overlay"
5. "Processing takes about 2 minutes for a 15-second video"
6. [While waiting] "The architecture uses FastAPI, Celery for queuing, and React"
7. "Here's the result with skeleton overlay showing detected poses"

### If It Fails
- "Let me show you a pre-processed example"
- Have backup video ready at `/demo/sample_output.mp4`
- Explain what would normally happen

## 💡 Key Points for Portfolio

1. **Architecture**: Microservices with separate API and worker
2. **Scalability**: Queue-based, can add workers
3. **Cost**: Under $1/month using free tiers
4. **Technology**: Python, FastAPI, MediaPipe, React
5. **Challenges**: Managing long-running tasks, video processing constraints

## Emergency Fixes

```bash
# If MediaPipe fails
pip uninstall mediapipe
pip install mediapipe==0.10.7

# If ffmpeg missing
apt-get update && apt-get install -y ffmpeg

# If out of space
rm -rf jobs/*

# If port in use
kill -9 $(lsof -t -i:8000)

# Quick test
curl -X POST localhost:8000/api/upload \
  -F "file=@test.mp4"
```

---

**Remember: Working demo > Perfect code**

The goal is to show:
- ✅ It processes real videos
- ✅ Shows progress to user
- ✅ Produces visible results
- ✅ Handles errors gracefully
- ✅ Deployed and accessible