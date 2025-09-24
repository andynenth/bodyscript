#!/usr/bin/env python3
"""
Web processing wrapper for existing MediaPipe processors.
Adapts the existing code for web service use.
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time

# Add CLI modules to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../cli')))

from src.processors.mediapipe_fast_smart import MediaPipeFastSmart
from src.video.frame_extractor import extract_frames

# Batch processing configuration
FRAME_BATCH_SIZE = 30  # Process frames in batches to reduce memory
from src.video.skeleton_overlay import load_pose_data, draw_skeleton_on_frame
import cv2
import pandas as pd
from datetime import datetime

# Import storage and video utilities
from storage_r2 import r2_storage
from video_utils import generate_thumbnail, generate_preview, get_video_metadata


class WebVideoProcessor:
    """Processes videos for web service using existing processors."""

    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def trim_video(self, input_path: str, output_path: str, max_seconds: int = 15) -> Dict[str, Any]:
        """Trim video to maximum duration using ffmpeg."""
        try:
            # Get video duration first
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", input_path
            ], capture_output=True, text=True)

            video_info = json.loads(result.stdout)
            duration = float(video_info['format']['duration'])

            # Trim if needed
            actual_duration = min(duration, max_seconds)

            subprocess.run([
                "ffmpeg", "-i", input_path,
                "-t", str(max_seconds),
                "-c", "copy",  # Fast copy without re-encoding
                "-y",  # Overwrite output
                output_path
            ], check=True, capture_output=True)

            return {
                "original_duration": duration,
                "trimmed_duration": actual_duration,
                "was_trimmed": duration > max_seconds
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to trim video: {e.stderr}")

    def extract_frames_batch(self, video_path: str, output_dir: str,
                            start_frame: int, end_frame: int, interval: int = 3) -> int:
        """
        Extract a batch of frames from video.
        Returns number of frames extracted.
        """
        from src.video.frame_extractor import extract_frames

        frames_extracted, _ = extract_frames(
            video_path,
            output_dir=output_dir,
            start_frame=start_frame,
            end_frame=end_frame,
            interval=interval,
            format='jpg',  # Use JPEG for less memory
            quality=85
        )
        return frames_extracted

    def reduce_resolution_if_needed(self, video_path: str, max_width: int = 720) -> bool:
        """Reduce video resolution if it's too large."""
        cap = None
        try:
            # Get video dimensions
            cap = cv2.VideoCapture(video_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if width > max_width:
                # Calculate new dimensions maintaining aspect ratio
                scale = max_width / width
                new_width = max_width
                new_height = int(height * scale)

                # Make sure height is even (required for some codecs)
                if new_height % 2 != 0:
                    new_height += 1

                temp_output = video_path + ".resized.mp4"

                subprocess.run([
                    "ffmpeg", "-i", video_path,
                    "-vf", f"scale={new_width}:{new_height}",
                    "-c:a", "copy",  # Copy audio without re-encoding
                    "-y", temp_output
                ], check=True, capture_output=True)

                # Replace original with resized
                shutil.move(temp_output, video_path)
                return True

            return False

        except Exception as e:
            print(f"Warning: Could not reduce resolution: {e}")
            return False
        finally:
            # Always release the capture
            if cap and cap.isOpened():
                cap.release()

    def process_video(self,
                     input_video_path: str,
                     job_id: str,
                     mode: str = 'fast',
                     progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Process video through complete pipeline.

        Args:
            input_video_path: Path to uploaded video
            job_id: Unique job identifier
            mode: Processing mode ('ultra_fast', 'fast', 'smart', 'quality')
            progress_callback: Function to call with progress updates

        Returns:
            Dictionary with output paths and statistics
        """
        start_time = time.time()
        job_dir = self.temp_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Trim video to 15 seconds
            if progress_callback:
                progress_callback(5, "Trimming video to 15 seconds...")

            trimmed_video = str(job_dir / "trimmed.mp4")
            trim_info = self.trim_video(input_video_path, trimmed_video)

            # Delete original to save memory
            if os.path.exists(input_video_path) and input_video_path != trimmed_video:
                os.remove(input_video_path)

            if progress_callback:
                progress_callback(10, "Video trimmed successfully")

            # Step 2: Reduce resolution if needed
            if progress_callback:
                progress_callback(12, "Checking video resolution...")

            was_resized = self.reduce_resolution_if_needed(trimmed_video)

            # Force garbage collection after video operations
            import gc
            gc.collect()

            if progress_callback:
                progress_callback(15, "Starting frame extraction...")

            # Step 3: Extract frames
            if progress_callback:
                progress_callback(18, "Extracting frames...")

            frames_dir = str(job_dir / "frames")
            frames_extracted, _ = extract_frames(
                trimmed_video,
                output_dir=frames_dir,
                interval=1,  # Process ALL frames for complete pose data
                format='jpg',  # Use JPEG to save memory
                quality=85  # Good quality/size balance
            )

            # Step 4: Process with MediaPipe
            if progress_callback:
                progress_callback(25, f"Starting MediaPipe processing for {frames_extracted} frames...")

            processor = MediaPipeFastSmart(mode=mode)
            csv_path = str(job_dir / "pose_data.csv")

            # Process frames with progress updates
            # Create a wrapper to send progress during processing
            def mediapipe_progress(current_frame, total_frames):
                if progress_callback:
                    # Scale progress from 25% to 75%
                    progress = 25 + int((current_frame / total_frames) * 50)
                    progress_callback(progress, f"Processing frame {current_frame}/{total_frames}...")

            results_df = processor.process_video_fast(
                frames_dir,
                csv_path,
                max_frames=None,  # Process all frames
                progress_callback=mediapipe_progress
            )

            # Clean up MediaPipe resources to prevent memory leak
            processor.close()

            # Calculate statistics
            avg_quality = results_df['visibility'].mean() if not results_df.empty else 0
            detection_rate = len(results_df) / (frames_extracted * 33) if frames_extracted > 0 else 0

            # Step 5: Generate output video with skeleton overlay
            if progress_callback:
                progress_callback(76, "Creating skeleton overlay video...")

            output_video = str(job_dir / "output.mp4")
            self.create_skeleton_video(trimmed_video, csv_path, output_video)

            # Step 6: Generate thumbnail and preview
            if progress_callback:
                progress_callback(85, "Generating thumbnail and preview...")

            thumbnail_path = str(job_dir / "thumbnail.jpg")
            preview_path = str(job_dir / "preview.mp4")

            generate_thumbnail(output_video, thumbnail_path, size=(405, 720))
            generate_preview(output_video, preview_path, duration=3, quality='low')

            # Step 7: Upload to R2 if configured
            urls = {}
            if r2_storage.is_configured():
                if progress_callback:
                    progress_callback(90, "Uploading to cloud storage...")

                # Upload all generated files
                urls = {
                    'thumbnail': r2_storage.upload_file(thumbnail_path, f"{job_id}/thumbnail.jpg"),
                    'preview': r2_storage.upload_file(preview_path, f"{job_id}/preview.mp4"),
                    'full': r2_storage.upload_file(output_video, f"{job_id}/full.mp4"),
                    'csv': r2_storage.upload_file(csv_path, f"{job_id}/pose_data.csv")
                }

                # Create and upload metadata
                metadata = {
                    'job_id': job_id,
                    'processed_at': datetime.now().isoformat(),
                    'statistics': {
                        'frames_processed': frames_extracted,
                        'average_quality': float(avg_quality),
                        'detection_rate': float(detection_rate),
                        'processing_time': time.time() - start_time,
                        'processing_mode': mode,
                        'video_was_trimmed': trim_info['was_trimmed'],
                        'video_was_resized': was_resized,
                        'original_duration': trim_info['original_duration'],
                        'processed_duration': trim_info['trimmed_duration']
                    },
                    'urls': urls,
                    'video_info': get_video_metadata(output_video)
                }

                metadata_path = str(job_dir / "metadata.json")
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

                r2_storage.upload_file(metadata_path, f"{job_id}/metadata.json")

            # Step 8: Clean up frames to save space
            shutil.rmtree(frames_dir, ignore_errors=True)

            # Force garbage collection after major operations
            import gc
            gc.collect()

            if progress_callback:
                progress_callback(100, "Processing complete!")

            processing_time = time.time() - start_time

            return {
                'success': True,
                'job_id': job_id,
                'output_video': output_video,
                'pose_data_csv': csv_path,
                'urls': urls,  # Include R2 URLs
                'statistics': {
                    'frames_processed': frames_extracted,
                    'average_quality': float(avg_quality),
                    'detection_rate': float(detection_rate),
                    'processing_time': processing_time,
                    'processing_mode': mode,
                    'video_was_trimmed': trim_info['was_trimmed'],
                    'video_was_resized': was_resized,
                    'original_duration': trim_info['original_duration'],
                    'processed_duration': trim_info['trimmed_duration']
                }
            }

        except Exception as e:
            # Clean up on error
            if job_dir.exists():
                shutil.rmtree(job_dir, ignore_errors=True)

            return {
                'success': False,
                'job_id': job_id,
                'error': str(e),
                'error_type': type(e).__name__
            }

    def create_skeleton_video(self, video_path: str, csv_path: str, output_path: str):
        """Create video with skeleton overlay using the same script as pipeline."""
        # Get absolute paths
        project_root = Path(__file__).parent.parent
        skeleton_script = project_root / "cli" / "src" / "video" / "skeleton_overlay.py"

        # Convert paths to absolute if they're relative
        video_abs = Path(video_path).absolute()
        csv_abs = Path(csv_path).absolute()
        output_abs = Path(output_path).absolute()

        # Use the same skeleton_overlay.py script for consistency
        result = subprocess.run([
            sys.executable,
            str(skeleton_script),
            "--video", str(video_abs),
            "--csv", str(csv_abs),
            "--output", str(output_abs),
            "--no-info"  # Same as pipeline script
        ], capture_output=True, text=True, cwd=str(project_root))

        if result.returncode != 0:
            print(f"Skeleton overlay stderr: {result.stderr}")
            print(f"Skeleton overlay stdout: {result.stdout}")
            raise RuntimeError(f"Skeleton overlay failed: {result.stderr}")

    def cleanup_processor(self):
        """Force cleanup of any processor resources and memory"""
        import gc
        # Force garbage collection to release memory
        gc.collect()

    def cleanup_job(self, job_id: str):
        """Clean up all files for a job."""
        job_dir = self.temp_dir / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
        # Also cleanup processor resources
        self.cleanup_processor()


# Quick test if run directly
if __name__ == "__main__":
    processor = WebVideoProcessor()

    # Test with a sample video
    test_video = "data/videos/dance.mp4"
    if os.path.exists(test_video):
        print(f"Testing with {test_video}")
        result = processor.process_video(
            test_video,
            "test_job_123",
            mode='fast',
            progress_callback=lambda p, m: print(f"[{p}%] {m}")
        )
        print(f"Result: {result}")