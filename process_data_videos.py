#!/usr/bin/env python3
"""
Process videos from data/videos directory using the local API.
"""

import os
import sys
import shutil
import requests
import time
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000"
SOURCE_DIR = Path("data/videos")
TEMP_DIR = Path("backend/temp/data_videos")  # Where we'll copy videos for processing
OUTPUT_DIR = Path("data/processed_videos")  # Where we'll save results

def setup_directories():
    """Create necessary directories."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directories:")
    print(f"  - Temp: {TEMP_DIR}")
    print(f"  - Output: {OUTPUT_DIR}")

def copy_video_to_temp(video_path):
    """Copy video to backend/temp for processing."""
    filename = video_path.name
    dest_path = TEMP_DIR / filename

    print(f"  Copying {filename} to backend/temp...")
    shutil.copy2(video_path, dest_path)

    # Return path relative to backend/temp
    return f"data_videos/{filename}"

def process_video(relative_path, video_name):
    """Process a video using the local API."""
    print(f"\n📹 Processing: {video_name}")
    print("=" * 50)

    # Step 1: Start processing
    print("  Starting processing...")
    response = requests.post(
        f"{API_URL}/api/process-local",
        json={"file_path": relative_path}
    )

    if response.status_code != 200:
        print(f"  ❌ Error: {response.json()}")
        return None

    result = response.json()
    job_id = result["job_id"]
    file_size = result.get("file_size_mb", 0)

    print(f"  ✓ Job created: {job_id}")
    print(f"  ✓ File size: {file_size} MB")

    # Step 2: Track progress
    print("\n  Progress:")
    last_progress = 0

    while True:
        status_response = requests.get(f"{API_URL}/api/status/{job_id}")
        if status_response.status_code != 200:
            print(f"  ❌ Error checking status")
            return None

        status = status_response.json()

        if status["status"] == "processing":
            progress = status.get("progress", 0)
            if progress > last_progress:
                current_frame = status.get("current_frame", "?")
                total_frames = status.get("total_frames", "?")

                # Create progress bar
                bar_width = 30
                filled = int((progress / 100) * bar_width)
                bar = "█" * filled + "░" * (bar_width - filled)

                print(f"  [{bar}] {progress}% - Frame {current_frame}/{total_frames}", end="\r")
                last_progress = progress

        elif status["status"] == "completed":
            print(f"\n  ✅ Processing completed!")

            # Get stats if available
            stats = status.get("statistics", {})
            if stats:
                print(f"  📊 Stats:")
                print(f"     - Total frames: {stats.get('total_frames', 'N/A')}")
                print(f"     - Accuracy: {stats.get('accuracy', 'N/A')}%")
                print(f"     - Processing time: {stats.get('processing_time', 'N/A')}s")

            return job_id

        elif status["status"] == "failed":
            print(f"\n  ❌ Processing failed: {status.get('error', 'Unknown error')}")
            return None

        time.sleep(1)

def download_results(job_id, video_name):
    """Download processed video and CSV data."""
    print(f"\n  Downloading results...")

    # Create clean filename (remove extension)
    base_name = Path(video_name).stem

    # Download processed video
    video_url = f"{API_URL}/api/download/{job_id}/video"
    video_response = requests.get(video_url)

    if video_response.status_code == 200:
        output_video = OUTPUT_DIR / f"{base_name}_processed.mp4"
        with open(output_video, 'wb') as f:
            f.write(video_response.content)
        print(f"  ✓ Video saved: {output_video}")
    else:
        print(f"  ❌ Failed to download video")

    # Download CSV data
    csv_url = f"{API_URL}/api/download/{job_id}/csv"
    csv_response = requests.get(csv_url)

    if csv_response.status_code == 200:
        output_csv = OUTPUT_DIR / f"{base_name}_pose_data.csv"
        with open(output_csv, 'wb') as f:
            f.write(csv_response.content)
        print(f"  ✓ CSV saved: {output_csv}")
    else:
        print(f"  ❌ Failed to download CSV")

def show_help():
    """Display help information."""
    help_text = """
🎬 BodyScript Batch Video Processor
=====================================

USAGE:
    python process_data_videos.py [OPTIONS]

DESCRIPTION:
    Process multiple videos through the BodyScript pose detection API.
    This script automatically processes all videos in the data/videos/ directory
    and saves the results (skeleton overlay videos and CSV pose data) to
    data/processed_videos/.

OPTIONS:
    --help, -h      Show this help message
    --manual        Show detailed manual with examples

WORKFLOW:
    1. Place video files in: data/videos/
    2. Start the API server: cd backend && python app.py
    3. Run this script: python process_data_videos.py
    4. Find results in: data/processed_videos/

SUPPORTED FORMATS:
    - .mp4 (recommended)
    - .mov
    - .avi

REQUIREMENTS:
    - API server must be running on http://localhost:8000
    - Videos should be under 30MB (API limit)
    - Videos should be under 10 seconds (for memory efficiency)
    """
    print(help_text)

def show_manual():
    """Display detailed manual."""
    manual_text = """
📚 DETAILED MANUAL
==================

OVERVIEW:
---------
This script is a batch processing client for the BodyScript pose detection API.
It processes multiple videos automatically without needing to use the web interface.

DIRECTORY STRUCTURE:
--------------------
    bodyscript/
    ├── data/
    │   ├── videos/           # Place input videos here
    │   └── processed_videos/ # Results will be saved here
    ├── backend/
    │   └── temp/            # Temporary processing directory
    └── process_data_videos.py

STEP-BY-STEP GUIDE:
-------------------
1. PREPARE VIDEOS:
   - Copy your videos to: data/videos/
   - Ensure videos are under 30MB and 10 seconds
   - Supported formats: .mp4, .mov, .avi

2. START THE API:
   cd backend
   python app.py
   # Should see: "INFO: Uvicorn running on http://127.0.0.1:8000"

3. RUN BATCH PROCESSING:
   python process_data_videos.py
   # You'll see a list of videos and be asked to confirm

4. MONITOR PROGRESS:
   The script will show:
   - Progress bars for each video
   - Frame-by-frame processing status
   - Success/failure indicators
   - Processing statistics

5. COLLECT RESULTS:
   For each video "example.mp4", you'll get:
   - data/processed_videos/example_processed.mp4 (with skeleton overlay)
   - data/processed_videos/example_pose_data.csv (landmark coordinates)

PROCESSING DETAILS:
-------------------
- Extracts ALL frames (interval=1) for smooth skeleton tracking
- Uses MediaPipe Pose for 33 body landmarks
- Generates colored skeleton overlays (green/pink/purple)
- Outputs CSV with frame_id, landmark_id, x, y, z, visibility

ERROR HANDLING:
---------------
- If a video fails, the script continues with the next one
- Failed videos are reported in the final summary
- Common issues:
  * API not running: Start with 'cd backend && python app.py'
  * Video too large: Keep under 30MB
  * Unsupported format: Convert to .mp4

EXAMPLES:
---------
# Process all videos in data/videos/
python process_data_videos.py

# Check if API is running
curl http://localhost:8000/health

# Process a single video manually (for testing)
1. Copy video to: backend/temp/data_videos/test.mp4
2. Use the API directly or web interface

TIPS:
-----
- For best results, use well-lit videos with clear human subjects
- Videos with single person work best
- Avoid videos with rapid camera movement
- Process in batches to manage memory usage

TROUBLESHOOTING:
----------------
Q: "Cannot connect to API"
A: Start the backend first: cd backend && python app.py

Q: "Processing failed: Memory error"
A: Video might be too long or high-resolution. Try shorter clips.

Q: "No skeleton overlay visible"
A: MediaPipe couldn't detect a person. Check video quality/lighting.

Q: "CSV is empty or has few frames"
A: Person might be partially out of frame or obscured.
    """
    print(manual_text)

def main():
    """Main function to process all videos."""
    print("🎬 BodyScript Video Processor")
    print("=" * 50)

    # Setup
    setup_directories()

    # Find all videos
    video_files = list(SOURCE_DIR.glob("*.mp4")) + \
                  list(SOURCE_DIR.glob("*.mov")) + \
                  list(SOURCE_DIR.glob("*.avi"))

    if not video_files:
        print(f"\n❌ No videos found in {SOURCE_DIR}")
        print("  Supported formats: .mp4, .mov, .avi")
        return

    print(f"\n📁 Found {len(video_files)} video(s) to process:")
    for video in video_files:
        print(f"  - {video.name} ({video.stat().st_size / 1024 / 1024:.1f} MB)")

    # Ask for confirmation
    confirm = input(f"\nProcess all {len(video_files)} videos? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    # Process each video
    successful = 0
    failed = 0

    for i, video_path in enumerate(video_files, 1):
        print(f"\n{'='*60}")
        print(f"VIDEO {i}/{len(video_files)}")
        print(f"{'='*60}")

        try:
            # Copy to temp
            relative_path = copy_video_to_temp(video_path)

            # Process
            job_id = process_video(relative_path, video_path.name)

            if job_id:
                # Download results
                download_results(job_id, video_path.name)
                successful += 1
            else:
                failed += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"🎬 PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"\n📁 Results saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    # Check for help flags first (before API check)
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--help', '-h']:
            show_help()
            sys.exit(0)
        elif arg == '--manual':
            show_manual()
            sys.exit(0)

    # Check if API is running
    try:
        health = requests.get(f"{API_URL}/health")
        if health.status_code == 200:
            print("✓ API is running\n")
            main()
        else:
            print("❌ API is not responding properly")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API at http://localhost:8000")
        print("  Make sure the backend is running:")
        print("  cd backend && python app.py")