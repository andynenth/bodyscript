"""
Video processing utilities for thumbnail and preview generation
"""

import subprocess
import cv2
import json
from pathlib import Path
from typing import Tuple, Dict, Optional


def generate_thumbnail(video_path: str, output_path: str,
                      size: Tuple[int, int] = (404, 720),
                      frame_number: int = 0) -> bool:
    """
    Generate thumbnail from video frame

    Args:
        video_path: Path to input video
        output_path: Path for output thumbnail
        size: Target size (width, height)
        frame_number: Which frame to use (0 = first frame)

    Returns:
        True if successful
    """
    try:
        cap = cv2.VideoCapture(video_path)

        # Seek to desired frame
        if frame_number > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        ret, frame = cap.read()
        if ret:
            # Calculate aspect ratio preserving resize
            h, w = frame.shape[:2]
            target_w, target_h = size

            # Calculate scale to fit within target size
            scale = min(target_w / w, target_h / h)
            new_w = int(w * scale)
            new_h = int(h * scale)

            # Resize frame
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Create canvas of target size (black background)
            canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)

            # Center the resized image on canvas
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

            # Save thumbnail
            cv2.imwrite(output_path, canvas, [cv2.IMWRITE_JPEG_QUALITY, 85])

            cap.release()
            print(f"Thumbnail generated: {output_path}")
            return True

        cap.release()
        return False

    except Exception as e:
        print(f"Thumbnail generation failed: {e}")
        return False


def generate_preview(video_path: str, output_path: str,
                    duration: int = 3,
                    quality: str = "low",
                    size: Tuple[int, int] = (404, 720)) -> bool:
    """
    Generate preview video clip

    Args:
        video_path: Path to input video
        output_path: Path for output preview
        duration: Preview duration in seconds
        quality: Quality level ('low', 'medium', 'high')
        size: Target size (width, height) - same as thumbnail

    Returns:
        True if successful
    """
    try:
        # Quality presets
        quality_settings = {
            'low': {'crf': '32', 'preset': 'ultrafast'},
            'medium': {'crf': '28', 'preset': 'fast'},
            'high': {'crf': '23', 'preset': 'medium'}
        }

        settings = quality_settings.get(quality, quality_settings['low'])
        target_w, target_h = size

        # Build ffmpeg command with proper scaling to match thumbnail
        # Scale to exact size (matching thumbnail generation behavior)
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-t", str(duration),  # Duration
            "-vf", f"scale={target_w}:{target_h}",  # Scale to exact size
            "-c:v", "libx264",  # H.264 codec
            "-preset", settings['preset'],
            "-crf", settings['crf'],  # Quality
            "-an",  # No audio
            "-movflags", "+faststart",  # Web optimization
            "-y",  # Overwrite output
            output_path
        ]

        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"Preview generated: {output_path}")
            return True
        else:
            print(f"ffmpeg error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("Preview generation timed out")
        return False
    except Exception as e:
        print(f"Preview generation failed: {e}")
        return False


def get_video_metadata(video_path: str) -> Dict:
    """
    Extract comprehensive video metadata

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video metadata
    """
    metadata = {}

    try:
        # Use OpenCV for basic metadata
        cap = cv2.VideoCapture(video_path)

        metadata['fps'] = cap.get(cv2.CAP_PROP_FPS)
        metadata['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        metadata['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        metadata['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        metadata['duration'] = metadata['frame_count'] / metadata['fps'] if metadata['fps'] > 0 else 0

        # Get codec info
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        metadata['codec'] = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

        cap.release()

        # Use ffprobe for detailed metadata
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                ffprobe_data = json.loads(result.stdout)

                # Extract additional info
                if 'format' in ffprobe_data:
                    metadata['size'] = int(ffprobe_data['format'].get('size', 0))
                    metadata['bit_rate'] = int(ffprobe_data['format'].get('bit_rate', 0))

                # Get video stream info
                for stream in ffprobe_data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        metadata['pixel_format'] = stream.get('pix_fmt', 'unknown')
                        metadata['color_space'] = stream.get('color_space', 'unknown')
                        break

        except:
            # ffprobe not available or failed
            pass

    except Exception as e:
        print(f"Failed to extract metadata: {e}")

    return metadata


def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is available in the system"""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False


def optimize_for_web(input_path: str, output_path: str) -> bool:
    """
    Optimize video for web streaming

    Args:
        input_path: Path to input video
        output_path: Path for optimized output

    Returns:
        True if successful
    """
    try:
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",  # Enable progressive download
            "-y",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0

    except Exception as e:
        print(f"Web optimization failed: {e}")
        return False


# Import numpy for thumbnail generation
import numpy as np