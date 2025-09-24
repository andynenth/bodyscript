"""
Consolidation Guide - Shows how to migrate existing processors to use base classes
This eliminates the 17+ duplicate implementations identified in the DRY violations report
"""

from typing import Dict, List, Tuple
from pathlib import Path
import re


class ProcessorConsolidator:
    """Helper class to analyze and consolidate duplicate processor implementations"""

    def __init__(self):
        self.duplicate_patterns = {
            'process_video': [
                r'def process_video\(.*?\):',
                r'video_loader = VideoLoader\(',
                r'\.extract_frames\(',
                r'detect_poses\(',
                r'tqdm\(.*desc.*Processing',
                r'return \{.*total_frames.*detected_frames'
            ],
            'mediapipe_init': [
                r'import mediapipe as mp',
                r'self\.mp_pose = mp\.solutions\.pose',
                r'self\.mp_pose\.Pose\(',
                r'min_detection_confidence=',
                r'min_tracking_confidence=',
                r'model_complexity='
            ],
            'csv_export': [
                r'def export.*csv',
                r'pd\.DataFrame\(',
                r'\.to_csv\(',
                r'frame_id.*timestamp.*landmark_id',
                r'x.*y.*z.*visibility'
            ],
            'error_handling': [
                r'try:.*except.*print.*Error',
                r'traceback\.print_exc\(\)',
                r'return \{\}.*error'
            ]
        }

    def analyze_duplication(self, source_dir: str) -> Dict[str, List[str]]:
        """Analyze duplicate code patterns across processors"""
        source_path = Path(source_dir)
        python_files = list(source_path.rglob("*.py"))

        duplication_report = {}

        for pattern_name, patterns in self.duplicate_patterns.items():
            duplication_report[pattern_name] = []

            for file_path in python_files:
                if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8')

                    # Check for pattern matches
                    matches = 0
                    for pattern in patterns:
                        if re.search(pattern, content, re.DOTALL | re.MULTILINE):
                            matches += 1

                    # If most patterns match, it's likely a duplicate
                    if matches >= len(patterns) * 0.6:  # 60% threshold
                        duplication_report[pattern_name].append(str(file_path))

                except (UnicodeDecodeError, PermissionError):
                    continue

        return duplication_report

    def generate_migration_plan(self, duplicates: Dict[str, List[str]]) -> str:
        """Generate migration plan for eliminating duplicates"""

        migration_plan = """
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

"""

        for pattern_type, files in duplicates.items():
            if files:
                migration_plan += f"\n### {pattern_type.upper()} Duplication ({len(files)} files)\n"
                migration_plan += f"Files with duplicate {pattern_type} code:\n"

                for file_path in files[:10]:  # Show first 10
                    relative_path = Path(file_path).name
                    migration_plan += f"- {relative_path}\n"

                if len(files) > 10:
                    migration_plan += f"... and {len(files) - 10} more files\n"

                # Provide migration guidance
                if pattern_type == 'process_video':
                    migration_plan += """
**Migration:** Replace duplicate process_video() implementations with:
```python
class YourProcessor(BaseMediaPipeProcessor):
    def _detect_frame(self, frame, frame_idx):
        # Your specific detection logic here
        return ProcessingResult(...)
```

"""
                elif pattern_type == 'mediapipe_init':
                    migration_plan += """
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

"""
                elif pattern_type == 'csv_export':
                    migration_plan += """
**Migration:** Use base class export methods:
```python
# OLD: Custom CSV export code
# NEW: Use inherited method
csv_path = self.export_csv(output_path)
```

"""

        migration_plan += """
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
"""

        return migration_plan


def demonstrate_consolidation():
    """Demonstrate the consolidation process"""
    print("🔄 PROCESSOR CONSOLIDATION DEMONSTRATION")
    print("=" * 60)

    consolidator = ProcessorConsolidator()

    # Analyze current codebase for duplications
    print("Analyzing codebase for duplicate patterns...")
    source_dir = "/Users/nrw/python/bodyscript"
    duplicates = consolidator.analyze_duplication(source_dir)

    # Display duplication analysis
    print("\n📊 DUPLICATION ANALYSIS:")
    print("-" * 40)

    total_duplicates = 0
    for pattern_type, files in duplicates.items():
        count = len(files)
        total_duplicates += count
        print(f"{pattern_type:20s}: {count:3d} files")

    print(f"\n🎯 Total duplicate implementations: {total_duplicates}")

    # Generate migration plan
    print("\n📋 Generating migration plan...")
    migration_plan = consolidator.generate_migration_plan(duplicates)

    # Save migration plan to file
    output_path = Path("PROCESSOR_CONSOLIDATION_PLAN.md")
    with open(output_path, 'w') as f:
        f.write(migration_plan)

    print(f"✅ Migration plan saved to: {output_path}")

    # Show specific examples of files to migrate
    print("\n🔍 HIGH PRIORITY MIGRATION TARGETS:")
    print("-" * 40)

    if duplicates['process_video']:
        print("process_video() duplicates:")
        for file_path in duplicates['process_video'][:5]:
            print(f"  - {Path(file_path).name}")

    if duplicates['mediapipe_init']:
        print("\nMediaPipe initialization duplicates:")
        for file_path in duplicates['mediapipe_init'][:5]:
            print(f"  - {Path(file_path).name}")

    # Provide next steps
    print(f"\n🚀 NEXT STEPS:")
    print(f"1. Review the migration plan: {output_path}")
    print(f"2. Start with simple processors (e.g., simple_pose_analyzer.py)")
    print(f"3. Test migrated processors against original implementations")
    print(f"4. Update import statements throughout the codebase")
    print(f"5. Remove original duplicate implementations")

    return duplicates, migration_plan


# Example of how to create a consolidated processor factory
class ProcessorFactory:
    """Factory for creating consolidated processors with different configurations"""

    @staticmethod
    def create_simple_analyzer(mode="fast"):
        """Create simple analyzer with different performance modes"""
        from processors.refactored_simple_analyzer import RefactoredSimpleAnalyzer
        from config.settings import PresetConfigs

        if mode == "fast":
            settings = PresetConfigs.mvp_fast()
        elif mode == "quality":
            settings = PresetConfigs.research_quality()
        elif mode == "debug":
            settings = PresetConfigs.debug_mode()
        else:
            settings = ProcessorSettings()

        return RefactoredSimpleAnalyzer(settings)

    @staticmethod
    def create_research_analyzer():
        """Create research analyzer using base classes"""
        # This would be a consolidated version of research_pose_analyzer.py
        from config.settings import PresetConfigs
        # TODO: Create RefactoredResearchAnalyzer(BaseMediaPipeProcessor)
        pass

    @staticmethod
    def create_creative_analyzer():
        """Create creative analyzer using base classes"""
        # This would be a consolidated version of creative_pose_analyzer.py
        from config.settings import PresetConfigs
        # TODO: Create RefactoredCreativeAnalyzer(BaseMediaPipeProcessor)
        pass


if __name__ == "__main__":
    demonstrate_consolidation()