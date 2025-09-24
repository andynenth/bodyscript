#!/usr/bin/env python3
"""
Simple utility script to extract frames from a video file.
Use this to validate video processing and check for skeleton overlays.

Usage:
    python extract_frames.py <video_file> [output_dir] [--interval N]

Examples:
    python extract_frames.py video.mp4
    python extract_frames.py output.mp4 frames/
    python extract_frames.py output.mp4 frames/ --interval 5
"""

import sys
import os
from pathlib import Path

def extract_frames_simple(video_path, output_dir="frames", interval=1):
    """
    Extract frames from a video file using OpenCV.

    Args:
        video_path: Path to input video
        output_dir: Directory to save frames (default: "frames")
        interval: Extract every Nth frame (default: 1 = all frames)
    """
    try:
        import cv2
    except ImportError:
        print("Error: OpenCV not installed. Run: pip install opencv-python")
        return False

    # Check if video exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return False

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return False

    # Get video info
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"\n📹 Video Info:")
    print(f"  File: {video_path}")
    print(f"  Resolution: {width}x{height}")
    print(f"  Total frames: {total_frames}")
    print(f"  FPS: {fps:.2f}")
    print(f"  Duration: {total_frames/fps if fps > 0 else 0:.2f} seconds")
    print(f"\n📸 Extracting frames:")
    print(f"  Output: {output_path}/")
    print(f"  Interval: every {interval} frame(s)")
    print(f"  Format: JPEG")

    # Extract frames
    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Save frame if it matches interval
        if frame_count % interval == 0:
            frame_filename = output_path / f"frame_{frame_count:06d}.jpg"
            cv2.imwrite(str(frame_filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            saved_count += 1

            # Progress indicator
            if saved_count % 10 == 0:
                print(f"  Extracted {saved_count} frames...")

        frame_count += 1

    cap.release()

    print(f"\n✅ Complete!")
    print(f"  Extracted: {saved_count} frames")
    print(f"  Location: {output_path}/")
    print(f"\n💡 Tips:")
    print(f"  • View frames: open {output_path}/")
    print(f"  • Check for skeleton: Look for colored lines on the person")
    print(f"  • If no skeleton visible, the overlay may have failed")

    return True

def main():
    """Main entry point for command line usage."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "frames"

    # Parse interval if provided
    interval = 1
    if "--interval" in sys.argv:
        try:
            idx = sys.argv.index("--interval")
            interval = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            print("Error: Invalid interval value")
            sys.exit(1)

    # Extract frames
    success = extract_frames_simple(video_path, output_dir, interval)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()