#!/usr/bin/env python3
"""
Minimal FastAPI application for BodyScript pose detection web service.
Portfolio MVP version - simple, functional, demonstrable.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uuid
import shutil
import os
import time
from datetime import datetime
from typing import Dict, Any
import json

from process_wrapper import WebVideoProcessor
from admin_routes import router as admin_router

# Track startup time for uptime monitoring
START_TIME = time.time()

# Initialize FastAPI app
app = FastAPI(
    title="BodyScript Pose Detection API",
    description="Web service for pose detection in videos using MediaPipe",
    version="1.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processor
processor = WebVideoProcessor()

# Include admin router for gallery curation
app.include_router(admin_router)

# In-memory job storage (no database for MVP)
jobs_status: Dict[str, Any] = {}

# Configuration
MAX_VIDEO_SIZE_MB = 100
MAX_VIDEO_DURATION_SECONDS = 15
ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "BodyScript Pose Detection API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upload": "/api/upload",
            "status": "/api/status/{job_id}",
            "download": "/api/download/{job_id}/video",
            "download_csv": "/api/download/{job_id}/csv",
            "health": "/health"
        }
    }


@app.get("/api/serve/{job_id}/{filename}")
async def serve_local_file(job_id: str, filename: str):
    """Serve local files for gallery display."""
    from pathlib import Path

    file_path = Path("temp") / job_id / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type
    if filename.endswith('.jpg'):
        media_type = "image/jpeg"
    elif filename.endswith('.mp4'):
        media_type = "video/mp4"
    elif filename.endswith('.csv'):
        media_type = "text/csv"
    else:
        media_type = "application/octet-stream"

    return FileResponse(str(file_path), media_type=media_type)


@app.get("/api/gallery")
async def get_gallery():
    """Get gallery videos for display."""
    import json
    from pathlib import Path

    # Check for local gallery.json file
    gallery_file = Path("temp") / "gallery.json"

    if gallery_file.exists():
        with open(gallery_file) as f:
            data = json.load(f)

            # Add tags to each video based on category
            tag_mapping = {
                'dance': ['#bodyscript', '#dance', '#movement', '#posedetection'],
                'martial': ['#bodyscript', '#martial', '#sports', '#combat'],
                'sports': ['#bodyscript', '#sports', '#athletics', '#fitness'],
                'yoga': ['#bodyscript', '#yoga', '#wellness', '#mindfulness']
            }

            for video in data.get('videos', []):
                category = video.get('category', 'dance')
                video['tags'] = tag_mapping.get(category, ['#bodyscript', '#movement'])
                # Add title-specific tags
                if 'salif' in video.get('title', '').lower():
                    video['tags'].append('#hiphop')
                elif 'shaolin' in video.get('title', '').lower():
                    video['tags'].append('#kungfu')
                elif 'teofimo' in video.get('title', '').lower():
                    video['tags'].append('#boxing')

            return data

    # Return empty gallery if no file exists
    return {"videos": []}


@app.get("/health")
async def health_check():
    """Enhanced health check with cold start detection and uptime."""
    uptime_seconds = time.time() - START_TIME

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(uptime_seconds, 2),
        "cold_start": uptime_seconds < 60,  # True if just started
        "jobs_in_memory": len(jobs_status),
        "free_tier_note": "Server may sleep after 15 min inactivity on Render free tier",
        "service": "bodyscript-api"
    }


@app.on_event("startup")
async def startup_event():
    """Pre-load heavy libraries at startup to reduce cold start time."""
    print("Starting BodyScript API...")

    # Pre-load heavy libraries
    try:
        import mediapipe
        import cv2
        import pandas
        print("Heavy libraries loaded successfully")
    except Exception as e:
        print(f"Warning: Failed to pre-load some libraries: {e}")

    print(f"API ready to serve requests at {datetime.now().isoformat()}")


@app.post("/api/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a video for pose detection processing.

    Returns:
        job_id and initial status
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Create temp directory for this job
    temp_dir = Path("web/temp") / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Save uploaded file
        input_path = temp_dir / f"input{file_ext}"
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Check file size
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        if file_size_mb > MAX_VIDEO_SIZE_MB:
            shutil.rmtree(temp_dir)
            raise HTTPException(
                status_code=400,
                detail=f"Video too large. Maximum size: {MAX_VIDEO_SIZE_MB}MB"
            )

        # Initialize job status
        jobs_status[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0,
            "message": "Video uploaded successfully",
            "created_at": datetime.now().isoformat(),
            "filename": file.filename,
            "file_size_mb": round(file_size_mb, 2)
        }

        # Process video in background
        background_tasks.add_task(
            process_video_task,
            job_id,
            str(input_path)
        )

        return {
            "job_id": job_id,
            "status": "pending",
            "message": f"Video '{file.filename}' uploaded successfully. Processing will begin shortly.",
            "file_size_mb": round(file_size_mb, 2)
        }

    except Exception as e:
        # Clean up on error
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=str(e))


def process_video_task(job_id: str, video_path: str):
    """Background task to process video."""
    def update_progress(progress: int, message: str):
        # Check if job was cancelled
        if jobs_status[job_id].get("cancelled"):
            raise Exception("Job cancelled by user")

        jobs_status[job_id]["progress"] = progress
        jobs_status[job_id]["message"] = message
        jobs_status[job_id]["status"] = "processing"

        # Extract frame info from message if present
        import re
        frame_match = re.search(r"frame (\d+)/(\d+)", message, re.IGNORECASE)
        if frame_match:
            jobs_status[job_id]["current_frame"] = int(frame_match.group(1))
            jobs_status[job_id]["total_frames"] = int(frame_match.group(2))

    try:
        # Update status to processing
        jobs_status[job_id]["status"] = "processing"
        jobs_status[job_id]["started_at"] = datetime.now().isoformat()

        # Process video
        result = processor.process_video(
            video_path,
            job_id,
            mode='fast',  # Use fast mode for demo
            progress_callback=update_progress
        )

        if result['success']:
            jobs_status[job_id].update({
                "status": "completed",
                "progress": 100,
                "message": "Processing completed successfully",
                "completed_at": datetime.now().isoformat(),
                "output_video": result['output_video'],
                "pose_data_csv": result['pose_data_csv'],
                "statistics": result['statistics']
            })
        else:
            jobs_status[job_id].update({
                "status": "failed",
                "message": f"Processing failed: {result['error']}",
                "error": result['error'],
                "completed_at": datetime.now().isoformat()
            })

    except Exception as e:
        # Check if it was a cancellation
        if "cancelled by user" in str(e).lower() or jobs_status[job_id].get("cancelled"):
            jobs_status[job_id].update({
                "status": "cancelled",
                "message": "Job cancelled by user",
                "completed_at": datetime.now().isoformat()
            })
            # Clean up files for cancelled job
            processor.cleanup_job(job_id)
        else:
            jobs_status[job_id].update({
                "status": "failed",
                "message": f"Processing failed: {str(e)}",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a processing job."""
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="Job not found")

    status = jobs_status[job_id].copy()

    # Add queue position if pending
    if status["status"] == "pending":
        pending_jobs = [j for j, s in jobs_status.items()
                       if s["status"] == "pending"]
        if job_id in pending_jobs:
            status["queue_position"] = pending_jobs.index(job_id) + 1
            status["queue_total"] = len(pending_jobs)

    return status


@app.post("/api/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a processing job."""
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_status[job_id]

    # Only cancel if still processing
    if job["status"] in ["pending", "processing"]:
        job["status"] = "cancelled"
        job["cancelled"] = True
        job["message"] = "Job cancelled by user"

        # Clean up files
        processor.cleanup_job(job_id)

        return {"message": f"Job {job_id} cancelled successfully"}
    else:
        return {"message": f"Job {job_id} already {job['status']}, cannot cancel"}


@app.get("/api/download/{job_id}/video")
async def download_video(job_id: str):
    """Download the processed video with skeleton overlay."""
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_status[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is {job['status']}. Cannot download."
        )

    video_path = job.get("output_video")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Output video not found")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"bodyscript_pose_{job_id}.mp4"
    )


@app.get("/api/download/{job_id}/csv")
async def download_csv(job_id: str):
    """Download the pose data as CSV."""
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_status[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is {job['status']}. Cannot download."
        )

    csv_path = job.get("pose_data_csv")
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="CSV data not found")

    return FileResponse(
        csv_path,
        media_type="text/csv",
        filename=f"bodyscript_pose_data_{job_id}.csv"
    )


@app.get("/api/jobs")
async def list_jobs():
    """List all jobs (for demo/debugging)."""
    return {
        "total": len(jobs_status),
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "progress": job.get("progress", 0),
                "created_at": job.get("created_at"),
                "filename": job.get("filename")
            }
            for job_id, job in jobs_status.items()
        ]
    }


@app.delete("/api/cleanup/{job_id}")
async def cleanup_job(job_id: str):
    """Clean up files for a completed job."""
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="Job not found")

    # Clean up files
    processor.cleanup_job(job_id)

    # Remove from status
    del jobs_status[job_id]

    return {"message": f"Job {job_id} cleaned up successfully"}


# Cleanup old jobs periodically (every hour)
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("=" * 60)
    print("🚀 BodyScript Pose Detection API Started")
    print("=" * 60)
    print("Endpoints:")
    print("  Upload: POST /api/upload")
    print("  Status: GET /api/status/{job_id}")
    print("  Download: GET /api/download/{job_id}/video")
    print("  Health: GET /health")
    print("=" * 60)


# Mount frontend as static files (must be last to avoid overriding API routes)
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )