"""Pose detection processors."""

# Only import what's actually working
from .mediapipe_fast_smart import MediaPipeFastSmart
from .mediapipe_final_optimized import MediaPipeFinalOptimized

__all__ = [
    'MediaPipeFastSmart',
    'MediaPipeFinalOptimized'
]