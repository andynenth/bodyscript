"""
Web Application - FastAPI backend for creative pose processing
Provides REST API, file upload, and real-time processing
"""

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import aiofiles
import uuid
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import bodyscript modules
from core.video_loader import VideoLoader
from core.pose_detector import PoseDetector
from creative.style.style_transfer import PoseStyleTransfer
from creative.animation.animation_tools import AnimationProcessor
from creative.export.export_3d import Export3D

# Try to import HolisticPoseDetector if MediaPipe is available
try:
    from research.holistic_detector import HolisticPoseDetector
    HOLISTIC_AVAILABLE = True
except ImportError:
    HOLISTIC_AVAILABLE = False
    print("Warning: MediaPipe not available. Holistic detection disabled.")


# Initialize FastAPI app
app = FastAPI(
    title="BodyScript Creative API",
    description="Creative pose processing and animation platform",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage paths
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
STATIC_DIR = Path("static")

# Create directories
for dir_path in [UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR]:
    dir_path.mkdir(exist_ok=True)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Processing queue
processing_queue = {}


# Request/Response Models
class ProcessingRequest(BaseModel):
    video_id: str
    style: str = "realistic"
    animation_smoothing: float = 0.5
    export_formats: List[str] = ["json", "csv"]
    holistic: bool = False


class ProcessingStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float
    message: str
    result: Optional[Dict] = None


class StyleTransferRequest(BaseModel):
    pose_data_id: str
    target_style: str
    strength: float = 1.0


class AnimationRequest(BaseModel):
    pose_data_id: str
    smoothing_type: str = "gaussian"
    smoothing_strength: float = 0.5
    create_loop: bool = False
    loop_type: str = "seamless"
    target_fps: Optional[float] = None


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "BodyScript Creative API",
        "version": "1.0.0",
        "endpoints": {
            "/upload": "Upload video file",
            "/process": "Process video for pose extraction",
            "/style": "Apply style transfer",
            "/animate": "Apply animation processing",
            "/export": "Export in various formats",
            "/status": "Check job status",
            "/preview": "Get preview data"
        }
    }


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file for processing.

    Returns:
        video_id: Unique identifier for the uploaded video
    """
    # Validate file type
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate unique ID
    video_id = str(uuid.uuid4())

    # Save file
    file_path = UPLOAD_DIR / f"{video_id}{file_ext}"

    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    return {
        "video_id": video_id,
        "filename": file.filename,
        "size": len(content),
        "path": str(file_path)
    }


@app.post("/process")
async def process_video(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """
    Process uploaded video for pose extraction.

    Returns:
        job_id: Processing job identifier
    """
    # Validate video exists
    video_path = None
    for ext in ['.mp4', '.avi', '.mov', '.mkv']:
        path = UPLOAD_DIR / f"{request.video_id}{ext}"
        if path.exists():
            video_path = path
            break

    if not video_path:
        raise HTTPException(status_code=404, detail="Video not found")

    # Create job
    job_id = str(uuid.uuid4())
    processing_queue[job_id] = ProcessingStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Processing queued"
    )

    # Start background processing
    background_tasks.add_task(
        process_video_task,
        job_id,
        video_path,
        request
    )

    return {"job_id": job_id, "status": "queued"}


async def process_video_task(job_id: str, video_path: Path, request: ProcessingRequest):
    """Background task for video processing."""
    try:
        # Update status
        processing_queue[job_id].status = "processing"
        processing_queue[job_id].message = "Loading video"
        processing_queue[job_id].progress = 0.1

        # Load video
        loader = VideoLoader()
        video_data = loader.load_video(str(video_path))
        frames = list(loader.extract_frames(max_frames=300))
        metadata = loader.get_video_metadata()

        processing_queue[job_id].progress = 0.3
        processing_queue[job_id].message = "Detecting poses"

        # Detect poses
        if request.holistic and HOLISTIC_AVAILABLE:
            detector = HolisticPoseDetector()
        else:
            if request.holistic and not HOLISTIC_AVAILABLE:
                processing_queue[job_id].message = "Holistic unavailable, using basic detection"
            detector = PoseDetector()

        pose_results = detector.detect_poses(frames, progress_bar=False)

        processing_queue[job_id].progress = 0.6
        processing_queue[job_id].message = "Processing pose data"

        # Convert to DataFrame
        all_data = []
        for frame_result in pose_results:
            if hasattr(frame_result, 'to_dataframe'):
                frame_df = frame_result.to_dataframe()
                if not frame_df.empty:
                    all_data.append(frame_df)

        if all_data:
            pose_df = pd.concat(all_data, ignore_index=True)
        else:
            pose_df = pd.DataFrame()

        # Apply style transfer if requested
        if request.style != "realistic":
            processing_queue[job_id].message = f"Applying {request.style} style"
            transfer = PoseStyleTransfer()
            pose_df = transfer.transform_pose(pose_df, request.style)

        # Apply animation smoothing
        if request.animation_smoothing > 0:
            processing_queue[job_id].message = "Smoothing animation"
            processor = AnimationProcessor(fps=metadata.get('fps', 30))
            pose_df = processor.smooth_animation(
                pose_df,
                strength=request.animation_smoothing
            )

        processing_queue[job_id].progress = 0.8
        processing_queue[job_id].message = "Exporting results"

        # Save processed data
        output_id = str(uuid.uuid4())
        output_base = OUTPUT_DIR / output_id

        # Export in requested formats
        export_paths = {}
        exporter = Export3D(fps=metadata.get('fps', 30))

        for format_type in request.export_formats:
            if format_type == "json":
                path = exporter.export_to_json_animation(
                    pose_df,
                    f"{output_base}.json"
                )
                export_paths["json"] = path
            elif format_type == "csv":
                path = exporter.export_to_csv_3d(
                    pose_df,
                    f"{output_base}.csv"
                )
                export_paths["csv"] = path
            elif format_type == "bvh":
                path = exporter.export_to_bvh(
                    pose_df,
                    f"{output_base}.bvh"
                )
                export_paths["bvh"] = path
            elif format_type == "fbx":
                path = exporter.export_to_fbx_ascii(
                    pose_df,
                    f"{output_base}.fbx"
                )
                export_paths["fbx"] = path

        # Update status
        processing_queue[job_id].status = "completed"
        processing_queue[job_id].progress = 1.0
        processing_queue[job_id].message = "Processing complete"
        processing_queue[job_id].result = {
            "output_id": output_id,
            "exports": export_paths,
            "frames_processed": len(frames),
            "landmarks_detected": len(pose_df) // len(frames) if frames else 0,
            "metadata": metadata
        }

    except Exception as e:
        processing_queue[job_id].status = "failed"
        processing_queue[job_id].message = str(e)
        processing_queue[job_id].progress = 0.0


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Get processing job status."""
    if job_id not in processing_queue:
        raise HTTPException(status_code=404, detail="Job not found")

    return processing_queue[job_id]


@app.post("/style")
async def apply_style(request: StyleTransferRequest):
    """Apply style transfer to pose data."""
    # Load pose data
    pose_file = OUTPUT_DIR / f"{request.pose_data_id}.csv"

    if not pose_file.exists():
        raise HTTPException(status_code=404, detail="Pose data not found")

    pose_df = pd.read_csv(pose_file)

    # Apply style transfer
    transfer = PoseStyleTransfer()
    styled_df = transfer.transform_pose(
        pose_df,
        request.target_style,
        request.strength
    )

    # Save styled data
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}_styled.csv"
    styled_df.to_csv(output_path, index=False)

    return {
        "output_id": output_id,
        "style": request.target_style,
        "strength": request.strength,
        "path": str(output_path)
    }


@app.post("/animate")
async def apply_animation(request: AnimationRequest):
    """Apply animation processing to pose data."""
    # Load pose data
    pose_file = OUTPUT_DIR / f"{request.pose_data_id}.csv"

    if not pose_file.exists():
        raise HTTPException(status_code=404, detail="Pose data not found")

    pose_df = pd.read_csv(pose_file)

    # Apply animation processing
    processor = AnimationProcessor()

    # Apply smoothing
    if request.smoothing_strength > 0:
        pose_df = processor.smooth_animation(
            pose_df,
            request.smoothing_type,
            request.smoothing_strength
        )

    # Create loop if requested
    if request.create_loop:
        pose_df = processor.create_loop(
            pose_df,
            loop_type=request.loop_type
        )

    # Interpolate frames if target FPS specified
    if request.target_fps:
        pose_df = processor.interpolate_frames(
            pose_df,
            target_fps=request.target_fps
        )

    # Save animated data
    output_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"{output_id}_animated.csv"
    pose_df.to_csv(output_path, index=False)

    return {
        "output_id": output_id,
        "frames": len(pose_df) // 33,  # Assuming 33 landmarks
        "path": str(output_path)
    }


@app.get("/export/{output_id}/{format}")
async def export_file(output_id: str, format: str):
    """Download exported file."""
    # Find file
    file_path = OUTPUT_DIR / f"{output_id}.{format}"

    if not file_path.exists():
        # Try with suffixes
        for suffix in ['_styled', '_animated', '']:
            alt_path = OUTPUT_DIR / f"{output_id}{suffix}.{format}"
            if alt_path.exists():
                file_path = alt_path
                break

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@app.get("/preview/{output_id}")
async def get_preview(output_id: str, max_frames: int = 10):
    """Get preview data for visualization."""
    # Find CSV file
    csv_file = None
    for suffix in ['', '_styled', '_animated']:
        path = OUTPUT_DIR / f"{output_id}{suffix}.csv"
        if path.exists():
            csv_file = path
            break

    if not csv_file:
        raise HTTPException(status_code=404, detail="Data not found")

    # Load pose data
    pose_df = pd.read_csv(csv_file)

    # Sample frames for preview
    unique_frames = pose_df['frame_id'].unique()[:max_frames]
    preview_df = pose_df[pose_df['frame_id'].isin(unique_frames)]

    # Convert to JSON-friendly format
    preview_data = []
    for frame_id in unique_frames:
        frame_data = preview_df[preview_df['frame_id'] == frame_id]

        landmarks = []
        for _, row in frame_data.iterrows():
            landmarks.append({
                'id': int(row.get('landmark_id', 0)),
                'x': float(row.get('x', 0)),
                'y': float(row.get('y', 0)),
                'z': float(row.get('z', 0)),
                'visibility': float(row.get('visibility', 1.0))
            })

        preview_data.append({
            'frame': int(frame_id),
            'landmarks': landmarks
        })

    return {
        "output_id": output_id,
        "total_frames": len(pose_df['frame_id'].unique()),
        "preview_frames": len(preview_data),
        "data": preview_data
    }


@app.get("/styles")
async def list_styles():
    """List available artistic styles."""
    transfer = PoseStyleTransfer()

    styles = []
    for style_name, style_profile in transfer.STYLES.items():
        styles.append({
            "name": style_name,
            "description": transfer.get_style_preview(style_name)
        })

    return {"styles": styles}


@app.get("/ui")
async def get_ui():
    """Serve basic web interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>BodyScript Creative Platform</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
                text-align: center;
            }
            .upload-box {
                border: 2px dashed #667eea;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                margin: 10px;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            }
            .status {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }
            .progress-bar {
                width: 100%;
                height: 20px;
                background: #e9ecef;
                border-radius: 10px;
                overflow: hidden;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                transition: width 0.3s;
            }
            select, input[type="range"] {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 BodyScript Creative Platform</h1>

            <div class="upload-box">
                <h2>Upload Video</h2>
                <input type="file" id="fileInput" accept="video/*">
                <br>
                <button class="btn" onclick="uploadVideo()">Upload</button>
            </div>

            <div id="controls" style="display:none;">
                <h3>Processing Options</h3>

                <label>Style:</label>
                <select id="styleSelect">
                    <option value="realistic">Realistic</option>
                    <option value="anime">Anime</option>
                    <option value="cartoon">Cartoon</option>
                    <option value="minimalist">Minimalist</option>
                    <option value="athletic">Athletic</option>
                </select>

                <label>Smoothing: <span id="smoothingValue">0.5</span></label>
                <input type="range" id="smoothingSlider" min="0" max="1" step="0.1" value="0.5"
                       oninput="document.getElementById('smoothingValue').textContent = this.value">

                <label>
                    <input type="checkbox" id="holisticCheck"> Use Holistic Detection (Body + Hands + Face)
                </label>

                <br>
                <button class="btn" onclick="processVideo()">Process Video</button>
            </div>

            <div id="status" class="status" style="display:none;">
                <h3>Processing Status</h3>
                <p id="statusMessage">Waiting...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressBar" style="width: 0%"></div>
                </div>
            </div>

            <div id="results" style="display:none;">
                <h3>Results</h3>
                <button class="btn" onclick="downloadResults('json')">Download JSON</button>
                <button class="btn" onclick="downloadResults('csv')">Download CSV</button>
                <button class="btn" onclick="downloadResults('bvh')">Download BVH</button>
                <button class="btn" onclick="downloadResults('fbx')">Download FBX</button>
            </div>
        </div>

        <script>
            let videoId = null;
            let jobId = null;
            let outputId = null;

            async function uploadVideo() {
                const fileInput = document.getElementById('fileInput');
                const file = fileInput.files[0];

                if (!file) {
                    alert('Please select a file');
                    return;
                }

                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();
                    videoId = data.video_id;

                    document.getElementById('controls').style.display = 'block';
                    alert('Video uploaded successfully!');
                } catch (error) {
                    alert('Upload failed: ' + error);
                }
            }

            async function processVideo() {
                if (!videoId) {
                    alert('Please upload a video first');
                    return;
                }

                const request = {
                    video_id: videoId,
                    style: document.getElementById('styleSelect').value,
                    animation_smoothing: parseFloat(document.getElementById('smoothingSlider').value),
                    holistic: document.getElementById('holisticCheck').checked,
                    export_formats: ['json', 'csv', 'bvh', 'fbx']
                };

                try {
                    const response = await fetch('/process', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(request)
                    });

                    const data = await response.json();
                    jobId = data.job_id;

                    document.getElementById('status').style.display = 'block';
                    checkStatus();
                } catch (error) {
                    alert('Processing failed: ' + error);
                }
            }

            async function checkStatus() {
                if (!jobId) return;

                try {
                    const response = await fetch(`/status/${jobId}`);
                    const data = await response.json();

                    document.getElementById('statusMessage').textContent = data.message;
                    document.getElementById('progressBar').style.width = (data.progress * 100) + '%';

                    if (data.status === 'completed') {
                        outputId = data.result.output_id;
                        document.getElementById('results').style.display = 'block';
                        alert('Processing complete!');
                    } else if (data.status === 'failed') {
                        alert('Processing failed: ' + data.message);
                    } else {
                        setTimeout(checkStatus, 1000);
                    }
                } catch (error) {
                    console.error('Status check failed:', error);
                    setTimeout(checkStatus, 2000);
                }
            }

            function downloadResults(format) {
                if (!outputId) return;
                window.open(`/export/${outputId}/${format}`, '_blank');
            }
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


# Run the application
if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("🎨 BodyScript Creative Platform")
    print("="*60)
    print("\nStarting web server...")
    print("\nAccess the application at:")
    print("  Web UI: http://localhost:8000/ui")
    print("  API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)