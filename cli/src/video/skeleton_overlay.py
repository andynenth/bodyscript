#!/usr/bin/env python
"""
Create a video with pose skeleton overlay from processed pose data.
This script reads the pose data and overlays it on the original video.
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import argparse
import bisect
from typing import List, Tuple

# MediaPipe pose connections (skeleton structure)
POSE_CONNECTIONS = [
    # Face
    (0, 1), (1, 2), (2, 3), (3, 7),  # Left eye
    (0, 4), (4, 5), (5, 6), (6, 8),  # Right eye
    (9, 10),  # Mouth

    # Arms
    (11, 12),  # Shoulders
    (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),  # Left arm
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),  # Right arm

    # Torso
    (11, 23), (12, 24), (23, 24),

    # Legs
    (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),  # Left leg
    (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),  # Right leg
]

# Color scheme for different body parts
COLORS = {
    'face': (255, 200, 150),      # Light blue
    'torso': (100, 255, 100),     # Green
    'left_arm': (255, 100, 100),  # Blue
    'right_arm': (100, 100, 255), # Red
    'left_leg': (255, 255, 100),  # Cyan
    'right_leg': (255, 100, 255), # Magenta
}

def get_connection_color(start_idx: int, end_idx: int) -> Tuple[int, int, int]:
    """Get color for a connection based on body part."""
    if start_idx <= 10 or end_idx <= 10:
        return COLORS['face']
    elif start_idx in [11, 12, 23, 24] or end_idx in [11, 12, 23, 24]:
        return COLORS['torso']
    elif start_idx in [13, 15, 17, 19, 21] or end_idx in [13, 15, 17, 19, 21]:
        return COLORS['left_arm']
    elif start_idx in [14, 16, 18, 20, 22] or end_idx in [14, 16, 18, 20, 22]:
        return COLORS['right_arm']
    elif start_idx in [25, 27, 29, 31] or end_idx in [25, 27, 29, 31]:
        return COLORS['left_leg']
    elif start_idx in [26, 28, 30, 32] or end_idx in [26, 28, 30, 32]:
        return COLORS['right_leg']
    else:
        return (200, 200, 200)  # Default gray

def load_pose_data(csv_path: str) -> pd.DataFrame:
    """Load pose data from CSV file."""
    print(f"Loading pose data from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} landmark records from {df['frame_id'].nunique()} frames")
    return df

def draw_skeleton_on_frame(frame: np.ndarray,
                          frame_data: pd.DataFrame,
                          show_landmarks: bool = True,
                          show_connections: bool = True,
                          confidence_threshold: float = 0.5) -> np.ndarray:
    """Draw skeleton on a single frame.

    Args:
        frame: The video frame
        frame_data: Pose data for this frame
        show_landmarks: Whether to draw individual landmarks
        show_connections: Whether to draw skeleton connections
        confidence_threshold: Minimum confidence to draw

    Returns:
        Frame with skeleton overlay
    """
    h, w = frame.shape[:2]

    # Draw connections first (so they appear behind landmarks)
    if show_connections:
        for start_idx, end_idx in POSE_CONNECTIONS:
            start_point = frame_data[frame_data['landmark_id'] == start_idx]
            end_point = frame_data[frame_data['landmark_id'] == end_idx]

            if not start_point.empty and not end_point.empty:
                start_vis = start_point.iloc[0]['visibility']
                end_vis = end_point.iloc[0]['visibility']

                if start_vis > confidence_threshold and end_vis > confidence_threshold:
                    # Use normalized coordinates if available, else use regular
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

                    # Get color and thickness based on confidence
                    color = get_connection_color(start_idx, end_idx)
                    thickness = int(2 + 3 * min(start_vis, end_vis))

                    cv2.line(frame, (x1, y1), (x2, y2), color, thickness, cv2.LINE_AA)

    # Draw landmarks
    if show_landmarks:
        for _, landmark in frame_data.iterrows():
            if landmark['visibility'] > confidence_threshold:
                if 'x_norm' in frame_data.columns:
                    x = int(landmark['x_norm'] * w)
                    y = int(landmark['y_norm'] * h)
                else:
                    x = int(landmark['x'] * w)
                    y = int(landmark['y'] * h)

                # Draw circle with size based on confidence
                radius = int(3 + 5 * landmark['visibility'])
                cv2.circle(frame, (x, y), radius, (0, 255, 0), -1)
                cv2.circle(frame, (x, y), radius + 1, (0, 0, 0), 1)  # Black border

    return frame

def create_overlay_video(video_path: str,
                        csv_path: str,
                        output_path: str,
                        show_info: bool = True) -> str:
    """Create video with skeleton overlay.

    Args:
        video_path: Path to original video
        csv_path: Path to pose data CSV
        output_path: Path for output video
        show_info: Whether to show frame info

    Returns:
        Path to created video
    """
    # Load pose data
    pose_df = load_pose_data(csv_path)

    # Open video
    print(f"\nOpening video: {video_path}")
    cap = cv2.VideoCapture(video_path)

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Video info: {width}x{height} @ {fps:.1f} FPS, {total_frames} frames")

    # Create video writer with compressed codec
    # Try H264 first for better compression, fallback to mp4v if not available
    try:
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        print("Using H264 codec for better compression")
    except:
        try:
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            print("Using avc1 codec")
        except:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            print("Warning: Using mp4v codec (larger file size)")

    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"\nProcessing frames...")
    frame_idx = 0

    # Get all unique frame IDs from the pose data for efficient lookup
    available_frames = sorted(pose_df['frame_id'].unique())
    print(f"Available pose data for frames: {available_frames[:10]}... (showing first 10)")

    # Cache for last known pose data (for frames without data)
    last_frame_data = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Get pose data for this frame
        frame_data = pose_df[pose_df['frame_id'] == frame_idx]

        if not frame_data.empty:
            # Found exact frame data
            frame = draw_skeleton_on_frame(frame, frame_data)
            last_frame_data = frame_data  # Cache for interpolation

            # Add info text
            if show_info:
                text = f"Frame: {frame_idx}/{total_frames} | Landmarks: {len(frame_data)}"
                cv2.putText(frame, text, (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Add style info
                style_text = "Style: Anime (transformed)"
                cv2.putText(frame, style_text, (10, 60),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 0), 2)
        else:
            # No exact frame data - use nearest or last known
            # Find nearest frame with data
            if available_frames:
                # Find closest frame
                idx = bisect.bisect_left(available_frames, frame_idx)

                # Use the closest available frame (preferring previous frame)
                if idx > 0:
                    nearest_frame = available_frames[idx - 1]
                elif idx < len(available_frames):
                    nearest_frame = available_frames[idx]
                else:
                    nearest_frame = available_frames[-1]

                nearest_data = pose_df[pose_df['frame_id'] == nearest_frame]
                if not nearest_data.empty:
                    frame = draw_skeleton_on_frame(frame, nearest_data)

                    if show_info:
                        text = f"Frame: {frame_idx}/{total_frames} | Using frame {nearest_frame} data"
                        cv2.putText(frame, text, (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            elif last_frame_data is not None:
                # Fallback: use last known frame data
                frame = draw_skeleton_on_frame(frame, last_frame_data)

                if show_info:
                    text = f"Frame: {frame_idx}/{total_frames} | Using cached data"
                    cv2.putText(frame, text, (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
            else:
                # No data available at all
                if show_info:
                    cv2.putText(frame, f"Frame: {frame_idx} | No pose data", (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Write frame
        out.write(frame)

        # Progress indicator
        if frame_idx % 30 == 0:
            progress = (frame_idx / total_frames) * 100
            print(f"Progress: {progress:.1f}% ({frame_idx}/{total_frames})")

        frame_idx += 1

    # Cleanup
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"\n✅ Skeleton overlay video created: {output_path}")
    print(f"   Processed {frame_idx} frames")

    return output_path

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Create video with pose skeleton overlay'
    )

    parser.add_argument(
        '--video',
        default='video/dance.mp4',
        help='Path to original video (default: video/dance.mp4)'
    )

    parser.add_argument(
        '--csv',
        default='creative_output/dance_poses.csv',
        help='Path to pose data CSV (default: creative_output/dance_poses.csv)'
    )

    parser.add_argument(
        '--output',
        default='creative_output/dance_skeleton_overlay.mp4',
        help='Output video path (default: creative_output/dance_skeleton_overlay.mp4)'
    )

    parser.add_argument(
        '--no-info',
        action='store_true',
        help='Hide frame info overlay'
    )

    args = parser.parse_args()

    # Check if files exist
    if not Path(args.video).exists():
        print(f"❌ Video file not found: {args.video}")
        sys.exit(1)

    if not Path(args.csv).exists():
        print(f"❌ CSV file not found: {args.csv}")
        sys.exit(1)

    # Create output directory if needed
    output_dir = Path(args.output).parent
    output_dir.mkdir(exist_ok=True)

    print("="*60)
    print("🎥 SKELETON OVERLAY VIDEO GENERATOR")
    print("="*60)
    print(f"Video:  {args.video}")
    print(f"Poses:  {args.csv}")
    print(f"Output: {args.output}")
    print("="*60)

    # Create the overlay video
    create_overlay_video(
        video_path=args.video,
        csv_path=args.csv,
        output_path=args.output,
        show_info=not args.no_info
    )

if __name__ == "__main__":
    main()