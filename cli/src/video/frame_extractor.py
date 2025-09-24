#!/usr/bin/env python
"""
Video Frame Extraction Script
Extract frames from video files for analysis and validation.
"""

import cv2
import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple
import os

def extract_frames(video_path: str,
                  output_dir: str = "frames",
                  start_frame: int = 0,
                  end_frame: Optional[int] = None,
                  interval: int = 1,
                  format: str = "png",
                  quality: int = 95,
                  prefix: str = "frame") -> Tuple[int, str]:
    """
    Extract frames from video file.

    Args:
        video_path: Path to input video
        output_dir: Directory to save frames
        start_frame: Starting frame number (0-based)
        end_frame: Ending frame number (None = all frames)
        interval: Extract every Nth frame
        format: Output format ('png' or 'jpg')
        quality: JPEG quality (1-100, only for jpg)
        prefix: Filename prefix

    Returns:
        Tuple of (frames_extracted, output_directory)
    """

    # Validate input
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0

    print(f"📹 Video Info:")
    print(f"   Resolution: {width}x{height}")
    print(f"   Total frames: {total_frames}")
    print(f"   FPS: {fps:.2f}")
    print(f"   Duration: {duration:.2f} seconds")
    print()

    # Set end frame if not specified
    if end_frame is None:
        end_frame = total_frames
    else:
        end_frame = min(end_frame, total_frames)

    # Validate frame range
    if start_frame >= total_frames:
        raise ValueError(f"Start frame {start_frame} exceeds video length {total_frames}")

    if start_frame >= end_frame:
        raise ValueError(f"Start frame {start_frame} must be less than end frame {end_frame}")

    print(f"📸 Extraction Settings:")
    print(f"   Frame range: {start_frame} to {end_frame}")
    print(f"   Interval: every {interval} frame(s)")
    print(f"   Format: {format.upper()}")
    if format.lower() == 'jpg':
        print(f"   Quality: {quality}%")
    print(f"   Output: {output_path}/")
    print()

    # Calculate frames to extract
    frames_to_extract = list(range(start_frame, end_frame, interval))
    total_to_extract = len(frames_to_extract)

    print(f"🎬 Extracting {total_to_extract} frames...")

    extracted_count = 0
    current_frame = 0

    # Set to start frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame

    while current_frame < end_frame:
        ret, frame = cap.read()
        if not ret:
            break

        # Check if this frame should be extracted
        if current_frame in frames_to_extract:
            # Generate filename
            frame_number = current_frame  # Use 0-based numbering to match video frame indices
            if format.lower() == 'png':
                filename = f"{prefix}_{frame_number:06d}.png"
                filepath = output_path / filename
                cv2.imwrite(str(filepath), frame)
            elif format.lower() in ['jpg', 'jpeg']:
                filename = f"{prefix}_{frame_number:06d}.jpg"
                filepath = output_path / filename
                cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                raise ValueError(f"Unsupported format: {format}")

            extracted_count += 1

            # Progress indicator
            if extracted_count % 50 == 0 or extracted_count == total_to_extract:
                progress = (extracted_count / total_to_extract) * 100
                print(f"   Progress: {progress:.1f}% ({extracted_count}/{total_to_extract})")

        current_frame += 1

    cap.release()

    print(f"\n✅ Extraction complete!")
    print(f"   Extracted: {extracted_count} frames")
    print(f"   Saved to: {output_path}")

    return extracted_count, str(output_path)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract frames from video files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all frames as PNG
  python extract_frames.py video.mp4

  # Extract frames 100-200 as JPEG
  python extract_frames.py video.mp4 --start 100 --end 200 --format jpg

  # Extract every 10th frame
  python extract_frames.py video.mp4 --interval 10

  # Custom output directory and prefix
  python extract_frames.py video.mp4 --output dance_frames --prefix dance

  # High quality JPEG with specific range
  python extract_frames.py video.mp4 --start 50 --end 150 --format jpg --quality 100
        """
    )

    parser.add_argument(
        'video',
        help='Path to input video file'
    )

    parser.add_argument(
        '--output', '-o',
        default='frames',
        help='Output directory for frames (default: frames)'
    )

    parser.add_argument(
        '--start', '-s',
        type=int,
        default=0,
        help='Starting frame number (0-based, default: 0)'
    )

    parser.add_argument(
        '--end', '-e',
        type=int,
        help='Ending frame number (default: last frame)'
    )

    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=1,
        help='Extract every Nth frame (default: 1)'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['png', 'jpg', 'jpeg'],
        default='png',
        help='Output image format (default: png)'
    )

    parser.add_argument(
        '--quality', '-q',
        type=int,
        default=95,
        help='JPEG quality 1-100 (default: 95, only for jpg format)'
    )

    parser.add_argument(
        '--prefix', '-p',
        default='frame',
        help='Filename prefix (default: frame)'
    )

    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean output directory before extraction'
    )

    args = parser.parse_args()

    # Validate quality parameter
    if args.quality < 1 or args.quality > 100:
        print("❌ Error: Quality must be between 1 and 100")
        sys.exit(1)

    # Clean output directory if requested
    if args.clean:
        output_path = Path(args.output)
        if output_path.exists():
            import shutil
            shutil.rmtree(output_path)
            print(f"🧹 Cleaned output directory: {output_path}")

    print("="*60)
    print("🎬 VIDEO FRAME EXTRACTOR")
    print("="*60)
    print(f"Input: {args.video}")
    print(f"Output: {args.output}/")
    print("="*60)

    try:
        extracted_count, output_dir = extract_frames(
            video_path=args.video,
            output_dir=args.output,
            start_frame=args.start,
            end_frame=args.end,
            interval=args.interval,
            format=args.format,
            quality=args.quality,
            prefix=args.prefix
        )

        # Show some example filenames
        print(f"\n📁 Sample files created:")
        output_path = Path(output_dir)
        files = sorted(list(output_path.glob(f"{args.prefix}_*")))
        for i, file in enumerate(files[:3]):
            print(f"   {file.name}")
        if len(files) > 3:
            print(f"   ... and {len(files) - 3} more")

        print(f"\n🎯 Usage tips:")
        print(f"   • Use these frames for pose validation")
        print(f"   • Check specific frames: ls {output_dir}/{args.prefix}_*.{args.format}")
        print(f"   • Total size: ~{extracted_count * 0.5:.1f}MB (estimated)")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()