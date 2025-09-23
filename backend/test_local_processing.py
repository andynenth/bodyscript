#!/usr/bin/env python3
"""
Example script to demonstrate processing a local video through the API.

This script shows how to:
1. Generate or place a video in backend/temp
2. Process it through the same pipeline as uploaded videos
3. Track progress and download results
"""

import requests
import time
import json
from pathlib import Path
import shutil

# API Configuration
API_URL = "http://localhost:8000"  # Change this if running on a different port

def process_local_video(video_path: str):
    """
    Process a video that already exists in backend/temp directory.

    Args:
        video_path: Path to video relative to backend/temp (e.g., "test_videos/sample.mp4")
    """
    print(f"Processing local video: {video_path}")

    # Step 1: Request processing
    response = requests.post(
        f"{API_URL}/api/process-local",
        json={"file_path": video_path}
    )

    if response.status_code != 200:
        print(f"Error: {response.json()}")
        return None

    result = response.json()
    job_id = result["job_id"]
    print(f"Job created: {job_id}")
    print(f"Initial status: {result['status']}")
    print(f"File size: {result['file_size_mb']} MB")

    # Step 2: Poll for status
    while True:
        status_response = requests.get(f"{API_URL}/api/status/{job_id}")
        if status_response.status_code != 200:
            print(f"Error checking status: {status_response.json()}")
            break

        status = status_response.json()

        if status["status"] == "processing":
            progress = status.get("progress", 0)
            current_frame = status.get("current_frame", "?")
            total_frames = status.get("total_frames", "?")
            print(f"Processing... {progress}% - Frame {current_frame}/{total_frames}")

        elif status["status"] == "completed":
            print("Processing completed!")
            print(f"Total frames: {status.get('statistics', {}).get('total_frames', 'N/A')}")
            print(f"Accuracy: {status.get('statistics', {}).get('accuracy', 'N/A')}%")
            print(f"Processing time: {status.get('statistics', {}).get('processing_time', 'N/A')} seconds")

            # Step 3: Download results
            print("\nResults available at:")
            print(f"  Video: {API_URL}/api/download/{job_id}/video")
            print(f"  CSV: {API_URL}/api/download/{job_id}/csv")

            return job_id

        elif status["status"] == "failed":
            print(f"Processing failed: {status.get('error', 'Unknown error')}")
            break

        time.sleep(1)

    return None


def copy_sample_video():
    """
    Copy a sample video to backend/temp for testing.
    Returns the path relative to backend/temp.
    """
    # Look for any existing video in the temp directory
    temp_dir = Path("temp")

    # Create a test videos directory
    test_dir = temp_dir / "test_videos"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Look for an existing video to use as sample
    existing_videos = list(temp_dir.glob("**/input*.mp4"))
    if existing_videos:
        # Copy an existing video as our test video
        sample_path = test_dir / "sample.mp4"
        shutil.copy2(existing_videos[0], sample_path)
        print(f"Copied existing video to: {sample_path}")
        return "test_videos/sample.mp4"
    else:
        print("No existing videos found in temp directory.")
        print("Please place a video at: backend/temp/test_videos/sample.mp4")
        return None


def main():
    """Main function to demonstrate local video processing."""
    print("=== BodyScript Local Video Processing Demo ===\n")

    # Option 1: Use an existing video in temp
    # Uncomment this if you have a video ready:
    # video_path = "your_video.mp4"  # Path relative to backend/temp

    # Option 2: Copy a sample video (if available)
    video_path = copy_sample_video()

    if not video_path:
        print("\nTo test local processing:")
        print("1. Place a video file in backend/temp/")
        print("2. Update the video_path variable in this script")
        print("3. Run this script again")
        return

    # Process the video
    job_id = process_local_video(video_path)

    if job_id:
        print(f"\n✅ Success! Job {job_id} completed.")
        print("You can now use the same job_id to access results through the API.")

        # Optional: Download the results
        download = input("\nDownload processed video? (y/n): ")
        if download.lower() == 'y':
            video_response = requests.get(f"{API_URL}/api/download/{job_id}/video")
            if video_response.status_code == 200:
                output_path = f"temp/processed_{job_id}.mp4"
                with open(output_path, 'wb') as f:
                    f.write(video_response.content)
                print(f"Video saved to: {output_path}")

            csv_response = requests.get(f"{API_URL}/api/download/{job_id}/csv")
            if csv_response.status_code == 200:
                csv_path = f"temp/pose_data_{job_id}.csv"
                with open(csv_path, 'wb') as f:
                    f.write(csv_response.content)
                print(f"CSV saved to: {csv_path}")


if __name__ == "__main__":
    main()