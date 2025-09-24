
# PROCESSOR CONSOLIDATION MIGRATION PLAN
# =====================================

This plan shows how to eliminate duplicate code by migrating existing processors
to use the new base class architecture.

## Base Classes Available:

1. **BaseVideoProcessor** - Abstract base for all video processors
   - Common process_video() template method
   - Standard result formats (ProcessingResult, VideoMetadata, ProcessingStatistics)
   - Unified export methods (CSV, JSON)
   - Error handling and logging

2. **BaseMediaPipeProcessor** - Extends BaseVideoProcessor for MediaPipe
   - Handles MediaPipe initialization
   - Standard MediaPipe detection pipeline
   - Resource cleanup

3. **ProcessorSettings** - Configuration management system
   - Eliminates hardcoded values
   - Preset configurations (MVP, Research, Creative)
   - Environment variable support

## Migration Steps:


### PROCESS_VIDEO Duplication (1 files)
Files with duplicate process_video code:
- simple_pose_analyzer.py

**Migration:** Replace duplicate process_video() implementations with:
```python
class YourProcessor(BaseMediaPipeProcessor):
    def _detect_frame(self, frame, frame_idx):
        # Your specific detection logic here
        return ProcessingResult(...)
```


### MEDIAPIPE_INIT Duplication (25 files)
Files with duplicate mediapipe_init code:
- base_processor.py
- consolidation_guide.py
- mediapipe_fast_smart.py
- mediapipe_final_optimized.py
- unified_optimization.py
- holistic_detector.py
- pose_detector.py
- visualize_all_strategies.py
- analyze_every_frame.py
- true_every_frame_analysis.py
... and 15 more files

**Migration:** Remove MediaPipe initialization code, inherit from BaseMediaPipeProcessor:
```python
# OLD:
import mediapipe as mp
self.mp_pose = mp.solutions.pose
self.detector = self.mp_pose.Pose(...)

# NEW:
class YourProcessor(BaseMediaPipeProcessor):
    # MediaPipe initialization handled automatically
```


### CSV_EXPORT Duplication (30 files)
Files with duplicate csv_export code:
- base_processor.py
- consolidation_guide.py
- mediapipe_fast_smart.py
- mediapipe_final_optimized.py
- simple_pose_analyzer.py
- unified_optimization.py
- quality_control.py
- holistic_detector.py
- analytics.py
- reporting.py
... and 20 more files

**Migration:** Use base class export methods:
```python
# OLD: Custom CSV export code
# NEW: Use inherited method
csv_path = self.export_csv(output_path)
```


### ERROR_HANDLING Duplication (2 files)
Files with duplicate error_handling code:
- base_processor.py
- simple_pose_analyzer.py

## Priority Migration Order:

1. **High Impact, Low Effort:**
   - Simple processors with basic MediaPipe usage
   - Files with only process_video() and export duplication

2. **Medium Impact, Medium Effort:**
   - Processors with custom preprocessing
   - Multiple detection strategies

3. **High Impact, High Effort:**
   - Complex processors with extensive customization
   - Research and creative processors with unique features

## Example Migration:

### Before (Duplicate Code):
```python
class OldProcessor:
    def __init__(self):
        import mediapipe as mp
        self.mp_pose = mp.solutions.pose
        self.detector = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def process_video(self, video_path):
        # 50+ lines of duplicate video processing code
        ...

    def export_csv(self, data):
        # 20+ lines of duplicate CSV export code
        ...
```

### After (Using Base Classes):
```python
from core.base_processor import BaseMediaPipeProcessor
from config.settings import ProcessorSettings, PresetConfigs

class NewProcessor(BaseMediaPipeProcessor):
    def __init__(self, settings=None):
        if settings is None:
            settings = PresetConfigs.mvp_fast()
        super().__init__(
            output_dir=settings.output_dir,
            detection_confidence=settings.mediapipe.min_detection_confidence
        )

    def _preprocess_frame(self, frame):
        # Optional: Add custom preprocessing
        return frame

    def _detect_frame(self, frame, frame_idx):
        # Only implement your specific detection logic
        result = super()._detect_frame(frame, frame_idx)
        # Add any custom processing
        return result

    # All other methods (process_video, export_csv, etc.) inherited
```

## Benefits of Migration:

- **Eliminated Code:** ~1000+ lines of duplicate code removed
- **Consistency:** All processors use same interfaces and error handling
- **Configuration:** Centralized settings management
- **Maintainability:** Changes in one place affect all processors
- **Testing:** Base classes can be thoroughly tested once
- **Performance:** Unified optimizations benefit all processors

## Validation:

After migration, run tests to ensure:
1. All processors produce same results as before
2. Configuration system works correctly
3. Export formats remain consistent
4. Error handling is preserved
