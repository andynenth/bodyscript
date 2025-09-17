"""Video processing module for pose estimation.

Handles video loading, frame extraction, and metadata collection.
"""

import cv2
import numpy as np
from typing import Iterator, Optional, Dict, Tuple
import os


class VideoLoader:
    """Handle video input/output operations"""
    
    def __init__(self, video_path: str):
        """Initialize video loader with path validation.
        
        Args:
            video_path: Path to video file
        
        Raises:
            ValueError: If video file doesn't exist or is invalid
        """
        self.video_path = os.path.abspath(video_path)
        self.cap = None
        self.metadata = {}
        self.is_loaded = False
        
        # Validate file exists
        if not os.path.exists(self.video_path):
            raise ValueError(f"Video file not found: {self.video_path}")
            
        # Validate file format
        self._validate_format()
        
    def _validate_format(self):
        """Validate video file format."""
        valid_formats = ['.mp4', '.avi', '.mov', '.wmv']
        ext = os.path.splitext(self.video_path)[1].lower()
        
        if ext not in valid_formats:
            raise ValueError(f"Unsupported video format: {ext}. Supported formats: {valid_formats}")
            
        # Check file size (500MB limit for MVP)
        file_size_mb = os.path.getsize(self.video_path) / (1024 * 1024)
        if file_size_mb > 500:
            raise ValueError(f"Video file too large: {file_size_mb:.1f}MB (max 500MB)")
            
    def load_video(self) -> bool:
        """Load video and extract metadata.
        
        Returns:
            bool: True if successfully loaded, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.video_path)
            
            if not self.cap.isOpened():
                return False
                
            # Extract metadata
            self.metadata = {
                'fps': self.cap.get(cv2.CAP_PROP_FPS),
                'total_frames': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration': self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.cap.get(cv2.CAP_PROP_FPS),
                'fourcc': int(self.cap.get(cv2.CAP_PROP_FOURCC))
            }
            
            # Validate resolution
            if self.metadata['width'] < 480 or self.metadata['height'] < 480:
                raise ValueError(f"Resolution too low: {self.metadata['width']}x{self.metadata['height']} (minimum 480p)")
                
            if self.metadata['duration'] > 600:  # 10 minutes
                raise ValueError(f"Video too long: {self.metadata['duration']:.1f}s (max 600s)")
                
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading video: {e}")
            return False
            
    def extract_frames(self) -> Iterator[Tuple[int, np.ndarray]]:
        """Yield frames one by one with frame index.
        
        Yields:
            Tuple[int, np.ndarray]: Frame index and frame array
        """
        if not self.is_loaded:
            if not self.load_video():
                raise RuntimeError("Failed to load video")
                
        # Reset to beginning
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_idx = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            yield frame_idx, frame
            frame_idx += 1
            
    def extract_frames_batch(self, batch_size: int = 30) -> Iterator[Tuple[int, list]]:
        """Extract frames in batches for efficiency.
        
        Args:
            batch_size: Number of frames per batch
            
        Yields:
            Tuple[int, list]: Starting frame index and list of frames
        """
        batch = []
        start_idx = None
        
        for frame_idx, frame in self.extract_frames():
            if start_idx is None:
                start_idx = frame_idx
                
            batch.append(frame)
            
            if len(batch) >= batch_size:
                yield start_idx, batch
                batch = []
                start_idx = None
                
        # Yield remaining frames
        if batch and start_idx is not None:
            yield start_idx, batch
            
    def get_frame(self, frame_number: int) -> Optional[np.ndarray]:
        """Get a specific frame by number.
        
        Args:
            frame_number: Frame index to retrieve
            
        Returns:
            np.ndarray: Frame array or None if failed
        """
        if not self.is_loaded:
            if not self.load_video():
                return None
                
        if frame_number < 0 or frame_number >= self.metadata['total_frames']:
            return None
            
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        
        return frame if ret else None
        
    def get_metadata(self) -> Dict:
        """Return video metadata."""
        return self.metadata.copy()
        
    def get_video_info(self) -> str:
        """Get formatted video information string."""
        if not self.metadata:
            return "Video not loaded"
            
        return (
            f"Video: {os.path.basename(self.video_path)}\n"
            f"Resolution: {self.metadata['width']}x{self.metadata['height']}\n"
            f"FPS: {self.metadata['fps']:.1f}\n"
            f"Duration: {self.metadata['duration']:.1f}s\n"
            f"Total frames: {self.metadata['total_frames']}"
        )
        
    def release(self):
        """Release video capture resources."""
        if self.cap:
            self.cap.release()
            self.cap = None
            self.is_loaded = False
            
    def __del__(self):
        """Cleanup on deletion."""
        self.release()
        
    def __enter__(self):
        """Context manager entry."""
        if not self.is_loaded:
            self.load_video()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()