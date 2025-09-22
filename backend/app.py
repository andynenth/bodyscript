#!/usr/bin/env python3
"""
Minimal FastAPI application for BodyScript pose detection web service.
Portfolio MVP version - simple, functional, demonstrable.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uuid
import shutil
import os
import time
from datetime import datetime
from typing import Dict, Any
import json

from process_wrapper import WebVideoProcessor

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


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "jobs_in_memory": len(jobs_status)
    }


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
        jobs_status[job_id]["progress"] = progress
        jobs_status[job_id]["message"] = message
        jobs_status[job_id]["status"] = "processing"

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )