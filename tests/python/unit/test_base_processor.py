"""
Unit tests for BaseVideoProcessor and related classes
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from cli.src.core.base_processor import (
    BaseVideoProcessor, BaseMediaPipeProcessor,
    ProcessingResult, VideoMetadata, ProcessingStatistics
)


class MockVideoProcessor(BaseVideoProcessor):
    """Concrete implementation for testing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detector_initialized = False

    def _initialize_detector(self):
        """Mock detector initialization"""
        self.detector_initialized = True
        return Mock()

    def _detect_frame(self, frame, frame_idx):
        """Mock frame detection"""
        result = ProcessingResult(frame_idx, frame_idx * 0.1)
        result.detected = True
        result.landmarks = [
            Mock(x=0.5, y=0.5, z=0.0, visibility=0.8),
            Mock(x=0.3, y=0.4, z=0.1, visibility=0.9)
        ]
        result.confidence = 0.85
        return result


class TestProcessingResult:
    """Test ProcessingResult class"""

    def test_initialization(self):
        """Test ProcessingResult initialization"""
        result = ProcessingResult(5, 0.5)

        assert result.frame_idx == 5
        assert result.timestamp == 0.5
        assert result.detected is False
        assert result.landmarks is None
        assert result.confidence == 0.0
        assert result.metadata == {}

    def test_to_dict(self):
        """Test conversion to dictionary"""
        result = ProcessingResult(10, 1.0)
        result.detected = True
        result.landmarks = ["landmark1", "landmark2"]
        result.confidence = 0.9
        result.metadata = {"test": "value"}

        result_dict = result.to_dict()

        assert result_dict["frame_idx"] == 10
        assert result_dict["timestamp"] == 1.0
        assert result_dict["detected"] is True
        assert result_dict["landmarks"] == ["landmark1", "landmark2"]
        assert result_dict["confidence"] == 0.9
        assert result_dict["metadata"] == {"test": "value"}


class TestVideoMetadata:
    """Test VideoMetadata class"""

    def test_initialization_empty(self):
        """Test VideoMetadata initialization with no path"""
        metadata = VideoMetadata()

        assert metadata.video_path == ""
        assert metadata.filename == ""
        assert metadata.width == 0
        assert metadata.height == 0
        assert metadata.fps == 0.0
        assert metadata.total_frames == 0
        assert metadata.duration == 0.0
        assert metadata.format == ""
        assert metadata.size_mb == 0.0
        assert isinstance(metadata.created_at, datetime)

    def test_initialization_with_path(self):
        """Test VideoMetadata initialization with path"""
        metadata = VideoMetadata("/path/to/video.mp4")

        assert metadata.video_path == "/path/to/video.mp4"
        assert metadata.filename == "video.mp4"

    def test_to_dict(self):
        """Test conversion to dictionary"""
        metadata = VideoMetadata("/test/video.mp4")
        metadata.width = 1920
        metadata.height = 1080
        metadata.fps = 30.0
        metadata.total_frames = 900
        metadata.duration = 30.0

        metadata_dict = metadata.to_dict()

        assert metadata_dict["video_path"] == "/test/video.mp4"
        assert metadata_dict["filename"] == "video.mp4"
        assert metadata_dict["width"] == 1920
        assert metadata_dict["height"] == 1080
        assert metadata_dict["fps"] == 30.0
        assert metadata_dict["total_frames"] == 900
        assert metadata_dict["duration"] == 30.0
        assert "created_at" in metadata_dict


class TestProcessingStatistics:
    """Test ProcessingStatistics class"""

    def test_initialization(self):
        """Test ProcessingStatistics initialization"""
        stats = ProcessingStatistics()

        assert stats.total_frames == 0
        assert stats.detected_frames == 0
        assert stats.detection_rate == 0.0
        assert stats.average_confidence == 0.0
        assert stats.processing_fps == 0.0
        assert stats.processing_time == 0.0
        assert stats.data_points == 0
        assert stats.quality_metrics == {}
        assert stats.errors == []

    def test_calculate_derived_metrics(self):
        """Test derived metrics calculation"""
        stats = ProcessingStatistics()
        stats.total_frames = 100
        stats.detected_frames = 80
        stats.processing_time = 10.0

        stats.calculate_derived_metrics()

        assert stats.detection_rate == 0.8
        assert stats.processing_fps == 10.0

    def test_calculate_derived_metrics_zero_division(self):
        """Test derived metrics with zero values"""
        stats = ProcessingStatistics()

        stats.calculate_derived_metrics()

        assert stats.detection_rate == 0.0
        assert stats.processing_fps == 0.0

    def test_to_dict(self):
        """Test conversion to dictionary"""
        stats = ProcessingStatistics()
        stats.total_frames = 50
        stats.detected_frames = 40
        stats.detection_rate = 0.8
        stats.errors = ["error1", "error2"]

        stats_dict = stats.to_dict()

        assert stats_dict["total_frames"] == 50
        assert stats_dict["detected_frames"] == 40
        assert stats_dict["detection_rate"] == 0.8
        assert stats_dict["error_count"] == 2


class TestBaseVideoProcessor:
    """Test BaseVideoProcessor abstract base class"""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create mock processor for testing"""
        return MockVideoProcessor(output_dir=str(tmp_path))

    @pytest.fixture
    def sample_results(self):
        """Sample processing results for testing"""
        results = []
        for i in range(3):
            result = ProcessingResult(i, i * 0.1)
            result.detected = i > 0  # First frame not detected
            if result.detected:
                result.landmarks = [Mock(x=0.5, y=0.5, z=0.0, visibility=0.8)]
                result.confidence = 0.8 + i * 0.1
            results.append(result)
        return results

    def test_initialization(self, tmp_path):
        """Test processor initialization"""
        processor = MockVideoProcessor(
            output_dir=str(tmp_path),
            detection_confidence=0.7,
            tracking_confidence=0.8
        )

        assert processor.output_dir == tmp_path
        assert processor.detection_confidence == 0.7
        assert processor.tracking_confidence == 0.8
        assert len(processor.results_data) == 0
        assert isinstance(processor.video_metadata, VideoMetadata)
        assert isinstance(processor.statistics, ProcessingStatistics)

    @patch('cv2.VideoCapture')
    def test_load_video_metadata(self, mock_cv2_cap, processor, tmp_path):
        """Test video metadata loading"""
        # Create a test file for size calculation
        test_file = tmp_path / "test.mp4"
        test_file.write_bytes(b"test" * 1024)  # 4KB file

        # Mock OpenCV capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: 1920,  # CAP_PROP_FRAME_WIDTH
            1: 1080,  # CAP_PROP_FRAME_HEIGHT
            5: 30.0,  # CAP_PROP_FPS
            7: 900    # CAP_PROP_FRAME_COUNT
        }.get(prop, 0)
        mock_cv2_cap.return_value = mock_cap

        metadata = processor._load_video_metadata(str(test_file))

        assert metadata.width == 1920
        assert metadata.height == 1080
        assert metadata.fps == 30.0
        assert metadata.total_frames == 900
        assert metadata.duration == 30.0  # 900 / 30
        assert metadata.size_mb == 4.0 / 1024  # 4KB in MB

    @patch('cv2.VideoCapture')
    def test_load_video_metadata_error(self, mock_cv2_cap, processor):
        """Test video metadata loading with error"""
        mock_cv2_cap.side_effect = Exception("OpenCV error")

        metadata = processor._load_video_metadata("nonexistent.mp4")

        # Should return default values without crashing
        assert metadata.width == 0
        assert metadata.height == 0

    @patch('cv2.VideoCapture')
    def test_extract_frames(self, mock_cv2_cap, processor):
        """Test frame extraction"""
        # Mock frames
        frames_data = [
            np.ones((100, 100, 3), dtype=np.uint8) * i
            for i in range(3)
        ]

        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = [
            (True, frames_data[0]),
            (True, frames_data[1]),
            (True, frames_data[2]),
            (False, None)  # End of video
        ]
        mock_cv2_cap.return_value = mock_cap

        frames = processor._extract_frames("test.mp4")

        assert len(frames) == 3
        np.testing.assert_array_equal(frames[0], frames_data[0])

    @patch('cv2.VideoCapture')
    def test_extract_frames_with_limit(self, mock_cv2_cap, processor):
        """Test frame extraction with max_frames limit"""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.ones((100, 100, 3), dtype=np.uint8))
        mock_cv2_cap.return_value = mock_cap

        frames = processor._extract_frames("test.mp4", max_frames=2)

        assert len(frames) == 2

    @patch('cv2.VideoCapture')
    def test_extract_frames_video_not_found(self, mock_cv2_cap, processor):
        """Test frame extraction with invalid video"""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_cv2_cap.return_value = mock_cap

        with pytest.raises(ValueError, match="Cannot open video"):
            processor._extract_frames("nonexistent.mp4")

    def test_calculate_statistics(self, processor, sample_results):
        """Test statistics calculation"""
        processor._processing_start_time = datetime.now().timestamp() - 1.0

        stats = processor._calculate_statistics(sample_results)

        assert stats.total_frames == 3
        assert stats.detected_frames == 2  # Only frames 1 and 2 detected
        assert abs(stats.average_confidence - (0.9 + 1.0) / 2) < 1e-6
        assert stats.data_points == 2  # One landmark per detected frame
        assert stats.processing_time > 0
        assert stats.detection_rate == 2/3

    @patch.object(MockVideoProcessor, '_extract_frames')
    @patch.object(MockVideoProcessor, '_load_video_metadata')
    @patch('tqdm.tqdm')
    def test_process_video_success(self, mock_tqdm, mock_metadata, mock_frames, processor):
        """Test successful video processing"""
        # Setup mocks
        mock_metadata.return_value = VideoMetadata("test.mp4")
        mock_metadata.return_value.fps = 30.0
        mock_frames.return_value = [
            np.ones((100, 100, 3), dtype=np.uint8) for _ in range(2)
        ]
        mock_tqdm.side_effect = lambda x, **kwargs: x

        result = processor.process_video("test.mp4", show_progress=False)

        assert result['success'] is True
        assert result['total_frames'] == 2
        assert result['detected_frames'] == 2
        assert 'statistics' in result
        assert 'metadata' in result

    @patch.object(MockVideoProcessor, '_extract_frames')
    def test_process_video_error(self, mock_frames, processor):
        """Test video processing with error"""
        mock_frames.side_effect = Exception("Processing error")

        result = processor.process_video("test.mp4")

        assert result['success'] is False
        assert 'error' in result

    def test_export_csv(self, processor, sample_results, tmp_path):
        """Test CSV export functionality"""
        processor.results_data = sample_results

        output_path = processor.export_csv()

        assert Path(output_path).exists()

        # Read and verify CSV content
        df = pd.read_csv(output_path)
        assert len(df) == 2  # Only detected frames exported
        assert 'frame_id' in df.columns
        assert 'timestamp' in df.columns
        assert 'x' in df.columns
        assert 'visibility' in df.columns

    def test_export_csv_no_data(self, processor):
        """Test CSV export with no data"""
        result = processor.export_csv()

        assert result == ""

    def test_export_json(self, processor, sample_results, tmp_path):
        """Test JSON export functionality"""
        processor.results_data = sample_results
        processor.video_metadata.filename = "test.mp4"
        processor.statistics.total_frames = 3

        output_path = processor.export_json()

        assert Path(output_path).exists()

        # Read and verify JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'statistics' in data
        assert 'processing_info' in data
        assert 'results' in data
        assert len(data['results']) == 3

    def test_get_dataframe(self, processor, sample_results):
        """Test DataFrame creation"""
        processor.results_data = sample_results

        df = processor.get_dataframe()

        assert len(df) == 2  # Only detected frames
        assert 'frame_id' in df.columns
        assert 'timestamp' in df.columns
        assert df['frame_id'].tolist() == [1, 2]

    def test_get_dataframe_no_data(self, processor):
        """Test DataFrame creation with no data"""
        df = processor.get_dataframe()

        assert len(df) == 0

    def test_get_statistics(self, processor):
        """Test statistics getter"""
        processor.statistics.total_frames = 10

        stats = processor.get_statistics()

        assert stats['total_frames'] == 10

    def test_context_manager(self, processor):
        """Test context manager functionality"""
        with processor as p:
            assert p is processor

        # cleanup should be called (no exception should be raised)

    def test_cleanup(self, processor):
        """Test cleanup method (base implementation does nothing)"""
        processor.cleanup()  # Should not raise exception


class TestBaseMediaPipeProcessor:
    """Test BaseMediaPipeProcessor class"""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create MediaPipe processor for testing"""
        return BaseMediaPipeProcessor(output_dir=str(tmp_path))

    @patch('mediapipe.solutions.pose.Pose')
    def test_initialize_detector(self, mock_pose_class, processor):
        """Test MediaPipe detector initialization"""
        mock_detector = Mock()
        mock_pose_class.return_value = mock_detector

        detector = processor._initialize_detector()

        assert detector is mock_detector
        assert processor._pose_detector is mock_detector
        mock_pose_class.assert_called_once_with(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    @patch('cv2.cvtColor')
    def test_detect_frame_with_landmarks(self, mock_cvtcolor, processor):
        """Test frame detection with landmarks"""
        # Setup mock detector
        mock_detector = Mock()
        mock_landmarks = [Mock(visibility=0.8), Mock(visibility=0.9)]
        mock_result = Mock()
        mock_result.pose_landmarks.landmark = mock_landmarks
        mock_detector.process.return_value = mock_result
        processor._pose_detector = mock_detector

        # Mock frame conversion
        frame = np.ones((100, 100, 3), dtype=np.uint8)
        mock_cvtcolor.return_value = frame

        result = processor._detect_frame(frame, 0)

        assert result.detected is True
        assert result.landmarks == mock_landmarks
        assert abs(result.confidence - 0.85) < 1e-6  # Mean of 0.8 and 0.9

    def test_detect_frame_no_landmarks(self, processor):
        """Test frame detection without landmarks"""
        # Setup mock detector
        mock_detector = Mock()
        mock_result = Mock()
        mock_result.pose_landmarks = None
        mock_detector.process.return_value = mock_result
        processor._pose_detector = mock_detector

        frame = np.ones((100, 100, 3), dtype=np.uint8)

        result = processor._detect_frame(frame, 0)

        assert result.detected is False

    def test_detect_frame_error(self, processor):
        """Test frame detection with error"""
        # Setup mock detector that raises exception
        mock_detector = Mock()
        mock_detector.process.side_effect = Exception("Detection error")
        processor._pose_detector = mock_detector

        frame = np.ones((100, 100, 3), dtype=np.uint8)

        result = processor._detect_frame(frame, 0)

        assert result.detected is False
        assert 'error' in result.metadata

    def test_cleanup(self, processor):
        """Test cleanup method"""
        mock_detector = Mock()
        processor._pose_detector = mock_detector

        processor.cleanup()

        mock_detector.close.assert_called_once()
        assert processor._pose_detector is None

    def test_cleanup_no_detector(self, processor):
        """Test cleanup when no detector exists"""
        processor._pose_detector = None

        processor.cleanup()  # Should not raise exception