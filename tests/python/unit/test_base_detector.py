"""
Unit tests for BasePoseDetector and related classes
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from typing import List

from cli.src.core.base_detector import (
    BasePoseDetector, PoseConfig, Landmark, PoseResult
)


class MockPoseDetector(BasePoseDetector):
    """Concrete implementation for testing"""

    def __init__(self, config=None):
        super().__init__(config)
        self.initialized = False
        self.released = False

    def detect_pose(self, frame: np.ndarray) -> PoseResult:
        """Mock implementation"""
        landmarks = [
            Landmark(x=0.5, y=0.5, z=0.0, visibility=0.8, name="nose", id=0),
            Landmark(x=0.3, y=0.4, z=0.1, visibility=0.9, name="left_eye", id=1),
            Landmark(x=0.7, y=0.4, z=0.1, visibility=0.7, name="right_eye", id=2)
        ]
        return PoseResult(
            landmarks=landmarks,
            detected=True,
            frame_idx=0,
            timestamp=0.0
        )

    def initialize(self) -> None:
        """Mock initialization"""
        self.initialized = True
        self._is_initialized = True

    def release(self) -> None:
        """Mock release"""
        self.released = True
        self._is_initialized = False


class TestPoseConfig:
    """Test PoseConfig dataclass"""

    def test_default_values(self):
        """Test default configuration values"""
        config = PoseConfig()

        assert config.model_complexity == 1
        assert config.min_detection_confidence == 0.5
        assert config.min_tracking_confidence == 0.5
        assert config.enable_segmentation is False
        assert config.smooth_landmarks is True
        assert config.static_image_mode is False

    def test_custom_values(self):
        """Test custom configuration values"""
        config = PoseConfig(
            model_complexity=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.8,
            enable_segmentation=True,
            smooth_landmarks=False,
            static_image_mode=True
        )

        assert config.model_complexity == 2
        assert config.min_detection_confidence == 0.7
        assert config.min_tracking_confidence == 0.8
        assert config.enable_segmentation is True
        assert config.smooth_landmarks is False
        assert config.static_image_mode is True


class TestLandmark:
    """Test Landmark dataclass"""

    def test_landmark_creation(self):
        """Test landmark creation with all fields"""
        landmark = Landmark(
            x=0.5, y=0.6, z=0.1, visibility=0.9,
            name="test", id=1
        )

        assert landmark.x == 0.5
        assert landmark.y == 0.6
        assert landmark.z == 0.1
        assert landmark.visibility == 0.9
        assert landmark.name == "test"
        assert landmark.id == 1

    def test_landmark_optional_fields(self):
        """Test landmark creation with optional fields"""
        landmark = Landmark(x=0.5, y=0.6, z=0.1, visibility=0.9)

        assert landmark.name is None
        assert landmark.id is None


class TestPoseResult:
    """Test PoseResult dataclass"""

    @pytest.fixture
    def sample_landmarks(self):
        """Sample landmarks for testing"""
        return [
            Landmark(x=0.5, y=0.5, z=0.0, visibility=0.8),
            Landmark(x=0.3, y=0.4, z=0.1, visibility=0.9),
            Landmark(x=0.7, y=0.4, z=0.1, visibility=0.7)
        ]

    def test_pose_result_creation(self, sample_landmarks):
        """Test pose result creation"""
        result = PoseResult(
            landmarks=sample_landmarks,
            detected=True,
            frame_idx=5,
            timestamp=0.5
        )

        assert result.landmarks == sample_landmarks
        assert result.detected is True
        assert result.frame_idx == 5
        assert result.timestamp == 0.5

    def test_num_landmarks_property(self, sample_landmarks):
        """Test num_landmarks property"""
        result = PoseResult(landmarks=sample_landmarks, detected=True, frame_idx=0)
        assert result.num_landmarks == 3

        empty_result = PoseResult(landmarks=[], detected=False, frame_idx=0)
        assert empty_result.num_landmarks == 0

        none_result = PoseResult(landmarks=None, detected=False, frame_idx=0)
        assert none_result.num_landmarks == 0

    def test_detection_confidence_property(self, sample_landmarks):
        """Test detection_confidence property"""
        result = PoseResult(landmarks=sample_landmarks, detected=True, frame_idx=0)
        expected_confidence = (0.8 + 0.9 + 0.7) / 3
        assert abs(result.detection_confidence - expected_confidence) < 1e-6

        empty_result = PoseResult(landmarks=[], detected=False, frame_idx=0)
        assert empty_result.detection_confidence == 0.0


class TestBasePoseDetector:
    """Test BasePoseDetector abstract base class"""

    @pytest.fixture
    def detector(self):
        """Create mock detector for testing"""
        return MockPoseDetector()

    @pytest.fixture
    def custom_detector(self):
        """Create detector with custom config"""
        config = PoseConfig(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.8
        )
        return MockPoseDetector(config)

    def test_initialization_default_config(self, detector):
        """Test initialization with default config"""
        assert detector.config is not None
        assert detector.config.min_detection_confidence == 0.5
        assert detector.config.min_tracking_confidence == 0.5
        assert detector.logger is not None
        assert detector._is_initialized is False

    def test_initialization_custom_config(self, custom_detector):
        """Test initialization with custom config"""
        assert custom_detector.config.min_detection_confidence == 0.7
        assert custom_detector.config.min_tracking_confidence == 0.8

    def test_get_confidence(self, detector):
        """Test get_confidence method"""
        detection_conf, tracking_conf = detector.get_confidence()

        assert detection_conf == 0.5
        assert tracking_conf == 0.5

    def test_set_confidence(self, detector):
        """Test set_confidence method"""
        detector.set_confidence(detection=0.7, tracking=0.8)

        assert detector.config.min_detection_confidence == 0.7
        assert detector.config.min_tracking_confidence == 0.8

    def test_set_confidence_partial(self, detector):
        """Test set_confidence with partial parameters"""
        detector.set_confidence(detection=0.6)

        assert detector.config.min_detection_confidence == 0.6
        assert detector.config.min_tracking_confidence == 0.5

        detector.set_confidence(tracking=0.9)

        assert detector.config.min_detection_confidence == 0.6
        assert detector.config.min_tracking_confidence == 0.9

    def test_set_confidence_bounds(self, detector):
        """Test confidence bounds are enforced"""
        detector.set_confidence(detection=-0.1, tracking=1.5)

        assert detector.config.min_detection_confidence == 0.0
        assert detector.config.min_tracking_confidence == 1.0

    def test_process_batch(self, detector):
        """Test batch processing"""
        frames = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(3)]

        results = detector.process_batch(frames)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.frame_idx == i
            assert result.detected is True
            assert len(result.landmarks) == 3

    def test_process_batch_with_callback(self, detector):
        """Test batch processing with progress callback"""
        frames = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(2)]
        callback_calls = []

        def progress_callback(current, total):
            callback_calls.append((current, total))

        detector.process_batch(frames, progress_callback)

        assert len(callback_calls) == 2
        assert callback_calls[0] == (1, 2)
        assert callback_calls[1] == (2, 2)

    def test_process_batch_with_error(self, detector):
        """Test batch processing handles errors gracefully"""
        frames = [np.zeros((100, 100, 3), dtype=np.uint8)]

        # Mock detect_pose to raise exception
        original_detect = detector.detect_pose
        detector.detect_pose = Mock(side_effect=Exception("Test error"))

        results = detector.process_batch(frames)

        assert len(results) == 1
        assert results[0].detected is False
        assert results[0].landmarks == []

        # Restore original method
        detector.detect_pose = original_detect

    def test_calculate_pose_quality_detected(self, detector):
        """Test pose quality calculation for detected pose"""
        landmarks = [
            Landmark(x=0.5, y=0.5, z=0.0, visibility=0.8),
            Landmark(x=0.3, y=0.4, z=0.1, visibility=0.6),  # Above threshold
            Landmark(x=0.7, y=0.4, z=0.1, visibility=0.3)   # Below threshold
        ]
        result = PoseResult(landmarks=landmarks, detected=True, frame_idx=0)

        quality = detector.calculate_pose_quality(result)

        assert quality['detection_rate'] == 1.0
        assert abs(quality['average_confidence'] - (0.8 + 0.6 + 0.3) / 3) < 1e-6
        assert quality['visible_landmarks'] == 2  # Only 2 above 0.5 threshold
        assert quality['total_landmarks'] == 3
        assert abs(quality['visibility_ratio'] - 2/3) < 1e-6

    def test_calculate_pose_quality_not_detected(self, detector):
        """Test pose quality calculation for non-detected pose"""
        result = PoseResult(landmarks=[], detected=False, frame_idx=0)

        quality = detector.calculate_pose_quality(result)

        assert quality['detection_rate'] == 0.0
        assert quality['average_confidence'] == 0.0
        assert quality['visible_landmarks'] == 0
        assert quality['total_landmarks'] == 0

    def test_filter_landmarks(self, detector):
        """Test landmark filtering by visibility"""
        landmarks = [
            Landmark(x=0.5, y=0.5, z=0.0, visibility=0.8),
            Landmark(x=0.3, y=0.4, z=0.1, visibility=0.3),
            Landmark(x=0.7, y=0.4, z=0.1, visibility=0.7)
        ]

        filtered = detector.filter_landmarks(landmarks, min_visibility=0.5)

        assert len(filtered) == 2
        assert filtered[0].visibility == 0.8
        assert filtered[1].visibility == 0.7

    def test_get_landmark_by_name(self, detector):
        """Test getting landmark by name"""
        landmarks = [
            Landmark(x=0.5, y=0.5, z=0.0, visibility=0.8, name="nose"),
            Landmark(x=0.3, y=0.4, z=0.1, visibility=0.9, name="left_eye")
        ]
        result = PoseResult(landmarks=landmarks, detected=True, frame_idx=0)

        nose = detector.get_landmark_by_name(result, "nose")
        assert nose is not None
        assert nose.name == "nose"
        assert nose.x == 0.5

        missing = detector.get_landmark_by_name(result, "missing")
        assert missing is None

    def test_calculate_joint_angle(self, detector):
        """Test joint angle calculation"""
        # Create points that form a 90-degree angle
        point1 = Landmark(x=0.0, y=0.0, z=0.0, visibility=1.0)
        point2 = Landmark(x=1.0, y=0.0, z=0.0, visibility=1.0)  # Joint
        point3 = Landmark(x=1.0, y=1.0, z=0.0, visibility=1.0)

        angle = detector.calculate_joint_angle(point1, point2, point3)

        assert abs(angle - 90.0) < 1e-6

    def test_normalize_landmarks(self, detector):
        """Test landmark normalization"""
        landmarks = [
            Landmark(x=100, y=200, z=0.5, visibility=0.8),  # Pixel coordinates
            Landmark(x=0.5, y=0.6, z=0.1, visibility=0.9)   # Already normalized
        ]

        normalized = detector.normalize_landmarks(landmarks, 1000, 800)

        assert abs(normalized[0].x - 0.1) < 1e-6  # 100/1000
        assert abs(normalized[0].y - 0.25) < 1e-6  # 200/800
        assert normalized[1].x == 0.5  # Already normalized
        assert normalized[1].y == 0.6  # Already normalized

    def test_denormalize_landmarks(self, detector):
        """Test landmark denormalization"""
        landmarks = [
            Landmark(x=0.1, y=0.25, z=0.5, visibility=0.8),   # Normalized
            Landmark(x=100, y=200, z=0.1, visibility=0.9)     # Already pixel coordinates
        ]

        denormalized = detector.denormalize_landmarks(landmarks, 1000, 800)

        assert abs(denormalized[0].x - 100.0) < 1e-6  # 0.1 * 1000
        assert abs(denormalized[0].y - 200.0) < 1e-6  # 0.25 * 800
        assert denormalized[1].x == 100  # Already pixel coordinates
        assert denormalized[1].y == 200  # Already pixel coordinates

    def test_is_initialized_property(self, detector):
        """Test is_initialized property"""
        assert not detector.is_initialized

        detector.initialize()
        assert detector.is_initialized

        detector.release()
        assert not detector.is_initialized

    def test_context_manager(self, detector):
        """Test context manager functionality"""
        assert not detector.initialized
        assert not detector.is_initialized

        with detector:
            assert detector.initialized
            assert detector.is_initialized

        assert detector.released
        assert not detector.is_initialized

    def test_context_manager_already_initialized(self, detector):
        """Test context manager when already initialized"""
        detector.initialize()
        assert detector.initialized

        with detector:
            assert detector.initialized

        assert detector.released

    def test_repr(self, detector):
        """Test string representation"""
        repr_str = repr(detector)

        assert "MockPoseDetector" in repr_str
        assert "detection_conf=0.50" in repr_str
        assert "tracking_conf=0.50" in repr_str

    def test_repr_custom_config(self, custom_detector):
        """Test string representation with custom config"""
        repr_str = repr(custom_detector)

        assert "detection_conf=0.70" in repr_str
        assert "tracking_conf=0.80" in repr_str