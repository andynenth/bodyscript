"""
Research Pose Analyzer - Complete research system integration
Main entry point for the research-grade pose analysis system
"""

import argparse
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Optional, Dict, List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.video_loader import VideoLoader
from research.holistic_detector import HolisticPoseDetector
from research.quality_control import QualityControl
from research.analytics import BiomechanicalAnalyzer
from research.visualizations import ResearchVisualizer
from research.reporting import ResearchReporter
from research.batch_processor import BatchProcessor


class ResearchPoseAnalyzer:
    """
    Complete research-grade pose analysis system.
    Integrates all Phase 2 modules for comprehensive analysis.
    """

    def __init__(self, mode: str = 'RESEARCH'):
        """Initialize the research analyzer."""
        self.mode = mode
        self.detector = None
        self.quality_control = QualityControl()
        self.analyzer = None
        self.visualizer = ResearchVisualizer()
        self.reporter = ResearchReporter()

    def process_video(self,
                     video_path: str,
                     output_dir: str = 'research_output',
                     generate_report: bool = True,
                     generate_visualizations: bool = True,
                     holistic: bool = True) -> Dict:
        """
        Process a single video with full research pipeline.

        Args:
            video_path: Path to video file
            output_dir: Output directory for results
            generate_report: Whether to generate HTML report
            generate_visualizations: Whether to create visualizations
            holistic: Whether to use holistic detection (body+hands+face)

        Returns:
            Dictionary with all analysis results
        """
        print(f"\n{'='*60}")
        print(f"RESEARCH POSE ANALYSIS")
        print(f"{'='*60}")
        print(f"Video: {video_path}")
        print(f"Mode: {self.mode}")
        print(f"Holistic Detection: {'Yes (543 landmarks)' if holistic else 'No (33 landmarks)'}")
        print(f"{'='*60}\n")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Step 1: Load Video
        print("📹 Loading video...")
        loader = VideoLoader()
        video_data = loader.load_video(video_path)
        frames = list(loader.extract_frames(max_frames=None))
        metadata = loader.get_video_metadata()

        print(f"  ✓ Loaded {len(frames)} frames")
        print(f"  ✓ Resolution: {metadata['width']}x{metadata['height']}")
        print(f"  ✓ FPS: {metadata['fps']:.1f}")

        # Step 2: Detect Poses
        print("\n🎯 Detecting poses...")
        if holistic:
            self.detector = HolisticPoseDetector(mode=self.mode)
        else:
            from core.pose_detector import BasicPoseDetector
            self.detector = BasicPoseDetector(mode=self.mode)

        pose_results = self.detector.detect_poses(frames, progress_bar=True)

        # Convert to DataFrame
        all_data = []
        for frame_result in pose_results:
            if hasattr(frame_result, 'to_dataframe'):
                frame_df = frame_result.to_dataframe()
                if not frame_df.empty:
                    all_data.append(frame_df)

        if all_data:
            pose_df = pd.concat(all_data, ignore_index=True)
        else:
            pose_df = pd.DataFrame()

        # Get detection statistics
        stats = self.detector.get_statistics() if hasattr(self.detector, 'get_statistics') else {}
        print(f"  ✓ Processed {stats.get('frames_processed', 0)} frames")
        if holistic and stats:
            print(f"  ✓ Body detection rate: {stats.get('pose_detection_rate', 0):.1%}")
            print(f"  ✓ Hand detection rate: {stats.get('left_hand_detection_rate', 0):.1%}")
            print(f"  ✓ Face detection rate: {stats.get('face_detection_rate', 0):.1%}")

        # Step 3: Quality Control
        print("\n🔧 Applying quality control...")
        pose_df_processed, quality_metrics = self.quality_control.process_dataframe(
            pose_df, apply_all=True
        )

        # Save processed data
        data_path = output_path / f"{Path(video_path).stem}_pose_data.csv"
        pose_df_processed.to_csv(data_path, index=False)
        print(f"  ✓ Processed data saved to {data_path}")

        # Step 4: Movement Analysis
        print("\n📊 Analyzing movement patterns...")
        self.analyzer = BiomechanicalAnalyzer(fps=metadata['fps'])
        movement_report = self.analyzer.generate_movement_report(pose_df_processed)

        # Save angle data
        if 'data' in movement_report.get('joint_angles', {}):
            angles_df = movement_report['joint_angles']['data']
            angles_path = output_path / f"{Path(video_path).stem}_angles.csv"
            angles_df.to_csv(angles_path, index=False)
            print(f"  ✓ Joint angles saved to {angles_path}")

        # Print detected patterns
        patterns = movement_report.get('movement_patterns', {})
        if patterns:
            print(f"  ✓ Detected patterns: {', '.join(patterns.keys())}")

        # Step 5: Generate Visualizations
        figures = {}
        if generate_visualizations:
            print("\n📈 Generating visualizations...")
            self.visualizer.output_dir = output_path / 'visualizations'
            self.visualizer.output_dir.mkdir(exist_ok=True)

            figures = self.visualizer.generate_all_visualizations(
                df=pose_df_processed,
                angles_df=movement_report.get('joint_angles', {}).get('data'),
                symmetry_scores=movement_report.get('symmetry'),
                quality_metrics={
                    'detection_rate': quality_metrics.detection_rate,
                    'avg_confidence': quality_metrics.avg_confidence,
                    'temporal_consistency': quality_metrics.temporal_consistency,
                    'completeness': 1 - quality_metrics.missing_landmarks_rate,
                    'smoothness': 1 - quality_metrics.jitter_score
                }
            )

        # Step 6: Generate Report
        report_path = None
        if generate_report:
            print("\n📄 Generating comprehensive report...")
            self.reporter.output_dir = output_path / 'reports'
            self.reporter.output_dir.mkdir(exist_ok=True)

            # Prepare video info
            video_info = {
                'filename': Path(video_path).name,
                'duration': metadata['total_frames'] / metadata['fps'],
                'fps': metadata['fps'],
                'width': metadata['width'],
                'height': metadata['height'],
                'total_frames': metadata['total_frames'],
                'mode': self.mode
            }

            # Generate HTML report
            report_path = self.reporter.generate_html_report(
                video_info=video_info,
                pose_data=pose_df_processed,
                quality_metrics=quality_metrics.__dict__,
                movement_analysis=movement_report,
                figures=figures
            )

            # Generate executive summary
            self.reporter.generate_executive_summary(
                video_info=video_info,
                quality_metrics=quality_metrics.__dict__,
                movement_analysis=movement_report
            )

        # Print summary
        print(f"\n{'='*60}")
        print("✅ ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"📁 Output Directory: {output_path}")
        print(f"📊 Quality Score: {quality_metrics.get_overall_score():.3f}")
        print(f"🎯 Research Quality: {'Yes' if quality_metrics.is_research_quality() else 'No'}")
        if report_path:
            print(f"📄 Report: {report_path}")
        print(f"{'='*60}\n")

        return {
            'video_info': metadata,
            'pose_data': pose_df_processed,
            'quality_metrics': quality_metrics,
            'movement_analysis': movement_report,
            'detection_stats': stats,
            'output_dir': str(output_path),
            'report_path': report_path
        }

    def process_batch(self,
                     video_dir: str,
                     output_dir: str = 'batch_output',
                     pattern: str = '*.mp4',
                     parallel: bool = True) -> Dict:
        """
        Process multiple videos in batch.

        Args:
            video_dir: Directory containing videos
            output_dir: Output directory
            pattern: File pattern to match
            parallel: Whether to process in parallel

        Returns:
            Batch processing results
        """
        # Find video files
        video_path = Path(video_dir)
        video_files = list(video_path.glob(pattern))

        if not video_files:
            print(f"No videos found matching pattern '{pattern}' in {video_dir}")
            return {}

        print(f"Found {len(video_files)} videos to process")

        # Use batch processor
        processor = BatchProcessor(
            output_dir=output_dir,
            mode=self.mode
        )

        return processor.process_batch(
            video_paths=[str(f) for f in video_files],
            parallel=parallel,
            generate_reports=True,
            comparative_analysis=True
        )


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Research-grade pose analysis system'
    )

    parser.add_argument(
        'video',
        help='Path to video file or directory for batch processing'
    )

    parser.add_argument(
        '-o', '--output',
        default='research_output',
        help='Output directory (default: research_output)'
    )

    parser.add_argument(
        '-m', '--mode',
        choices=['MVP', 'RESEARCH', 'CREATIVE'],
        default='RESEARCH',
        help='Processing mode (default: RESEARCH)'
    )

    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process multiple videos in batch mode'
    )

    parser.add_argument(
        '--no-holistic',
        action='store_true',
        help='Use basic pose detection instead of holistic'
    )

    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip report generation'
    )

    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Skip visualization generation'
    )

    parser.add_argument(
        '--pattern',
        default='*.mp4',
        help='File pattern for batch processing (default: *.mp4)'
    )

    parser.add_argument(
        '--sequential',
        action='store_true',
        help='Process videos sequentially instead of parallel'
    )

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = ResearchPoseAnalyzer(mode=args.mode)

    # Process based on mode
    if args.batch:
        # Batch processing
        results = analyzer.process_batch(
            video_dir=args.video,
            output_dir=args.output,
            pattern=args.pattern,
            parallel=not args.sequential
        )
    else:
        # Single video processing
        if not os.path.isfile(args.video):
            print(f"Error: Video file not found: {args.video}")
            sys.exit(1)

        results = analyzer.process_video(
            video_path=args.video,
            output_dir=args.output,
            generate_report=not args.no_report,
            generate_visualizations=not args.no_viz,
            holistic=not args.no_holistic
        )

    return results


if __name__ == "__main__":
    # Example usage
    print("""
    Research Pose Analyzer - Examples:

    # Single video with full analysis:
    python research_pose_analyzer.py video.mp4 -o output/

    # Batch processing directory:
    python research_pose_analyzer.py videos/ --batch -o batch_output/

    # Basic pose detection only (faster):
    python research_pose_analyzer.py video.mp4 --no-holistic

    # Skip visualizations for speed:
    python research_pose_analyzer.py video.mp4 --no-viz

    # Process MOV files in batch:
    python research_pose_analyzer.py videos/ --batch --pattern "*.mov"
    """)

    # Run main if called directly
    # main()