"""
Base Pose Detector - Abstract base class for all pose detection implementations
Provides common interface and shared functionality
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import logging


@dataclass
class PoseConfig:
    """Configuration for pose detection"""
    model_complexity: int = 1
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    enable_segmentation: bool = False
    smooth_landmarks: bool = True
    static_image_mode: bool = False


@dataclass
class Landmark:
    """Represents a pose landmark"""
    x: float  # Normalized x coordinate (0-1)
    y: float  # Normalized y coordinate (0-1)
    z: float  # Normalized z coordinate
    visibility: float  # Visibility/confidence score (0-1)
    name: Optional[str] = None
    id: Optional[int] = None


@dataclass
class PoseResult:
    """Contains pose detection results for a frame"""
    landmarks: List[Landmark]
    detected: bool
    frame_idx: int
    timestamp: Optional[float] = None
    world_landmarks: Optional[List[Landmark]] = None
    segmentation_mask: Optional[np.ndarray] = None

    @property
    def num_landmarks(self) -> int:
        """Get number of detected landmarks"""
        return len(self.landmarks) if self.landmarks else 0

    @property
    def detection_confidence(self) -> float:
        """Calculate average visibility/confidence across landmarks"""
        if not self.landmarks:
            return 0.0
        return sum(lm.visibility for lm in self.landmarks) / len(self.landmarks)


class BasePoseDetector(ABC):
    """
    Abstract base class for pose detection implementations

    This class defines the interface that all pose detectors must implement
    and provides common utility methods.
    """

    def __init__(self, config: Optional[PoseConfig] = None):
        """
        Initialize base pose detector

        Args:
            config: Pose detection configuration
        """
        self.config = config or PoseConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_initialized = False

    @abstractmethod
    def detect_pose(self, frame: np.ndarray) -> PoseResult:
        """
        Detect pose in a single frame

        Args:
            frame: Input frame as numpy array (BGR format)

        Returns:
            PoseResult containing detected landmarks
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the pose detection model"""
        pass

    @abstractmethod
    def release(self) -> None:
        """Release resources and cleanup"""
        pass

    def get_confidence(self) -> Tuple[float, float]:
        """
        Get current confidence thresholds

        Returns:
            Tuple of (detection_confidence, tracking_confidence)
        """
        return (
            self.config.min_detection_confidence,
            self.config.min_tracking_confidence
        )

    def set_confidence(self,
                       detection: Optional[float] = None,
                       tracking: Optional[float] = None) -> None:
        """
        Update confidence thresholds

        Args:
            detection: New detection confidence (0-1)
            tracking: New tracking confidence (0-1)
        """
        if detection is not None:
            self.config.min_detection_confidence = max(0.0, min(1.0, detection))

        if tracking is not None:
            self.config.min_tracking_confidence = max(0.0, min(1.0, tracking))

    def process_batch(self,
                      frames: List[np.ndarray],
                      progress_callback: Optional[callable] = None) -> List[PoseResult]:
        """
        Process multiple frames in batch

        Args:
            frames: List of frames to process
            progress_callback: Optional callback for progress updates

        Returns:
            List of PoseResults
        """
        results = []
        total_frames = len(frames)

        for idx, frame in enumerate(frames):
            try:
                result = self.detect_pose(frame)
                result.frame_idx = idx
                results.append(result)

                if progress_callback:
                    progress_callback(idx + 1, total_frames)

            except Exception as e:
                self.logger.error(f"Error processing frame {idx}: {e}")
                # Return empty result for failed frame
                results.append(PoseResult(
                    landmarks=[],
                    detected=False,
                    frame_idx=idx
                ))

        return results

    def calculate_pose_quality(self, result: PoseResult) -> Dict[str, float]:
        """
        Calculate quality metrics for a pose detection result

        Args:
            result: Pose detection result

        Returns:
            Dictionary of quality metrics
        """
        if not result.detected or not result.landmarks:
            return {
                'detection_rate': 0.0,
                'average_confidence': 0.0,
                'visible_landmarks': 0,
                'total_landmarks': 0
            }

        visible_count = sum(1 for lm in result.landmarks if lm.visibility > 0.5)

        return {
            'detection_rate': 1.0 if result.detected else 0.0,
            'average_confidence': result.detection_confidence,
            'visible_landmarks': visible_count,
            'total_landmarks': len(result.landmarks),
            'visibility_ratio': visible_count / len(result.landmarks) if result.landmarks else 0
        }

    def filter_landmarks(self,
                        landmarks: List[Landmark],
                        min_visibility: float = 0.5) -> List[Landmark]:
        """
        Filter landmarks by visibility threshold

        Args:
            landmarks: List of landmarks to filter
            min_visibility: Minimum visibility threshold

        Returns:
            Filtered list of landmarks
        """
        return [lm for lm in landmarks if lm.visibility >= min_visibility]

    def get_landmark_by_name(self,
                             result: PoseResult,
                             name: str) -> Optional[Landmark]:
        """
        Get specific landmark by name

        Args:
            result: Pose detection result
            name: Landmark name

        Returns:
            Landmark if found, None otherwise
        """
        for landmark in result.landmarks:
            if landmark.name == name:
                return landmark
        return None

    def calculate_joint_angle(self,
                             point1: Landmark,
                             point2: Landmark,
                             point3: Landmark) -> float:
        """
        Calculate angle between three points (joint angle)

        Args:
            point1: First landmark
            point2: Middle landmark (joint)
            point3: Third landmark

        Returns:
            Angle in degrees
        """
        # Convert to numpy arrays
        a = np.array([point1.x, point1.y])
        b = np.array([point2.x, point2.y])
        c = np.array([point3.x, point3.y])

        # Calculate vectors
        ba = a - b
        bc = c - b

        # Calculate angle
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

        return np.degrees(angle)

    def normalize_landmarks(self,
                           landmarks: List[Landmark],
                           frame_width: int,
                           frame_height: int) -> List[Landmark]:
        """
        Normalize landmark coordinates to 0-1 range

        Args:
            landmarks: List of landmarks
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels

        Returns:
            Normalized landmarks
        """
        normalized = []
        for lm in landmarks:
            normalized.append(Landmark(
                x=lm.x / frame_width if lm.x > 1 else lm.x,
                y=lm.y / frame_height if lm.y > 1 else lm.y,
                z=lm.z,
                visibility=lm.visibility,
                name=lm.name,
                id=lm.id
            ))
        return normalized

    def denormalize_landmarks(self,
                             landmarks: List[Landmark],
                             frame_width: int,
                             frame_height: int) -> List[Landmark]:
        """
        Convert normalized coordinates to pixel coordinates

        Args:
            landmarks: List of normalized landmarks
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels

        Returns:
            Denormalized landmarks
        """
        denormalized = []
        for lm in landmarks:
            denormalized.append(Landmark(
                x=lm.x * frame_width if lm.x <= 1 else lm.x,
                y=lm.y * frame_height if lm.y <= 1 else lm.y,
                z=lm.z,
                visibility=lm.visibility,
                name=lm.name,
                id=lm.id
            ))
        return denormalized

    @property
    def is_initialized(self) -> bool:
        """Check if detector is initialized"""
        return self._is_initialized

    def __enter__(self):
        """Context manager entry"""
        if not self.is_initialized:
            self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()

    def __repr__(self) -> str:
        """String representation"""
        return (f"{self.__class__.__name__}("
                f"detection_conf={self.config.min_detection_confidence:.2f}, "
                f"tracking_conf={self.config.min_tracking_confidence:.2f})")