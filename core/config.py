"""Configuration settings for pose estimation system."""

from typing import List, Tuple


class Config:
    """Configuration settings for pose estimation"""
    
    # Model settings
    MODEL_COMPLEXITY = 1  # 0=lite, 1=full, 2=heavy
    MIN_DETECTION_CONFIDENCE = 0.5
    MIN_TRACKING_CONFIDENCE = 0.5
    
    # Processing settings
    BATCH_SIZE = 30
    SKIP_FRAMES = 1  # Process every Nth frame
    MAX_VIDEO_DURATION = 600  # seconds (10 minutes)
    
    # Output settings
    OUTPUT_FPS = 30
    OVERLAY_COLOR = (0, 255, 0)  # Green
    LANDMARK_COLOR = (0, 0, 255)  # Red
    LINE_THICKNESS = 2
    LANDMARK_RADIUS = 5
    
    # Quality thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.3
    SMOOTHING_WINDOW = 5
    
    # File limits
    MAX_FILE_SIZE_MB = 500
    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.wmv']
    
    # Resolution limits
    MIN_RESOLUTION = 480
    MAX_RESOLUTION = 1920
    
    # Pose landmark names (33 body landmarks)
    POSE_LANDMARKS = {
        0: "nose",
        1: "left_eye_inner",
        2: "left_eye",
        3: "left_eye_outer",
        4: "right_eye_inner",
        5: "right_eye",
        6: "right_eye_outer",
        7: "left_ear",
        8: "right_ear",
        9: "left_mouth",
        10: "right_mouth",
        11: "left_shoulder",
        12: "right_shoulder",
        13: "left_elbow",
        14: "right_elbow",
        15: "left_wrist",
        16: "right_wrist",
        17: "left_pinky",
        18: "right_pinky",
        19: "left_index",
        20: "right_index",
        21: "left_thumb",
        22: "right_thumb",
        23: "left_hip",
        24: "right_hip",
        25: "left_knee",
        26: "right_knee",
        27: "left_ankle",
        28: "right_ankle",
        29: "left_heel",
        30: "right_heel",
        31: "left_foot_index",
        32: "right_foot_index"
    }
    
    # Pose connections for skeleton drawing
    POSE_CONNECTIONS = [
        # Face
        (1, 2), (2, 3),  # Left eye
        (4, 5), (5, 6),  # Right eye
        (9, 10),  # Mouth
        
        # Upper body
        (11, 12),  # Shoulders
        (11, 13), (13, 15),  # Left arm
        (12, 14), (14, 16),  # Right arm
        
        # Torso
        (11, 23), (12, 24),  # Shoulder to hip
        (23, 24),  # Hips
        
        # Lower body
        (23, 25), (25, 27),  # Left leg
        (24, 26), (26, 28),  # Right leg
        
        # Feet
        (27, 29), (29, 31),  # Left foot
        (28, 30), (30, 32),  # Right foot
        
        # Hand connections
        (15, 17), (15, 19), (15, 21),  # Left hand
        (16, 18), (16, 20), (16, 22),  # Right hand
    ]
    
    # Key angles for biomechanical analysis
    KEY_ANGLES = {
        'left_elbow': (11, 13, 15),  # shoulder-elbow-wrist
        'right_elbow': (12, 14, 16),
        'left_shoulder': (13, 11, 23),  # elbow-shoulder-hip
        'right_shoulder': (14, 12, 24),
        'left_hip': (11, 23, 25),  # shoulder-hip-knee
        'right_hip': (12, 24, 26),
        'left_knee': (23, 25, 27),  # hip-knee-ankle
        'right_knee': (24, 26, 28),
    }
    
    @classmethod
    def get_landmark_name(cls, idx: int) -> str:
        """Get landmark name by index."""
        return cls.POSE_LANDMARKS.get(idx, f"landmark_{idx}")
    
    @classmethod
    def get_connection_indices(cls) -> List[Tuple[int, int]]:
        """Get pose connection indices for drawing."""
        return cls.POSE_CONNECTIONS
    
    @classmethod
    def validate_confidence(cls, confidence: float) -> bool:
        """Check if confidence score meets threshold."""
        return confidence >= cls.MIN_CONFIDENCE_THRESHOLD