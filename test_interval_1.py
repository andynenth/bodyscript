#!/usr/bin/env python3
"""Test script to verify interval=1 processing"""

import sys
import os
sys.path.insert(0, 'backend')
sys.path.insert(0, 'cli')

# Test frame extraction with interval=1
from cli.src.video.frame_extractor import extract_frames

print("Testing frame extraction with interval=1...")
video_path = "backend/temp/a1daaffd-c356-4bbd-94d0-c2621ebf8ff9/trimmed.mp4"

if not os.path.exists(video_path):
    print(f"Video not found: {video_path}")
    sys.exit(1)

# Extract frames with interval=1
frames_extracted, _ = extract_frames(
    video_path,
    output_dir="data/test_interval_1_frames",
    interval=1,  # Extract ALL frames
    format='jpg',
    quality=85
)

print(f"\nExtracted {frames_extracted} frames with interval=1")

# Now test MediaPipe processing
from cli.src.processors.mediapipe_fast_smart import MediaPipeFastSmart

print("\nTesting MediaPipe processing...")
processor = MediaPipeFastSmart(mode='fast')

results_df = processor.process_video_fast(
    "data/test_interval_1_frames",
    "data/test_interval_1_pose.csv",
    max_frames=20  # Just test first 20 frames
)

processor.close()

print(f"Processed {len(results_df) // 33} frames")
print(f"Unique frame IDs in CSV: {sorted(results_df['frame_id'].unique())[:10]}...")

# Test skeleton overlay
print("\nTesting skeleton overlay...")
os.system(f"python cli/src/video/skeleton_overlay.py --video {video_path} --csv data/test_interval_1_pose.csv --output data/test_interval_1_overlay.mp4 --no-info")

print("\n✅ Test complete! Check data/test_interval_1_overlay.mp4")