"""
Refactored Simple Pose Analyzer - Demonstrates consolidation using base classes
This replaces the original simple_pose_analyzer.py with DRY-compliant implementation
"""

import numpy as np
from typing import Dict, List, Optional
from pathlib import Path

# Import our new base classes and configuration system
from core.base_processor import BaseMediaPipeProcessor, ProcessingResult
from config.settings import ProcessorSettings, PresetConfigs, LandmarkDefinitions
from utils.visualization import PoseVisualizer


class RefactoredSimpleAnalyzer(BaseMediaPipeProcessor):
    """
    Simple pose analyzer using the new base class architecture.
    Eliminates all the duplicated code from the original implementation.
    """

    def __init__(self,
                 settings: Optional[ProcessorSettings] = None):
        """Initialize with configuration system"""

        # Use preset if no settings provided
        if settings is None:
            settings = PresetConfigs.mvp_fast()

        super().__init__(
            output_dir=settings.output_dir,
            detection_confidence=settings.mediapipe.min_detection_confidence,
            tracking_confidence=settings.mediapipe.min_tracking_confidence,
            model_complexity=settings.mediapipe.model_complexity,
            enable_segmentation=settings.mediapipe.enable_segmentation
        )

        self.settings = settings
        self.visualizer = None

        # Initialize visualizer if needed
        if settings.export.include_visualizations:
            self.visualizer = PoseVisualizer(str(self.output_dir))

    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Apply preprocessing based on configuration"""
        if not self.settings.mediapipe.preprocessing_strategies:
            return frame

        # For simplicity, just apply the first strategy
        # In the unified optimizer, this would try multiple strategies
        strategy = self.settings.mediapipe.preprocessing_strategies[0]

        if strategy == 'clahe':
            return self._apply_clahe_enhancement(frame)
        elif strategy == 'bright':
            import cv2
            return cv2.convertScaleAbs(frame, alpha=1.3, beta=30)
        elif strategy == 'lower_enhanced':
            return self._enhance_lower_body(frame)
        else:
            return frame

    def _apply_clahe_enhancement(self, frame: np.ndarray) -> np.ndarray:
        """Apply CLAHE contrast enhancement"""
        import cv2

        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    def _enhance_lower_body(self, frame: np.ndarray) -> np.ndarray:
        """Enhance lower body region for better leg detection"""
        import cv2

        h, w = frame.shape[:2]
        result = frame.copy()

        # Enhance lower 2/3 of the frame
        lower_start = h // 3
        lower_region = result[lower_start:, :]

        # Apply CLAHE to lower region
        lab = cv2.cvtColor(lower_region, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        result[lower_start:, :] = enhanced
        return result

    def _detect_frame(self, frame: np.ndarray, frame_idx: int) -> ProcessingResult:
        """Enhanced detection with quality validation"""
        # Use parent's detection method
        result = super()._detect_frame(frame, frame_idx)

        # Add quality validation if enabled
        if self.settings.mediapipe.anatomical_validation and result.detected:
            if not self._validate_anatomical_constraints(result.landmarks):
                result.confidence *= 0.5  # Penalize invalid poses

        # Filter by visibility threshold
        if result.detected and result.landmarks:
            visibility_scores = [lm.visibility for lm in result.landmarks]
            avg_visibility = np.mean(visibility_scores)

            if avg_visibility < self.settings.mediapipe.min_visibility_threshold:
                result.detected = False
                result.confidence = 0.0

        return result

    def _validate_anatomical_constraints(self, landmarks) -> bool:
        """Validate basic anatomical constraints"""
        try:
            # Check if head is above hips
            nose = landmarks[0]  # Nose
            left_hip = landmarks[23]
            right_hip = landmarks[24]

            avg_hip_y = (left_hip.y + right_hip.y) / 2
            if nose.y > avg_hip_y + 0.1:  # Head below hips by more than 10%
                return False

            # Check shoulder width is reasonable
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            shoulder_width = abs(left_shoulder.x - right_shoulder.x)

            if shoulder_width < 0.05 or shoulder_width > 0.5:
                return False

            return True

        except (IndexError, AttributeError):
            return False

    def analyze_joint_angles(self) -> Dict[str, List[Dict]]:
        """Calculate joint angles from pose data"""
        if not self.results_data:
            return {}

        angle_data = {}

        for result in self.results_data:
            if result.detected and result.landmarks:
                frame_angles = {}

                # Calculate each defined angle
                for angle_name, (p1_idx, p2_idx, p3_idx) in LandmarkDefinitions.KEY_ANGLES.items():
                    if all(idx < len(result.landmarks) for idx in [p1_idx, p2_idx, p3_idx]):
                        p1 = result.landmarks[p1_idx]
                        p2 = result.landmarks[p2_idx]
                        p3 = result.landmarks[p3_idx]

                        # Only calculate if all points are visible
                        min_visibility = min(p1.visibility, p2.visibility, p3.visibility)
                        if min_visibility > self.settings.mediapipe.min_visibility_threshold:
                            angle = self._calculate_angle(p1, p2, p3)
                            frame_angles[angle_name] = {
                                'angle_degrees': angle,
                                'confidence': min_visibility,
                                'frame_id': result.frame_idx,
                                'timestamp': result.timestamp
                            }

                if frame_angles:
                    angle_data[result.frame_idx] = frame_angles

        return angle_data

    def _calculate_angle(self, p1, p2, p3) -> float:
        """Calculate angle between three points (p2 is the vertex)"""
        # Create vectors
        v1 = np.array([p1.x - p2.x, p1.y - p2.y, p1.z - p2.z])
        v2 = np.array([p3.x - p2.x, p3.y - p2.y, p3.z - p2.z])

        # Calculate angle
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))

        return np.degrees(angle)

    def create_visualizations(self) -> Dict[str, str]:
        """Create visualizations if enabled"""
        if not self.settings.export.include_visualizations or not self.visualizer:
            return {}

        if not self.results_data:
            print("No data available for visualization!")
            return {}

        print("\nGenerating visualizations...")

        # Get data as DataFrame
        df = self.get_dataframe()
        if df.empty:
            return {}

        viz_paths = {}

        try:
            # 1. Confidence over time
            viz_paths['confidence'] = self.visualizer.plot_confidence_over_time(df)

            # 2. Landmark trajectories
            viz_paths['trajectories'] = self.visualizer.plot_landmark_trajectories(df)

            # 3. Movement heatmap
            viz_paths['heatmap'] = self.visualizer.plot_movement_heatmap(df)

            # 4. Summary visualization
            if self.statistics:
                viz_paths['summary'] = self.visualizer.create_summary_visualization(
                    df, self.statistics.to_dict()
                )

            print(f"Created {len(viz_paths)} visualizations")

        except Exception as e:
            print(f"Warning: Visualization creation failed: {e}")

        return viz_paths

    def create_overlay_video(self, video_path: str, output_path: Optional[str] = None) -> str:
        """Create video with skeleton overlay"""
        if not self.settings.export.create_overlay_video:
            print("Overlay video creation disabled in settings")
            return ""

        if not self.results_data:
            print("No pose data available! Process video first.")
            return ""

        print("\nCreating overlay video...")

        # Use base class export functionality
        # This would be implemented in the base exporter
        from video.skeleton_overlay import SkeletonOverlay

        overlay_creator = SkeletonOverlay(
            color=self.settings.export.overlay_skeleton_color,
            thickness=self.settings.export.overlay_thickness
        )

        if not output_path:
            timestamp = self._get_timestamp()
            output_path = self.output_dir / f"overlay_video_{timestamp}.mp4"

        overlay_path = overlay_creator.create_overlay_video(
            video_path=video_path,
            pose_results=self.results_data,
            output_path=str(output_path)
        )

        return overlay_path

    def _get_timestamp(self) -> str:
        """Get formatted timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive analysis report"""
        if not self.settings.export.generate_report:
            return ""

        if not self.statistics:
            print("No statistics available! Process video first.")
            return ""

        timestamp = self._get_timestamp()
        report_path = self.output_dir / f"analysis_report_{timestamp}.html"

        # Calculate additional metrics
        angle_data = self.analyze_joint_angles()

        # Generate HTML report
        html_content = self._generate_html_report(angle_data)

        with open(report_path, 'w') as f:
            f.write(html_content)

        print(f"Comprehensive report saved to: {report_path}")
        return str(report_path)

    def _generate_html_report(self, angle_data: Dict) -> str:
        """Generate HTML report content"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>BodyScript Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f0f0f0; padding: 20px; margin-bottom: 20px; }}
                .metric {{ margin: 10px 0; }}
                .section {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>BodyScript Pose Analysis Report</h1>
                <p>Generated: {self._get_timestamp()}</p>
                <p>Processor: {self.__class__.__name__}</p>
            </div>

            <div class="section">
                <h2>Processing Statistics</h2>
                <div class="metric">Total Frames: {self.statistics.total_frames}</div>
                <div class="metric">Detected Frames: {self.statistics.detected_frames}</div>
                <div class="metric">Detection Rate: {self.statistics.detection_rate:.1%}</div>
                <div class="metric">Average Confidence: {self.statistics.average_confidence:.3f}</div>
                <div class="metric">Processing Speed: {self.statistics.processing_fps:.1f} fps</div>
            </div>

            <div class="section">
                <h2>Configuration Used</h2>
                <pre>{self._format_config_for_html()}</pre>
            </div>

            <div class="section">
                <h2>Joint Angle Analysis</h2>
                <p>Analyzed {len(angle_data)} frames with valid joint angles</p>
                {self._format_angle_summary(angle_data)}
            </div>
        </body>
        </html>
        """
        return html

    def _format_config_for_html(self) -> str:
        """Format configuration for HTML display"""
        config_dict = self.settings.to_dict()
        # Convert to readable format
        import json
        return json.dumps(config_dict, indent=2)

    def _format_angle_summary(self, angle_data: Dict) -> str:
        """Format angle analysis summary"""
        if not angle_data:
            return "<p>No angle data available</p>"

        # Calculate summary statistics for each joint
        angle_summary = {}
        for frame_data in angle_data.values():
            for angle_name, angle_info in frame_data.items():
                if angle_name not in angle_summary:
                    angle_summary[angle_name] = []
                angle_summary[angle_name].append(angle_info['angle_degrees'])

        html = "<table><tr><th>Joint</th><th>Avg Angle</th><th>Min</th><th>Max</th><th>Frames</th></tr>"

        for angle_name, angles in angle_summary.items():
            avg_angle = np.mean(angles)
            min_angle = np.min(angles)
            max_angle = np.max(angles)
            frame_count = len(angles)

            html += f"<tr><td>{angle_name}</td><td>{avg_angle:.1f}°</td><td>{min_angle:.1f}°</td><td>{max_angle:.1f}°</td><td>{frame_count}</td></tr>"

        html += "</table>"
        return html


# Example usage and testing
def main():
    """Example usage of the refactored analyzer"""
    print("RefactoredSimpleAnalyzer - Example Usage")
    print("=" * 60)

    # Example 1: Use preset configuration
    print("\n1. Using MVP Fast preset:")
    analyzer = RefactoredSimpleAnalyzer(PresetConfigs.mvp_fast())

    # Example 2: Custom configuration
    print("\n2. Using custom configuration:")
    custom_settings = ProcessorSettings()
    custom_settings.mediapipe.min_detection_confidence = 0.3
    custom_settings.mediapipe.preprocessing_strategies = ['clahe', 'lower_enhanced']
    custom_settings.export.include_visualizations = True
    custom_settings.export.generate_report = True

    analyzer_custom = RefactoredSimpleAnalyzer(custom_settings)

    # Test video processing (if example video exists)
    example_video = "data/test_videos/test1.mp4"
    if Path(example_video).exists():
        print(f"\nProcessing example video: {example_video}")

        # Process with custom analyzer
        results = analyzer_custom.process_video(example_video, show_progress=True)

        if results['success']:
            # Export data using base class methods
            csv_path = analyzer_custom.export_csv()
            json_path = analyzer_custom.export_json()

            # Generate visualizations
            viz_paths = analyzer_custom.create_visualizations()

            # Generate comprehensive report
            report_path = analyzer_custom.generate_comprehensive_report()

            # Create overlay video
            overlay_path = analyzer_custom.create_overlay_video(example_video)

            # Display results
            print(f"\nProcessing Complete!")
            print(f"CSV data: {csv_path}")
            print(f"JSON data: {json_path}")
            print(f"Report: {report_path}")
            print(f"Overlay video: {overlay_path}")
            print(f"Visualizations: {len(viz_paths)} files created")

    else:
        print(f"\nExample video not found: {example_video}")
        print("The refactored analyzer is ready to use with any video file!")

    print(f"\n✅ Refactored analyzer eliminates duplicate code and uses:")
    print(f"   - BaseMediaPipeProcessor for common functionality")
    print(f"   - Configuration system for settings management")
    print(f"   - Centralized export methods")
    print(f"   - Unified preprocessing strategies")


if __name__ == "__main__":
    main()