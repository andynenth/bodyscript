#!/usr/bin/env python
"""
Optimized skeleton overlay video generator with enhanced visualization options.
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import argparse
from typing import List, Tuple, Dict
from collections import deque

# Enhanced pose connections with body part grouping
BODY_PARTS = {
    'face': {
        'connections': [(0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10)],
        'color': (255, 200, 150),
        'thickness': 2
    },
    'torso': {
        'connections': [(11, 12), (11, 23), (12, 24), (23, 24)],
        'color': (100, 255, 100),
        'thickness': 4
    },
    'left_arm': {
        'connections': [(11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19)],
        'color': (255, 100, 100),
        'thickness': 3
    },
    'right_arm': {
        'connections': [(12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20)],
        'color': (100, 100, 255),
        'thickness': 3
    },
    'left_leg': {
        'connections': [(23, 25), (25, 27), (27, 29), (27, 31), (29, 31)],
        'color': (255, 255, 100),
        'thickness': 3
    },
    'right_leg': {
        'connections': [(24, 26), (26, 28), (28, 30), (28, 32), (30, 32)],
        'color': (255, 100, 255),
        'thickness': 3
    }
}

class OptimizedSkeletonRenderer:
    """Enhanced skeleton rendering with optimization features."""

    def __init__(self,
                 smoothing_window: int = 5,
                 trail_length: int = 0,
                 glow_effect: bool = False,
                 adaptive_thickness: bool = True,
                 highlight_joints: bool = True):
        """
        Initialize renderer with optimization settings.

        Args:
            smoothing_window: Temporal smoothing window size
            trail_length: Number of frames for motion trail (0=disabled)
            glow_effect: Add glowing effect to skeleton
            adaptive_thickness: Vary line thickness based on confidence
            highlight_joints: Emphasize joint points
        """
        self.smoothing_window = smoothing_window
        self.trail_length = trail_length
        self.glow_effect = glow_effect
        self.adaptive_thickness = adaptive_thickness
        self.highlight_joints = highlight_joints

        # History buffers for smoothing and trails
        self.position_history = deque(maxlen=smoothing_window)
        self.trail_history = deque(maxlen=trail_length) if trail_length > 0 else None

    def smooth_positions(self, current_frame_data: pd.DataFrame) -> pd.DataFrame:
        """Apply temporal smoothing to reduce jitter."""
        if len(self.position_history) == 0:
            return current_frame_data

        # Add current frame to history
        self.position_history.append(current_frame_data)

        # Average positions over window
        smoothed = current_frame_data.copy()

        if len(self.position_history) > 1:
            # Calculate weighted average (more recent frames have more weight)
            weights = np.linspace(0.5, 1.0, len(self.position_history))
            weights = weights / weights.sum()

            for landmark_id in current_frame_data['landmark_id'].unique():
                x_vals = []
                y_vals = []

                for i, frame in enumerate(self.position_history):
                    landmark = frame[frame['landmark_id'] == landmark_id]
                    if not landmark.empty:
                        if 'x_norm' in frame.columns:
                            x_vals.append(landmark.iloc[0]['x_norm'])
                            y_vals.append(landmark.iloc[0]['y_norm'])
                        else:
                            x_vals.append(landmark.iloc[0]['x'])
                            y_vals.append(landmark.iloc[0]['y'])

                if len(x_vals) == len(self.position_history):
                    smoothed.loc[smoothed['landmark_id'] == landmark_id,
                                'x_norm' if 'x_norm' in smoothed.columns else 'x'] = np.average(x_vals, weights=weights)
                    smoothed.loc[smoothed['landmark_id'] == landmark_id,
                                'y_norm' if 'y_norm' in smoothed.columns else 'y'] = np.average(y_vals, weights=weights)

        return smoothed

    def draw_glow_line(self, frame: np.ndarray, pt1: Tuple, pt2: Tuple,
                      color: Tuple, thickness: int) -> np.ndarray:
        """Draw a line with glow effect."""
        if self.glow_effect:
            # Draw multiple lines with decreasing opacity for glow
            overlay = frame.copy()

            # Outer glow
            cv2.line(overlay, pt1, pt2, color, thickness * 3, cv2.LINE_AA)
            frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

            # Middle glow
            cv2.line(overlay, pt1, pt2, color, thickness * 2, cv2.LINE_AA)
            frame = cv2.addWeighted(frame, 0.6, overlay, 0.4, 0)

        # Main line
        cv2.line(frame, pt1, pt2, color, thickness, cv2.LINE_AA)
        return frame

    def draw_motion_trail(self, frame: np.ndarray, h: int, w: int) -> np.ndarray:
        """Draw motion trail from previous frames."""
        if self.trail_history is None or len(self.trail_history) < 2:
            return frame

        overlay = frame.copy()

        for i in range(len(self.trail_history) - 1):
            alpha = (i + 1) / len(self.trail_history) * 0.3  # Fade older trails

            old_data = self.trail_history[i]

            # Draw faded skeleton from history
            for body_part, config in BODY_PARTS.items():
                for start_idx, end_idx in config['connections']:
                    start_point = old_data[old_data['landmark_id'] == start_idx]
                    end_point = old_data[old_data['landmark_id'] == end_idx]

                    if not start_point.empty and not end_point.empty:
                        if 'x_norm' in old_data.columns:
                            x1 = int(start_point.iloc[0]['x_norm'] * w)
                            y1 = int(start_point.iloc[0]['y_norm'] * h)
                            x2 = int(end_point.iloc[0]['x_norm'] * w)
                            y2 = int(end_point.iloc[0]['y_norm'] * h)
                        else:
                            x1 = int(start_point.iloc[0]['x'] * w)
                            y1 = int(start_point.iloc[0]['y'] * h)
                            x2 = int(end_point.iloc[0]['x'] * w)
                            y2 = int(end_point.iloc[0]['y'] * h)

                        # Faded color
                        faded_color = tuple(int(c * 0.3) for c in config['color'])
                        cv2.line(overlay, (x1, y1), (x2, y2), faded_color, 1, cv2.LINE_AA)

            frame = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)

        return frame

    def render_skeleton(self, frame: np.ndarray, frame_data: pd.DataFrame,
                       confidence_threshold: float = 0.5) -> np.ndarray:
        """
        Render optimized skeleton on frame.

        Args:
            frame: Video frame
            frame_data: Pose data for this frame
            confidence_threshold: Minimum confidence to draw

        Returns:
            Frame with skeleton overlay
        """
        h, w = frame.shape[:2]

        # Apply temporal smoothing
        if self.smoothing_window > 1:
            frame_data = self.smooth_positions(frame_data)

        # Add to trail history
        if self.trail_history is not None:
            self.trail_history.append(frame_data.copy())
            frame = self.draw_motion_trail(frame, h, w)

        # Draw connections by body part
        for body_part, config in BODY_PARTS.items():
            for start_idx, end_idx in config['connections']:
                start_point = frame_data[frame_data['landmark_id'] == start_idx]
                end_point = frame_data[frame_data['landmark_id'] == end_idx]

                if not start_point.empty and not end_point.empty:
                    start_vis = start_point.iloc[0]['visibility']
                    end_vis = end_point.iloc[0]['visibility']

                    if start_vis > confidence_threshold and end_vis > confidence_threshold:
                        # Get coordinates
                        if 'x_norm' in frame_data.columns:
                            x1 = int(start_point.iloc[0]['x_norm'] * w)
                            y1 = int(start_point.iloc[0]['y_norm'] * h)
                            x2 = int(end_point.iloc[0]['x_norm'] * w)
                            y2 = int(end_point.iloc[0]['y_norm'] * h)
                        else:
                            x1 = int(start_point.iloc[0]['x'] * w)
                            y1 = int(start_point.iloc[0]['y'] * h)
                            x2 = int(end_point.iloc[0]['x'] * w)
                            y2 = int(end_point.iloc[0]['y'] * h)

                        # Calculate thickness
                        if self.adaptive_thickness:
                            thickness = int(config['thickness'] * min(start_vis, end_vis))
                        else:
                            thickness = config['thickness']

                        # Draw connection
                        frame = self.draw_glow_line(frame, (x1, y1), (x2, y2),
                                                  config['color'], thickness)

        # Draw joint points
        if self.highlight_joints:
            for _, landmark in frame_data.iterrows():
                if landmark['visibility'] > confidence_threshold:
                    if 'x_norm' in frame_data.columns:
                        x = int(landmark['x_norm'] * w)
                        y = int(landmark['y_norm'] * h)
                    else:
                        x = int(landmark['x'] * w)
                        y = int(landmark['y'] * h)

                    # Determine color based on body part
                    landmark_id = int(landmark['landmark_id'])
                    if landmark_id <= 10:
                        color = BODY_PARTS['face']['color']
                    elif landmark_id in [11, 12, 23, 24]:
                        color = BODY_PARTS['torso']['color']
                    else:
                        color = (255, 255, 255)  # White for other joints

                    # Draw joint with adaptive size
                    radius = int(4 + 4 * landmark['visibility'])

                    if self.glow_effect:
                        # Glow effect for joints
                        cv2.circle(frame, (x, y), radius + 3, color, -1)
                        overlay = frame.copy()
                        cv2.circle(overlay, (x, y), radius + 6, color, -1)
                        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

                    cv2.circle(frame, (x, y), radius, color, -1)
                    cv2.circle(frame, (x, y), radius + 1, (0, 0, 0), 1)  # Black border

        return frame

def create_optimized_overlay(video_path: str,
                            csv_path: str,
                            output_path: str,
                            optimization_settings: Dict) -> str:
    """
    Create optimized skeleton overlay video.

    Args:
        video_path: Path to original video
        csv_path: Path to pose data CSV
        output_path: Output video path
        optimization_settings: Dictionary of optimization parameters

    Returns:
        Path to created video
    """
    # Load pose data
    print(f"Loading pose data from {csv_path}...")
    pose_df = pd.read_csv(csv_path)

    # Initialize renderer
    renderer = OptimizedSkeletonRenderer(
        smoothing_window=optimization_settings.get('smoothing', 5),
        trail_length=optimization_settings.get('trail', 0),
        glow_effect=optimization_settings.get('glow', False),
        adaptive_thickness=optimization_settings.get('adaptive', True),
        highlight_joints=optimization_settings.get('joints', True)
    )

    # Open video
    print(f"Opening video: {video_path}")
    cap = cv2.VideoCapture(video_path)

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Video codec selection
    codec = optimization_settings.get('codec', 'mp4v')
    if codec == 'h264':
        fourcc = cv2.VideoWriter_fourcc(*'h264')
    elif codec == 'hevc':
        fourcc = cv2.VideoWriter_fourcc(*'hevc')
    else:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # Create video writer with higher quality
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"\nProcessing {total_frames} frames with optimizations:")
    print(f"  • Temporal smoothing: {optimization_settings.get('smoothing', 5)} frames")
    print(f"  • Motion trail: {optimization_settings.get('trail', 0)} frames")
    print(f"  • Glow effect: {optimization_settings.get('glow', False)}")
    print(f"  • Adaptive thickness: {optimization_settings.get('adaptive', True)}")
    print(f"  • Joint highlighting: {optimization_settings.get('joints', True)}")
    print(f"  • Confidence threshold: {optimization_settings.get('confidence', 0.5)}")

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Get pose data for this frame
        frame_data = pose_df[pose_df['frame_id'] == frame_idx]

        if not frame_data.empty:
            # Render optimized skeleton
            frame = renderer.render_skeleton(
                frame, frame_data,
                confidence_threshold=optimization_settings.get('confidence', 0.5)
            )

            # Add info overlay if requested
            if optimization_settings.get('info', True):
                # Background box for text
                cv2.rectangle(frame, (5, 5), (300, 70), (0, 0, 0), -1)
                cv2.rectangle(frame, (5, 5), (300, 70), (0, 255, 0), 2)

                # Frame info
                text = f"Frame: {frame_idx}/{total_frames}"
                cv2.putText(frame, text, (10, 25),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

                # Style info
                style_text = f"Style: {optimization_settings.get('style', 'Unknown')}"
                cv2.putText(frame, style_text, (10, 45),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 1)

                # FPS counter
                fps_text = f"FPS: {fps:.1f}"
                cv2.putText(frame, fps_text, (10, 65),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # Write frame
        out.write(frame)

        # Progress
        if frame_idx % 30 == 0:
            progress = (frame_idx / total_frames) * 100
            print(f"Progress: {progress:.1f}%")

        frame_idx += 1

    # Cleanup
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"\n✅ Optimized video created: {output_path}")
    return output_path

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create optimized skeleton overlay video'
    )

    parser.add_argument('--video', default='video/dance.mp4',
                       help='Input video path')
    parser.add_argument('--csv', default='creative_output/dance_poses.csv',
                       help='Pose data CSV path')
    parser.add_argument('--output', default='creative_output/skeleton_optimized.mp4',
                       help='Output video path')

    # Optimization options
    parser.add_argument('--smoothing', type=int, default=5,
                       help='Temporal smoothing window (frames)')
    parser.add_argument('--trail', type=int, default=0,
                       help='Motion trail length (0=disabled)')
    parser.add_argument('--glow', action='store_true',
                       help='Add glow effect to skeleton')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Minimum confidence threshold (0-1)')
    parser.add_argument('--codec', default='mp4v',
                       choices=['mp4v', 'h264', 'hevc'],
                       help='Video codec')
    parser.add_argument('--no-adaptive', action='store_true',
                       help='Disable adaptive line thickness')
    parser.add_argument('--no-joints', action='store_true',
                       help='Hide joint points')
    parser.add_argument('--no-info', action='store_true',
                       help='Hide info overlay')
    parser.add_argument('--style', default='Unknown',
                       help='Style name for display')

    # Presets
    parser.add_argument('--preset', choices=['smooth', 'trail', 'glow', 'minimal'],
                       help='Use optimization preset')

    args = parser.parse_args()

    # Apply presets
    optimization_settings = {
        'smoothing': args.smoothing,
        'trail': args.trail,
        'glow': args.glow,
        'confidence': args.confidence,
        'codec': args.codec,
        'adaptive': not args.no_adaptive,
        'joints': not args.no_joints,
        'info': not args.no_info,
        'style': args.style
    }

    if args.preset == 'smooth':
        optimization_settings.update({
            'smoothing': 10,
            'trail': 0,
            'glow': False,
            'adaptive': True
        })
        print("Using SMOOTH preset: Maximum temporal smoothing")
    elif args.preset == 'trail':
        optimization_settings.update({
            'smoothing': 5,
            'trail': 10,
            'glow': False,
            'adaptive': True
        })
        print("Using TRAIL preset: Motion trail visualization")
    elif args.preset == 'glow':
        optimization_settings.update({
            'smoothing': 5,
            'trail': 0,
            'glow': True,
            'adaptive': True
        })
        print("Using GLOW preset: Neon glow effect")
    elif args.preset == 'minimal':
        optimization_settings.update({
            'smoothing': 3,
            'trail': 0,
            'glow': False,
            'adaptive': False,
            'joints': False
        })
        print("Using MINIMAL preset: Clean lines only")

    # Check files
    if not Path(args.video).exists():
        print(f"❌ Video not found: {args.video}")
        sys.exit(1)

    if not Path(args.csv).exists():
        print(f"❌ CSV not found: {args.csv}")
        sys.exit(1)

    # Create output directory
    Path(args.output).parent.mkdir(exist_ok=True)

    print("="*60)
    print("🎥 OPTIMIZED SKELETON OVERLAY GENERATOR")
    print("="*60)

    # Create optimized video
    create_optimized_overlay(
        args.video,
        args.csv,
        args.output,
        optimization_settings
    )

if __name__ == "__main__":
    main()