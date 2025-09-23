#!/usr/bin/env python3
"""
Process videos from data/videos directory using the local API.
"""

import os
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