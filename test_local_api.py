#!/usr/bin/env python3
"""
Test script for local API functionality
Run this to verify everything works before deploying
"""

import requests
import time
import sys

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Server healthy - Uptime: {data['uptime_seconds']:.1f}s")
            print(f"   Cold start: {data.get('cold_start', False)}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {e}")
        return False

def test_upload_small_video():
    """Test with a small video file"""
    print("\n2. Testing video upload...")

    # Create a tiny test video (1 second black video)
    import cv2
    import numpy as np
    import tempfile
    import os

    # Create temporary video file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        temp_video = tmp.name

    try:
        # Create 1-second test video (30 frames at 30fps)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video, fourcc, 30.0, (640, 480))

        # Write 30 black frames
        for i in range(30):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Add frame number
            cv2.putText(frame, f"Frame {i}", (50, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
            out.write(frame)

        out.release()
        print(f"   Created test video: {temp_video}")

        # Upload the video
        with open(temp_video, 'rb') as f:
            files = {'file': ('test.mp4', f, 'video/mp4')}
            response = requests.post(f"{API_URL}/api/upload", files=files)

        if response.status_code == 200:
            data = response.json()
            job_id = data.get('job_id')
            print(f"   ✅ Upload successful - Job ID: {job_id}")
            return job_id
        else:
            print(f"   ❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    finally:
        # Clean up temp file
        if os.path.exists(temp_video):
            os.remove(temp_video)
            print(f"   Cleaned up test video")

def test_status_polling(job_id):
    """Test status endpoint"""
    print(f"\n3. Testing status polling for job {job_id}...")

    max_attempts = 60  # Max 60 seconds
    for i in range(max_attempts):
        try:
            response = requests.get(f"{API_URL}/api/status/{job_id}")
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                progress = data.get('progress', 0)

                print(f"   Status: {status} - Progress: {progress}%", end='\r')

                if status == 'completed':
                    print(f"\n   ✅ Processing completed successfully!")
                    return True
                elif status == 'failed':
                    print(f"\n   ❌ Processing failed: {data.get('error')}")
                    return False

                time.sleep(1)
            else:
                print(f"\n   ❌ Status check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"\n   ❌ Error checking status: {e}")
            return False

    print(f"\n   ⚠️  Processing timeout after {max_attempts} seconds")
    return False

def test_download(job_id):
    """Test download endpoints"""
    print(f"\n4. Testing download for job {job_id}...")

    # Test video download
    try:
        response = requests.get(f"{API_URL}/api/download/{job_id}/video")
        if response.status_code == 200:
            print(f"   ✅ Video download works - Size: {len(response.content)} bytes")
        else:
            print(f"   ❌ Video download failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error downloading video: {e}")

    # Test CSV download
    try:
        response = requests.get(f"{API_URL}/api/download/{job_id}/csv")
        if response.status_code == 200:
            print(f"   ✅ CSV download works - Size: {len(response.content)} bytes")
        else:
            print(f"   ❌ CSV download failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error downloading CSV: {e}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing BodyScript API Locally")
    print("=" * 60)

    # Test 1: Health check
    if not test_health():
        print("\n❌ Server is not running! Start it with:")
        print("   cd backend && uvicorn app:app --reload")
        return

    # Test 2: Upload
    job_id = test_upload_small_video()
    if not job_id:
        print("\n❌ Upload failed. Check server logs.")
        return

    # Test 3: Status polling
    if not test_status_polling(job_id):
        print("\n❌ Processing failed. Check server logs.")
        return

    # Test 4: Download
    test_download(job_id)

    print("\n" + "=" * 60)
    print("✅ All tests completed! Check results above.")
    print("=" * 60)

if __name__ == "__main__":
    main()