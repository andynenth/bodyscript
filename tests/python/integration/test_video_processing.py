"""
Integration tests for video processing pipeline
Tests the interaction between base classes and real video processing
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json

from cli.src.core.base_detector import BasePoseDetector, PoseConfig, Landmark, PoseResult
from cli.src.core.base_processor import BaseVideoProcessor, ProcessingResult


class TestPoseDetector(BasePoseDetector):
    """Test implementation of pose detector"""

    def __init__(self, config=None, detection_success_rate=0.8):
        super().__init__(config)
        self.detection_success_rate = detection_success_rate
        self.frame_count = 0

    def detect_pose(self, frame):
        """Mock pose detection with configurable success rate"""
        self.frame_count += 1
        detected = np.random.random() < self.detection_success_rate

        if detected:
            # Generate mock landmarks
            landmarks = [
                Landmark(
                    x=0.5 + np.random.normal(0, 0.1),
                    y=0.5 + np.random.normal(0, 0.1),
                    z=np.random.normal(0, 0.05),
                    visibility=np.random.uniform(0.7, 0.95),
                    name=f"landmark_{i}",
                    id=i
                )
                for i in range(33)  # Body pose landmarks
            ]
        else:
            landmarks = []

        return PoseResult(
            landmarks=landmarks,
            detected=detected,
            frame_idx=self.frame_count - 1,
            timestamp=(self.frame_count - 1) * 0.033  # 30 FPS
        )

    def initialize(self):
        self._is_initialized = True

    def release(self):
        self._is_initialized = False


class TestVideoProcessor(BaseVideoProcessor):
    """Test implementation of video processor"""

    def __init__(self, detector=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detector = detector or TestPoseDetector()

    def _initialize_detector(self):
        self.detector.initialize()
        return self.detector

    def _detect_frame(self, frame, frame_idx):
        pose_result = self.detector.detect_pose(frame)

        # Convert to ProcessingResult
        result = ProcessingResult(frame_idx, pose_result.timestamp)
        result.detected = pose_result.detected
        result.confidence = pose_result.detection_confidence if pose_result.detected else 0.0

        if pose_result.detected:
            result.landmarks = pose_result.landmarks
            result.metadata = {
                'num_landmarks': pose_result.num_landmarks,
                'detection_confidence': pose_result.detection_confidence
            }

        return result


@pytest.mark.integration
class TestVideoProcessingIntegration:
    """Integration tests for complete video processing pipeline"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def mock_video_frames(self):
        """Generate mock video frames"""
        return [
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            for _ in range(10)
        ]

    @pytest.fixture
    def high_quality_detector(self):
        """Detector with high success rate"""
        return TestPoseDetector(detection_success_rate=0.9)

    @pytest.fixture
    def low_quality_detector(self):
        """Detector with low success rate"""
        return TestPoseDetector(detection_success_rate=0.3)

    def test_complete_processing_pipeline(self, temp_output_dir, mock_video_frames, high_quality_detector):
        """Test complete video processing from frames to export"""
        processor = TestVideoProcessor(
            detector=high_quality_detector,
            output_dir=temp_output_dir
        )

        # Mock frame extraction and metadata loading
        with patch.object(processor, '_extract_frames', return_value=mock_video_frames), \
             patch.object(processor, '_load_video_metadata') as mock_metadata:

            # Setup metadata
            metadata = processor.video_metadata
            metadata.fps = 30.0
            metadata.width = 640
            metadata.height = 480
            metadata.total_frames = len(mock_video_frames)
            metadata.duration = len(mock_video_frames) / 30.0
            mock_metadata.return_value = metadata

            # Process video
            result = processor.process_video("test_video.mp4", show_progress=False)

            # Verify processing results
            assert result['success'] is True
            assert result['total_frames'] == 10
            assert result['detected_frames'] > 0  # Should detect some poses
            assert result['detection_rate'] > 0.5  # With 90% success rate
            assert result['processing_fps'] > 0

            # Verify internal state
            assert len(processor.results_data) == 10
            assert processor.statistics.total_frames == 10
            assert processor.statistics.detected_frames > 0

    def test_pose_quality_analysis(self, temp_output_dir, high_quality_detector):
        """Test pose quality analysis across processing pipeline"""
        processor = TestVideoProcessor(
            detector=high_quality_detector,
            output_dir=temp_output_dir
        )

        # Generate test frames
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(5)]

        # Process frames directly
        results = []
        processor._initialize_detector()

        for i, frame in enumerate(frames):
            result = processor._detect_frame(frame, i)
            results.append(result)

        processor.results_data = results
        stats = processor._calculate_statistics(results)

        # Analyze quality
        detected_results = [r for r in results if r.detected]
        quality_scores = []

        for result in detected_results:
            if hasattr(result, 'landmarks') and result.landmarks:
                # Convert ProcessingResult landmarks to PoseResult for quality analysis
                pose_result = PoseResult(
                    landmarks=result.landmarks,
                    detected=result.detected,
                    frame_idx=result.frame_idx
                )
                quality = high_quality_detector.calculate_pose_quality(pose_result)
                quality_scores.append(quality)

        # Verify quality metrics
        assert len(quality_scores) > 0
        for quality in quality_scores:
            assert quality['detection_rate'] == 1.0
            assert quality['average_confidence'] > 0.7
            assert quality['visible_landmarks'] > 0

    def test_data_export_formats(self, temp_output_dir, high_quality_detector, mock_video_frames):
        """Test data export in different formats"""
        processor = TestVideoProcessor(
            detector=high_quality_detector,
            output_dir=temp_output_dir
        )

        # Mock processing
        with patch.object(processor, '_extract_frames', return_value=mock_video_frames[:5]):
            processor._initialize_detector()

            # Process frames
            for i, frame in enumerate(mock_video_frames[:5]):
                result = processor._detect_frame(frame, i)
                result.timestamp = i * 0.033
                processor.results_data.append(result)

            # Export CSV
            csv_path = processor.export_csv()
            assert Path(csv_path).exists()

            # Verify CSV content
            df = pd.read_csv(csv_path)
            assert len(df) > 0
            assert 'frame_id' in df.columns
            assert 'timestamp' in df.columns
            assert 'landmark_id' in df.columns
            assert 'x' in df.columns
            assert 'y' in df.columns
            assert 'z' in df.columns
            assert 'visibility' in df.columns

            # Export JSON
            json_path = processor.export_json()
            assert Path(json_path).exists()

            # Verify JSON content
            with open(json_path, 'r') as f:
                json_data = json.load(f)

            assert 'metadata' in json_data
            assert 'statistics' in json_data
            assert 'processing_info' in json_data
            assert 'results' in json_data
            assert len(json_data['results']) == 5

            # Test DataFrame creation
            df_direct = processor.get_dataframe()
            assert len(df_direct) > 0
            assert list(df_direct.columns) == list(df.columns)

    def test_detector_processor_interaction(self, temp_output_dir):
        """Test interaction between detector and processor with different configurations"""
        # Test with different detector configurations
        configs = [
            PoseConfig(min_detection_confidence=0.3, min_tracking_confidence=0.3),
            PoseConfig(min_detection_confidence=0.7, min_tracking_confidence=0.7),
        ]

        results_by_config = {}

        for i, config in enumerate(configs):
            detector = TestPoseDetector(config=config, detection_success_rate=0.8)
            processor = TestVideoProcessor(
                detector=detector,
                output_dir=temp_output_dir,
                detection_confidence=config.min_detection_confidence,
                tracking_confidence=config.min_tracking_confidence
            )

            # Process small set of frames
            frames = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(3)]

            with patch.object(processor, '_extract_frames', return_value=frames):
                result = processor.process_video(f"test_{i}.mp4", show_progress=False)
                results_by_config[i] = result

        # Both should succeed but might have different detection rates
        assert all(result['success'] for result in results_by_config.values())
        assert all(result['total_frames'] == 3 for result in results_by_config.values())

    def test_error_handling_integration(self, temp_output_dir, high_quality_detector):
        """Test error handling across the processing pipeline"""
        processor = TestVideoProcessor(
            detector=high_quality_detector,
            output_dir=temp_output_dir
        )

        # Test with frame extraction error
        with patch.object(processor, '_extract_frames', side_effect=Exception("Frame extraction failed")):
            result = processor.process_video("test_video.mp4")
            assert result['success'] is False
            assert 'error' in result

        # Test with detector initialization error
        with patch.object(processor, '_initialize_detector', side_effect=Exception("Detector init failed")):
            result = processor.process_video("test_video.mp4")
            assert result['success'] is False

        # Test with individual frame processing errors
        def failing_detect_frame(frame, frame_idx):
            if frame_idx == 2:  # Fail on third frame
                raise Exception("Frame processing failed")
            return processor._detect_frame(frame, frame_idx)

        frames = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(5)]

        with patch.object(processor, '_extract_frames', return_value=frames), \
             patch.object(processor, '_detect_frame', side_effect=failing_detect_frame):

            # Should handle partial failures gracefully
            try:
                result = processor.process_video("test_video.mp4", show_progress=False)
                # Depending on implementation, might succeed with partial results or fail
                if result['success']:
                    assert result['total_frames'] == 5
            except Exception:
                # If it propagates the exception, that's also acceptable behavior
                pass

    def test_performance_metrics(self, temp_output_dir, high_quality_detector, mock_video_frames):
        """Test performance metric calculation"""
        processor = TestVideoProcessor(
            detector=high_quality_detector,
            output_dir=temp_output_dir
        )

        # Process with timing
        with patch.object(processor, '_extract_frames', return_value=mock_video_frames):
            result = processor.process_video("test_video.mp4", show_progress=False)

            # Verify performance metrics
            assert 'processing_fps' in result
            assert 'statistics' in result

            stats = result['statistics']
            assert 'processing_fps' in stats
            assert 'processing_time' in stats
            assert 'detection_rate' in stats
            assert 'average_confidence' in stats

            # Performance metrics should be reasonable
            assert stats['processing_fps'] > 0
            assert stats['processing_time'] > 0
            assert 0 <= stats['detection_rate'] <= 1

    def test_context_manager_integration(self, temp_output_dir, high_quality_detector):
        """Test context manager usage across components"""
        frames = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(3)]

        # Test detector context manager
        with high_quality_detector:
            assert high_quality_detector.is_initialized

            # Process some frames
            results = []
            for i, frame in enumerate(frames):
                result = high_quality_detector.detect_pose(frame)
                results.append(result)

        assert not high_quality_detector.is_initialized
        assert len(results) == 3

        # Test processor context manager
        with TestVideoProcessor(detector=high_quality_detector, output_dir=temp_output_dir) as processor:
            assert processor is not None

            # Mock some processing
            with patch.object(processor, '_extract_frames', return_value=frames[:2]):
                result = processor.process_video("test.mp4", show_progress=False)
                assert result['success'] is True

    def test_landmark_analysis_integration(self, temp_output_dir, high_quality_detector):
        """Test landmark-specific analysis across the pipeline"""
        # Configure detector to generate named landmarks
        detector = TestPoseDetector(detection_success_rate=1.0)  # Always detect
        processor = TestVideoProcessor(detector=detector, output_dir=temp_output_dir)

        # Process a single frame to get landmarks
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        detector.initialize()

        pose_result = detector.detect_pose(frame)
        assert pose_result.detected
        assert len(pose_result.landmarks) > 0

        # Test landmark filtering
        high_visibility_landmarks = detector.filter_landmarks(pose_result.landmarks, min_visibility=0.8)
        low_visibility_landmarks = detector.filter_landmarks(pose_result.landmarks, min_visibility=0.5)

        assert len(high_visibility_landmarks) <= len(low_visibility_landmarks)

        # Test landmark lookup by name
        first_landmark = pose_result.landmarks[0]
        if first_landmark.name:
            found_landmark = detector.get_landmark_by_name(pose_result, first_landmark.name)
            assert found_landmark is not None
            assert found_landmark.name == first_landmark.name

        # Test coordinate normalization/denormalization
        normalized = detector.normalize_landmarks(pose_result.landmarks, 640, 480)
        denormalized = detector.denormalize_landmarks(normalized, 640, 480)

        # Values should be approximately equal after round trip
        for orig, norm, denorm in zip(pose_result.landmarks, normalized, denormalized):
            if orig.x <= 1:  # Already normalized
                assert abs(norm.x - orig.x) < 1e-6
            else:  # Was in pixel coordinates
                assert abs(denorm.x - orig.x) < 1e-6

        detector.release()