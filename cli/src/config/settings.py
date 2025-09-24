"""
Configuration Management System
Eliminates hardcoded values and provides centralized settings
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
import os
from enum import Enum


class ProcessingMode(Enum):
    """Processing modes for different use cases"""
    MVP = "MVP"
    RESEARCH = "RESEARCH"
    CREATIVE = "CREATIVE"


class DetectionModel(Enum):
    """Available detection models"""
    BASIC_POSE = "basic_pose"      # 33 landmarks
    HOLISTIC = "holistic"          # 543 landmarks (body + hands + face)
    FAST = "fast"                  # Optimized for speed
    HIGH_ACCURACY = "high_accuracy"  # Maximum accuracy


class ExportFormat(Enum):
    """Available export formats"""
    CSV = "csv"
    JSON = "json"
    BVH = "bvh"
    FBX = "fbx"
    BLENDER = "blender"


@dataclass
class MediaPipeSettings:
    """MediaPipe-specific configuration"""
    # Detection parameters
    min_detection_confidence: float = 0.5
    min_tracking_confidence: float = 0.5
    model_complexity: int = 1
    enable_segmentation: bool = False
    static_image_mode: bool = False

    # Multiple detection strategies
    use_multiple_detectors: bool = False
    detector_configs: Dict[str, Dict] = field(default_factory=lambda: {
        'high_accuracy': {
            'static_image_mode': True,
            'model_complexity': 2,
            'min_detection_confidence': 0.1,
            'min_tracking_confidence': 0.1
        },
        'balanced': {
            'static_image_mode': True,
            'model_complexity': 1,
            'min_detection_confidence': 0.3,
            'min_tracking_confidence': 0.3
        },
        'fast': {
            'static_image_mode': False,
            'model_complexity': 0,
            'min_detection_confidence': 0.5,
            'min_tracking_confidence': 0.5
        }
    })

    # Preprocessing strategies
    preprocessing_strategies: List[str] = field(default_factory=lambda: [
        'original', 'bright', 'clahe', 'bilateral', 'sharpened',
        'hist_eq', 'gamma_corrected', 'lower_enhanced'
    ])

    # Quality thresholds
    min_visibility_threshold: float = 0.5
    anatomical_validation: bool = True
    temporal_smoothing: bool = True
    smoothing_window_size: int = 5


@dataclass
class VideoSettings:
    """Video processing configuration"""
    # Input parameters
    max_frames: Optional[int] = None
    frame_skip: int = 1
    batch_size: int = 32

    # Resolution settings
    target_width: Optional[int] = None
    target_height: Optional[int] = None
    maintain_aspect_ratio: bool = True

    # Performance settings
    use_gpu: bool = False
    parallel_processing: bool = True
    max_workers: int = 4
    memory_limit_mb: int = 2048


@dataclass
class ExportSettings:
    """Export configuration"""
    # Output formats
    formats: List[ExportFormat] = field(default_factory=lambda: [ExportFormat.CSV, ExportFormat.JSON])

    # CSV settings
    csv_include_metadata: bool = True
    csv_precision: int = 6

    # JSON settings
    json_include_raw_data: bool = False
    json_pretty_print: bool = True

    # Video overlay settings
    create_overlay_video: bool = False
    overlay_skeleton_color: Tuple[int, int, int] = (0, 255, 0)
    overlay_connection_color: Tuple[int, int, int] = (255, 0, 0)
    overlay_thickness: int = 2

    # Report generation
    generate_report: bool = True
    include_visualizations: bool = True
    include_statistics: bool = True


@dataclass
class ProcessorSettings:
    """Main configuration class combining all settings"""
    # Mode and model
    mode: ProcessingMode = ProcessingMode.MVP
    detection_model: DetectionModel = DetectionModel.BASIC_POSE

    # Output settings
    output_dir: str = "output"
    create_timestamped_folders: bool = True

    # Component settings
    mediapipe: MediaPipeSettings = field(default_factory=MediaPipeSettings)
    video: VideoSettings = field(default_factory=VideoSettings)
    export: ExportSettings = field(default_factory=ExportSettings)

    # Logging and debugging
    verbose: bool = True
    debug_mode: bool = False
    log_level: str = "INFO"
    save_debug_frames: bool = False

    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'ProcessorSettings':
        """Create settings from dictionary"""
        # Create nested objects
        mediapipe_settings = MediaPipeSettings(**config_dict.get('mediapipe', {}))
        video_settings = VideoSettings(**config_dict.get('video', {}))
        export_settings = ExportSettings(**config_dict.get('export', {}))

        # Remove nested dicts and add objects
        config_dict = config_dict.copy()
        config_dict.pop('mediapipe', None)
        config_dict.pop('video', None)
        config_dict.pop('export', None)

        # Convert enums
        if 'mode' in config_dict:
            config_dict['mode'] = ProcessingMode(config_dict['mode'])
        if 'detection_model' in config_dict:
            config_dict['detection_model'] = DetectionModel(config_dict['detection_model'])

        return cls(
            mediapipe=mediapipe_settings,
            video=video_settings,
            export=export_settings,
            **config_dict
        )

    @classmethod
    def from_json_file(cls, filepath: str) -> 'ProcessorSettings':
        """Load settings from JSON file"""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        def convert_dataclass(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: convert_dataclass(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, list):
                return [convert_dataclass(item) for item in obj]
            else:
                return obj

        return convert_dataclass(self)

    def save_to_json(self, filepath: str):
        """Save settings to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    def get_output_path(self) -> Path:
        """Get full output path with timestamping if enabled"""
        base_path = Path(self.output_dir)

        if self.create_timestamped_folders:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return base_path / timestamp

        return base_path


# Predefined configurations for common use cases
class PresetConfigs:
    """Predefined configuration presets"""

    @staticmethod
    def mvp_fast() -> ProcessorSettings:
        """Fast MVP configuration for quick testing"""
        settings = ProcessorSettings(
            mode=ProcessingMode.MVP,
            detection_model=DetectionModel.FAST
        )
        settings.mediapipe.min_detection_confidence = 0.5
        settings.mediapipe.model_complexity = 0
        settings.video.batch_size = 64
        settings.export.formats = [ExportFormat.CSV]
        settings.export.generate_report = False
        return settings

    @staticmethod
    def research_quality() -> ProcessorSettings:
        """High-quality research configuration"""
        settings = ProcessorSettings(
            mode=ProcessingMode.RESEARCH,
            detection_model=DetectionModel.HOLISTIC
        )
        settings.mediapipe.min_detection_confidence = 0.3
        settings.mediapipe.model_complexity = 2
        settings.mediapipe.use_multiple_detectors = True
        settings.mediapipe.temporal_smoothing = True
        settings.export.formats = [ExportFormat.CSV, ExportFormat.JSON]
        settings.export.create_overlay_video = True
        return settings

    @staticmethod
    def creative_full() -> ProcessorSettings:
        """Full creative platform configuration"""
        settings = ProcessorSettings(
            mode=ProcessingMode.CREATIVE,
            detection_model=DetectionModel.HOLISTIC
        )
        settings.mediapipe.use_multiple_detectors = True
        settings.export.formats = [ExportFormat.CSV, ExportFormat.JSON, ExportFormat.BVH, ExportFormat.BLENDER]
        settings.export.json_include_raw_data = True
        settings.video.parallel_processing = True
        return settings

    @staticmethod
    def debug_mode() -> ProcessorSettings:
        """Debug configuration with extensive logging"""
        settings = ProcessorSettings(
            debug_mode=True,
            verbose=True
        )
        settings.mediapipe.use_multiple_detectors = True
        settings.export.create_overlay_video = True
        settings.save_debug_frames = True
        return settings


# Landmark definitions and mappings
class LandmarkDefinitions:
    """Standard landmark definitions and mappings"""

    # MediaPipe Pose landmarks (33 points)
    POSE_LANDMARKS = {
        0: "nose",
        1: "left_eye_inner", 2: "left_eye", 3: "left_eye_outer",
        4: "right_eye_inner", 5: "right_eye", 6: "right_eye_outer",
        7: "left_ear", 8: "right_ear",
        9: "mouth_left", 10: "mouth_right",
        11: "left_shoulder", 12: "right_shoulder",
        13: "left_elbow", 14: "right_elbow",
        15: "left_wrist", 16: "right_wrist",
        17: "left_pinky", 18: "right_pinky",
        19: "left_index", 20: "right_index",
        21: "left_thumb", 22: "right_thumb",
        23: "left_hip", 24: "right_hip",
        25: "left_knee", 26: "right_knee",
        27: "left_ankle", 28: "right_ankle",
        29: "left_heel", 30: "right_heel",
        31: "left_foot_index", 32: "right_foot_index"
    }

    # Body regions for analysis
    BODY_REGIONS = {
        'head': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'upper_body': [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
        'lower_body': [23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
        'core': [11, 12, 23, 24],
        'arms': [13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
        'legs': [25, 26, 27, 28, 29, 30, 31, 32]
    }

    # Key angles for biomechanical analysis
    KEY_ANGLES = {
        'left_elbow': (11, 13, 15),      # shoulder -> elbow -> wrist
        'right_elbow': (12, 14, 16),
        'left_knee': (23, 25, 27),       # hip -> knee -> ankle
        'right_knee': (24, 26, 28),
        'left_shoulder': (13, 11, 23),   # elbow -> shoulder -> hip
        'right_shoulder': (14, 12, 24),
        'spine': (11, 23, 25)            # shoulder midpoint -> hip -> knee
    }

    # Landmark connections for skeleton visualization
    POSE_CONNECTIONS = [
        # Face
        (0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6),
        (0, 9), (0, 10), (9, 10),
        # Upper body
        (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
        (12, 14), (14, 16), (16, 18), (16, 20), (16, 22),
        (11, 23), (12, 24), (23, 24),
        # Lower body
        (23, 25), (25, 27), (27, 29), (27, 31),
        (24, 26), (26, 28), (28, 30), (28, 32),
        (29, 31), (30, 32)
    ]

    @classmethod
    def get_landmark_name(cls, landmark_id: int) -> str:
        """Get landmark name by ID"""
        return cls.POSE_LANDMARKS.get(landmark_id, f"unknown_{landmark_id}")

    @classmethod
    def get_region_landmarks(cls, region: str) -> List[int]:
        """Get landmark IDs for a body region"""
        return cls.BODY_REGIONS.get(region, [])


# Global configuration instance
DEFAULT_CONFIG = ProcessorSettings()


def get_config() -> ProcessorSettings:
    """Get current global configuration"""
    return DEFAULT_CONFIG


def set_config(config: ProcessorSettings):
    """Set global configuration"""
    global DEFAULT_CONFIG
    DEFAULT_CONFIG = config


def load_config_from_env() -> ProcessorSettings:
    """Load configuration from environment variables"""
    config = ProcessorSettings()

    # Check for environment variable overrides
    if os.getenv('BODYSCRIPT_MODE'):
        config.mode = ProcessingMode(os.getenv('BODYSCRIPT_MODE'))

    if os.getenv('BODYSCRIPT_OUTPUT_DIR'):
        config.output_dir = os.getenv('BODYSCRIPT_OUTPUT_DIR')

    if os.getenv('BODYSCRIPT_DETECTION_CONFIDENCE'):
        config.mediapipe.min_detection_confidence = float(os.getenv('BODYSCRIPT_DETECTION_CONFIDENCE'))

    if os.getenv('BODYSCRIPT_DEBUG'):
        config.debug_mode = os.getenv('BODYSCRIPT_DEBUG').lower() == 'true'

    return config