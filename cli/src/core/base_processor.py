"""
Base Video Processor - Abstract base class for all video processors
Provides common interface and eliminates duplication across processors
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import pandas as pd
import numpy as np
import cv2
from datetime import datetime
import json


class ProcessingResult:
    """Standard result object for video processing operations"""

    def __init__(self, frame_idx: int, timestamp: float):
        self.frame_idx = frame_idx
        self.timestamp = timestamp
        self.detected = False
        self.landmarks = None
        self.confidence = 0.0
        self.metadata = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary format"""
        return {
            'frame_idx': self.frame_idx,
            'timestamp': self.timestamp,
            'detected': self.detected,
            'landmarks': self.landmarks,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


class VideoMetadata:
    """Standard video metadata container"""

    def __init__(self, video_path: str = ""):
        self.video_path = video_path
        self.filename = Path(video_path).name if video_path else ""
        self.width = 0
        self.height = 0
        self.fps = 0.0
        self.total_frames = 0
        self.duration = 0.0
        self.format = ""
        self.size_mb = 0.0
        self.created_at = datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary format"""
        return {
            'video_path': self.video_path,
            'filename': self.filename,
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'total_frames': self.total_frames,
            'duration': self.duration,
            'format': self.format,
            'size_mb': self.size_mb,
            'created_at': self.created_at.isoformat()
        }


class ProcessingStatistics:
    """Standard statistics container for processing results"""

    def __init__(self):
        self.total_frames = 0
        self.detected_frames = 0
        self.detection_rate = 0.0
        self.average_confidence = 0.0
        self.processing_fps = 0.0
        self.processing_time = 0.0
        self.data_points = 0
        self.quality_metrics = {}
        self.errors = []

    def calculate_derived_metrics(self):
        """Calculate derived metrics"""
        if self.total_frames > 0:
            self.detection_rate = self.detected_frames / self.total_frames
        if self.processing_time > 0:
            self.processing_fps = self.total_frames / self.processing_time

    def to_dict(self) -> Dict:
        """Convert to dictionary format"""
        return {
            'total_frames': self.total_frames,
            'detected_frames': self.detected_frames,
            'detection_rate': self.detection_rate,
            'average_confidence': self.average_confidence,
            'processing_fps': self.processing_fps,
            'processing_time': self.processing_time,
            'data_points': self.data_points,
            'quality_metrics': self.quality_metrics,
            'error_count': len(self.errors)
        }


class BaseVideoProcessor(ABC):
    """
    Abstract base class for all video processors.
    Eliminates duplication and provides common interface.
    """

    def __init__(self,
                 output_dir: str = "output",
                 detection_confidence: float = 0.5,
                 tracking_confidence: float = 0.5):
        """Initialize base processor"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        # Results storage
        self.results_data: List[ProcessingResult] = []
        self.video_metadata = VideoMetadata()
        self.statistics = ProcessingStatistics()

        # Processing state
        self._processing_start_time = None

    @abstractmethod
    def _initialize_detector(self) -> Any:
        """Initialize the specific detector (MediaPipe, etc.)"""
        pass

    @abstractmethod
    def _detect_frame(self, frame: np.ndarray, frame_idx: int) -> ProcessingResult:
        """Detect poses in a single frame"""
        pass

    @abstractmethod
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame before detection (optional override)"""
        return frame

    def _load_video_metadata(self, video_path: str) -> VideoMetadata:
        """Load video metadata using OpenCV"""
        metadata = VideoMetadata(video_path)

        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                metadata.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                metadata.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                metadata.fps = cap.get(cv2.CAP_PROP_FPS)
                metadata.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                metadata.duration = metadata.total_frames / metadata.fps if metadata.fps > 0 else 0

                # Get file size
                file_size = Path(video_path).stat().st_size
                metadata.size_mb = file_size / (1024 * 1024)

            cap.release()

        except Exception as e:
            print(f"Error loading video metadata: {e}")

        return metadata

    def _extract_frames(self, video_path: str, max_frames: Optional[int] = None) -> List[np.ndarray]:
        """Extract frames from video"""
        frames = []
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frames.append(frame)
            frame_count += 1

            if max_frames and frame_count >= max_frames:
                break

        cap.release()
        return frames

    def _calculate_statistics(self, results: List[ProcessingResult]) -> ProcessingStatistics:
        """Calculate processing statistics"""
        stats = ProcessingStatistics()

        stats.total_frames = len(results)
        stats.detected_frames = sum(1 for r in results if r.detected)

        if stats.detected_frames > 0:
            confidences = [r.confidence for r in results if r.detected]
            stats.average_confidence = np.mean(confidences)
            stats.data_points = sum(len(r.landmarks) if r.landmarks else 0
                                  for r in results if r.detected)

        if self._processing_start_time:
            stats.processing_time = datetime.now().timestamp() - self._processing_start_time

        stats.calculate_derived_metrics()
        return stats

    def process_video(self,
                     video_path: str,
                     show_progress: bool = True,
                     max_frames: Optional[int] = None) -> Dict:
        """
        Main video processing method - template method pattern.
        This is the common interface that eliminates duplication.
        """
        print(f"\n{'='*60}")
        print(f"Processing video: {Path(video_path).name}")
        print(f"Processor: {self.__class__.__name__}")
        print(f"{'='*60}")

        # Reset state
        self.results_data = []
        self._processing_start_time = datetime.now().timestamp()

        try:
            # Step 1: Load metadata
            self.video_metadata = self._load_video_metadata(video_path)
            print(f"Resolution: {self.video_metadata.width}x{self.video_metadata.height}")
            print(f"FPS: {self.video_metadata.fps:.1f}")
            print(f"Total frames: {self.video_metadata.total_frames}")

            # Step 2: Initialize detector
            detector = self._initialize_detector()

            # Step 3: Extract frames
            print("\nExtracting frames...")
            frames = self._extract_frames(video_path, max_frames)
            print(f"Extracted {len(frames)} frames")

            # Step 4: Process frames
            print("\nProcessing frames...")
            from tqdm import tqdm

            frame_iterator = tqdm(frames, desc="Processing") if show_progress else frames

            for frame_idx, frame in enumerate(frame_iterator):
                # Preprocess frame
                processed_frame = self._preprocess_frame(frame)

                # Detect poses
                result = self._detect_frame(processed_frame, frame_idx)
                result.timestamp = frame_idx / self.video_metadata.fps

                self.results_data.append(result)

            # Step 5: Calculate statistics
            self.statistics = self._calculate_statistics(self.results_data)

            # Step 6: Display results
            self._print_summary()

            return {
                'success': True,
                'total_frames': self.statistics.total_frames,
                'detected_frames': self.statistics.detected_frames,
                'detection_rate': self.statistics.detection_rate,
                'processing_fps': self.statistics.processing_fps,
                'statistics': self.statistics.to_dict(),
                'metadata': self.video_metadata.to_dict()
            }

        except Exception as e:
            print(f"\nError processing video: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def _print_summary(self):
        """Print processing summary"""
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total frames: {self.statistics.total_frames}")
        print(f"Detected frames: {self.statistics.detected_frames}")
        print(f"Detection rate: {self.statistics.detection_rate:.1%}")
        print(f"Average confidence: {self.statistics.average_confidence:.3f}")
        print(f"Processing speed: {self.statistics.processing_fps:.1f} fps")
        print(f"Data points: {self.statistics.data_points}")
        print(f"{'='*60}")

    def export_csv(self, output_path: Optional[str] = None) -> str:
        """Export results to CSV - common implementation"""
        if not self.results_data:
            print("No data to export!")
            return ""

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"pose_data_{timestamp}.csv"
        else:
            output_path = Path(output_path)

        # Convert results to DataFrame
        rows = []
        for result in self.results_data:
            if result.detected and result.landmarks:
                for landmark_idx, landmark in enumerate(result.landmarks):
                    rows.append({
                        'frame_id': result.frame_idx,
                        'timestamp': result.timestamp,
                        'landmark_id': landmark_idx,
                        'x': getattr(landmark, 'x', 0),
                        'y': getattr(landmark, 'y', 0),
                        'z': getattr(landmark, 'z', 0),
                        'visibility': getattr(landmark, 'visibility', 0),
                        'confidence': result.confidence
                    })

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)

        print(f"Exported {len(rows)} data points to: {output_path}")
        return str(output_path)

    def export_json(self, output_path: Optional[str] = None) -> str:
        """Export comprehensive results to JSON"""
        if not self.results_data:
            print("No data to export!")
            return ""

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"pose_results_{timestamp}.json"
        else:
            output_path = Path(output_path)

        # Prepare export data
        export_data = {
            'metadata': self.video_metadata.to_dict(),
            'statistics': self.statistics.to_dict(),
            'processing_info': {
                'processor_class': self.__class__.__name__,
                'detection_confidence': self.detection_confidence,
                'tracking_confidence': self.tracking_confidence,
                'processed_at': datetime.now().isoformat()
            },
            'results': [result.to_dict() for result in self.results_data]
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        print(f"Exported comprehensive results to: {output_path}")
        return str(output_path)

    def get_dataframe(self) -> pd.DataFrame:
        """Get results as pandas DataFrame - common implementation"""
        if not self.results_data:
            return pd.DataFrame()

        rows = []
        for result in self.results_data:
            if result.detected and result.landmarks:
                for landmark_idx, landmark in enumerate(result.landmarks):
                    rows.append({
                        'frame_id': result.frame_idx,
                        'timestamp': result.timestamp,
                        'landmark_id': landmark_idx,
                        'x': getattr(landmark, 'x', 0),
                        'y': getattr(landmark, 'y', 0),
                        'z': getattr(landmark, 'z', 0),
                        'visibility': getattr(landmark, 'visibility', 0),
                        'confidence': result.confidence
                    })

        return pd.DataFrame(rows)

    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        return self.statistics.to_dict()

    def cleanup(self):
        """Cleanup resources - override in subclasses"""
        pass

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


class BaseMediaPipeProcessor(BaseVideoProcessor):
    """
    Base class for MediaPipe-based processors.
    Eliminates MediaPipe initialization duplication.
    """

    def __init__(self,
                 output_dir: str = "output",
                 detection_confidence: float = 0.5,
                 tracking_confidence: float = 0.5,
                 model_complexity: int = 1,
                 enable_segmentation: bool = False):

        super().__init__(output_dir, detection_confidence, tracking_confidence)

        self.model_complexity = model_complexity
        self.enable_segmentation = enable_segmentation
        self._pose_detector = None

    def _initialize_detector(self) -> Any:
        """Initialize MediaPipe pose detector"""
        import mediapipe as mp

        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        self._pose_detector = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=self.model_complexity,
            enable_segmentation=self.enable_segmentation,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence
        )

        return self._pose_detector

    def _detect_frame(self, frame: np.ndarray, frame_idx: int) -> ProcessingResult:
        """Detect poses using MediaPipe"""
        result = ProcessingResult(frame_idx, 0.0)

        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process with MediaPipe
            mp_result = self._pose_detector.process(rgb_frame)

            if mp_result.pose_landmarks:
                result.detected = True
                result.landmarks = mp_result.pose_landmarks.landmark
                result.confidence = np.mean([lm.visibility for lm in result.landmarks])
                result.metadata = {
                    'pose_landmarks': True,
                    'model_complexity': self.model_complexity
                }

        except Exception as e:
            result.metadata['error'] = str(e)

        return result

    def cleanup(self):
        """Cleanup MediaPipe resources"""
        if self._pose_detector:
            self._pose_detector.close()
            self._pose_detector = None