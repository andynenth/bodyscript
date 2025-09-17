"""
Creative Pose Analyzer - Main integration for creative platform
Combines all creative modules for artistic pose transformation
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
from core.pose_detector import PoseDetector
from research.holistic_detector import HolisticPoseDetector
from creative.style.style_transfer import PoseStyleTransfer
from creative.animation.animation_tools import AnimationProcessor
from creative.export.export_3d import Export3D


class CreativePoseAnalyzer:
    """
    Complete creative pose processing system.
    Integrates style transfer, animation, and export capabilities.
    """

    def __init__(self, mode: str = 'CREATIVE'):
        """Initialize the creative analyzer."""
        self.mode = mode
        self.style_transfer = PoseStyleTransfer()
        self.animation_processor = AnimationProcessor()
        self.exporter = Export3D()

    def process_video(self,
                     video_path: str,
                     output_dir: str = 'creative_output',
                     style: str = 'realistic',
                     style_strength: float = 1.0,
                     animation_smoothing: float = 0.5,
                     create_loop: bool = False,
                     export_formats: List[str] = ['json', 'csv', 'blender'],
                     holistic: bool = False) -> Dict:
        """
        Process video with creative transformations.

        Args:
            video_path: Path to video file
            output_dir: Output directory
            style: Artistic style to apply
            style_strength: Strength of style transfer (0-1)
            animation_smoothing: Smoothing strength (0-1)
            create_loop: Whether to create looping animation
            export_formats: List of export formats
            holistic: Use holistic detection

        Returns:
            Dictionary with processing results
        """
        print(f"\n{'='*60}")
        print(f"🎨 CREATIVE POSE ANALYSIS")
        print(f"{'='*60}")
        print(f"Video: {video_path}")
        print(f"Style: {style} (strength: {style_strength})")
        print(f"Animation: Smoothing={animation_smoothing}, Loop={create_loop}")
        print(f"Export Formats: {', '.join(export_formats)}")
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
            detector = HolisticPoseDetector(mode=self.mode)
        else:
            detector = PoseDetector()

        pose_results = detector.detect_poses(frames, progress_bar=True)

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

        print(f"  ✓ Detected {len(pose_df) // len(frames) if frames else 0} landmarks per frame")

        # Step 3: Apply Style Transfer
        if style != 'realistic':
            print(f"\n🎨 Applying {style} style...")
            pose_df = self.style_transfer.transform_pose(
                pose_df,
                target_style=style,
                strength=style_strength
            )
            print(f"  ✓ Style transfer complete")

        # Step 4: Animation Processing
        print("\n🎬 Processing animation...")

        # Apply smoothing
        if animation_smoothing > 0:
            pose_df = self.animation_processor.smooth_animation(
                pose_df,
                smoothing_type='gaussian',
                strength=animation_smoothing
            )
            print(f"  ✓ Applied smoothing (strength: {animation_smoothing})")

        # Create loop if requested
        if create_loop:
            pose_df = self.animation_processor.create_loop(
                pose_df,
                blend_frames=10,
                loop_type='seamless'
            )
            print(f"  ✓ Created seamless loop")

        # Add animation curves
        pose_df = self.animation_processor.add_animation_curves(
            pose_df,
            curve_type='ease_in_out'
        )
        print(f"  ✓ Applied animation curves")

        # Step 5: Export Results
        print("\n📦 Exporting results...")
        export_paths = {}
        base_name = Path(video_path).stem

        for format_type in export_formats:
            if format_type == 'json':
                path = self.exporter.export_to_json_animation(
                    pose_df,
                    str(output_path / f"{base_name}_animation.json")
                )
                export_paths['json'] = path

            elif format_type == 'csv':
                path = self.exporter.export_to_csv_3d(
                    pose_df,
                    str(output_path / f"{base_name}_poses.csv")
                )
                export_paths['csv'] = path

            elif format_type == 'blender':
                path = self.exporter.export_to_blender_python(
                    pose_df,
                    str(output_path / f"{base_name}_blender.py")
                )
                export_paths['blender'] = path

            elif format_type == 'bvh':
                path = self.exporter.export_to_bvh(
                    pose_df,
                    str(output_path / f"{base_name}.bvh")
                )
                export_paths['bvh'] = path

            elif format_type == 'fbx':
                path = self.exporter.export_to_fbx_ascii(
                    pose_df,
                    str(output_path / f"{base_name}.fbx")
                )
                export_paths['fbx'] = path

        # Print summary
        print(f"\n{'='*60}")
        print("✅ CREATIVE PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"📁 Output Directory: {output_path}")
        print(f"🎨 Applied Style: {style}")
        print(f"📊 Total Frames: {len(pose_df['frame_id'].unique())}")
        print(f"📦 Exported Formats:")
        for format_type, path in export_paths.items():
            print(f"   - {format_type.upper()}: {Path(path).name}")
        print(f"{'='*60}\n")

        return {
            'video_info': metadata,
            'pose_data': pose_df,
            'style': style,
            'export_paths': export_paths,
            'output_dir': str(output_path)
        }

    def create_style_blend(self,
                         video_path: str,
                         styles: List[Tuple[str, float]],
                         output_dir: str = 'creative_output') -> Dict:
        """
        Process video with blended styles.

        Args:
            video_path: Path to video file
            styles: List of (style_name, weight) tuples
            output_dir: Output directory

        Returns:
            Processing results
        """
        print(f"\n🎨 Creating style blend:")
        for style_name, weight in styles:
            print(f"  - {style_name}: {weight:.1%}")

        # Load and process video
        loader = VideoLoader()
        video_data = loader.load_video(video_path)
        frames = list(loader.extract_frames(max_frames=300))

        # Detect poses
        detector = PoseDetector()
        pose_results = detector.detect_poses(frames, progress_bar=True)

        # Convert to DataFrame
        all_data = []
        for frame_result in pose_results:
            if hasattr(frame_result, 'to_dataframe'):
                frame_df = frame_result.to_dataframe()
                if not frame_df.empty:
                    all_data.append(frame_df)

        pose_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

        # Apply blended styles
        blended_df = self.style_transfer.blend_styles(pose_df, styles)

        # Export results
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        export_path = self.exporter.export_to_json_animation(
            blended_df,
            str(output_path / f"{Path(video_path).stem}_blended.json")
        )

        print(f"✓ Style blend exported to {export_path}")

        return {
            'pose_data': blended_df,
            'styles': styles,
            'export_path': export_path
        }

    def create_animation_variations(self,
                                  video_path: str,
                                  output_dir: str = 'creative_output') -> Dict:
        """
        Create multiple animation variations from a single video.

        Args:
            video_path: Path to video file
            output_dir: Output directory

        Returns:
            Dictionary with variation paths
        """
        print(f"\n🎬 Creating animation variations...")

        # Load and process video
        loader = VideoLoader()
        video_data = loader.load_video(video_path)
        frames = list(loader.extract_frames(max_frames=300))
        metadata = loader.get_video_metadata()

        # Detect poses
        detector = PoseDetector()
        pose_results = detector.detect_poses(frames, progress_bar=False)

        # Convert to DataFrame
        all_data = []
        for frame_result in pose_results:
            if hasattr(frame_result, 'to_dataframe'):
                frame_df = frame_result.to_dataframe()
                if not frame_df.empty:
                    all_data.append(frame_df)

        pose_df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        base_name = Path(video_path).stem

        variations = {}

        # Variation 1: Smooth loop
        print("  Creating smooth loop...")
        loop_df = self.animation_processor.create_loop(pose_df, loop_type='seamless')
        loop_df = self.animation_processor.smooth_animation(loop_df, strength=0.7)
        variations['smooth_loop'] = self.exporter.export_to_json_animation(
            loop_df, str(output_path / f"{base_name}_smooth_loop.json")
        )

        # Variation 2: Ping-pong
        print("  Creating ping-pong animation...")
        pingpong_df = self.animation_processor.create_loop(pose_df, loop_type='pingpong')
        variations['pingpong'] = self.exporter.export_to_json_animation(
            pingpong_df, str(output_path / f"{base_name}_pingpong.json")
        )

        # Variation 3: High FPS interpolation
        print("  Creating 60fps version...")
        hifps_df = self.animation_processor.interpolate_frames(pose_df, target_fps=60)
        variations['60fps'] = self.exporter.export_to_json_animation(
            hifps_df, str(output_path / f"{base_name}_60fps.json")
        )

        # Variation 4: With secondary motion
        print("  Adding secondary motion...")
        secondary_df = self.animation_processor.add_secondary_motion(
            pose_df, 'follow_through', strength=0.3
        )
        variations['secondary'] = self.exporter.export_to_json_animation(
            secondary_df, str(output_path / f"{base_name}_secondary.json")
        )

        print(f"\n✓ Created {len(variations)} animation variations")

        return variations


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Creative pose transformation and animation system'
    )

    parser.add_argument(
        'video',
        help='Path to video file'
    )

    parser.add_argument(
        '-o', '--output',
        default='creative_output',
        help='Output directory (default: creative_output)'
    )

    parser.add_argument(
        '-s', '--style',
        choices=['realistic', 'anime', 'cartoon', 'minimalist', 'athletic'],
        default='realistic',
        help='Artistic style (default: realistic)'
    )

    parser.add_argument(
        '--strength',
        type=float,
        default=1.0,
        help='Style strength 0-1 (default: 1.0)'
    )

    parser.add_argument(
        '--smooth',
        type=float,
        default=0.5,
        help='Animation smoothing 0-1 (default: 0.5)'
    )

    parser.add_argument(
        '--loop',
        action='store_true',
        help='Create looping animation'
    )

    parser.add_argument(
        '--formats',
        nargs='+',
        default=['json', 'csv', 'blender'],
        help='Export formats (default: json csv blender)'
    )

    parser.add_argument(
        '--holistic',
        action='store_true',
        help='Use holistic detection (body+hands+face)'
    )

    parser.add_argument(
        '--variations',
        action='store_true',
        help='Create multiple animation variations'
    )

    parser.add_argument(
        '--web',
        action='store_true',
        help='Start web interface'
    )

    args = parser.parse_args()

    # Start web interface if requested
    if args.web:
        print("Starting web interface...")
        from creative.web.app import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
        return

    # Initialize analyzer
    analyzer = CreativePoseAnalyzer()

    # Check if video file exists
    if not os.path.isfile(args.video):
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)

    # Process based on mode
    if args.variations:
        # Create animation variations
        results = analyzer.create_animation_variations(
            video_path=args.video,
            output_dir=args.output
        )
    else:
        # Standard processing
        results = analyzer.process_video(
            video_path=args.video,
            output_dir=args.output,
            style=args.style,
            style_strength=args.strength,
            animation_smoothing=args.smooth,
            create_loop=args.loop,
            export_formats=args.formats,
            holistic=args.holistic
        )

    return results


if __name__ == "__main__":
    print("""
    Creative Pose Analyzer - Examples:

    # Apply anime style:
    python creative_pose_analyzer.py video.mp4 --style anime

    # Create smooth loop with cartoon style:
    python creative_pose_analyzer.py video.mp4 --style cartoon --loop --smooth 0.8

    # Export to multiple formats:
    python creative_pose_analyzer.py video.mp4 --formats json csv bvh fbx blender

    # Create animation variations:
    python creative_pose_analyzer.py video.mp4 --variations

    # Start web interface:
    python creative_pose_analyzer.py video.mp4 --web

    # Use holistic detection with style:
    python creative_pose_analyzer.py video.mp4 --holistic --style anime
    """)

    # Run main if called directly
    # main()