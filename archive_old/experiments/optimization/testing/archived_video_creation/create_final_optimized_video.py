#!/usr/bin/env python
"""
Final optimized video creation that combines:
1. Best detection from targeted_rotation_fix (dance_poses_best_clean.csv)
2. Gentle temporal smoothing ONLY for low confidence areas
3. Preserves accurate hand tracking
"""

import pandas as pd
import numpy as np
import cv2
import subprocess
from pathlib import Path


def selective_temporal_smoothing(csv_path: str, output_path: str):
    """
    Apply temporal smoothing ONLY where needed, preserving good detections.

    Strategy:
    - Keep original when visibility > 0.6 (good detection)
    - Apply gentle smoothing for 0.3-0.6 (medium confidence)
    - Apply stronger smoothing/prediction for < 0.3 (poor detection)
    """
    print("🎯 Selective Temporal Smoothing")
    print("="*50)

    df = pd.read_csv(csv_path)

    # Group by frame
    frames = []
    frame_ids = sorted(df['frame_id'].unique())

    # Simple moving average for smoothing
    window_size = 3

    for i, frame_id in enumerate(frame_ids):
        frame_data = df[df['frame_id'] == frame_id].copy()

        # Get window of frames for smoothing
        window_start = max(0, i - window_size // 2)
        window_end = min(len(frame_ids), i + window_size // 2 + 1)
        window_frames = frame_ids[window_start:window_end]

        # Process each landmark
        for landmark_id in range(33):
            landmark = frame_data[frame_data['landmark_id'] == landmark_id]

            if landmark.empty:
                continue

            idx = landmark.index[0]
            visibility = landmark.iloc[0]['visibility']

            # Decision based on visibility
            if visibility > 0.6:
                # Good detection - keep original (no smoothing)
                # This preserves accurate hand tracking
                pass

            elif visibility > 0.3:
                # Medium confidence - gentle smoothing
                # Get neighboring frames
                neighbors = []
                for wf in window_frames:
                    if wf != frame_id:
                        neighbor = df[(df['frame_id'] == wf) &
                                    (df['landmark_id'] == landmark_id)]
                        if not neighbor.empty and neighbor.iloc[0]['visibility'] > 0.5:
                            neighbors.append(neighbor.iloc[0])

                if neighbors:
                    # Gentle blend with neighbors
                    alpha = 0.7  # 70% original, 30% smoothed

                    avg_x = np.mean([n['x'] for n in neighbors])
                    avg_y = np.mean([n['y'] for n in neighbors])

                    frame_data.loc[idx, 'x'] = (alpha * landmark.iloc[0]['x'] +
                                               (1-alpha) * avg_x)
                    frame_data.loc[idx, 'y'] = (alpha * landmark.iloc[0]['y'] +
                                               (1-alpha) * avg_y)

                    # Slight confidence boost
                    frame_data.loc[idx, 'visibility'] = min(visibility + 0.1, 0.6)

            else:
                # Poor detection - stronger intervention
                # But check if this is a special case

                # Special handling for hands/arms when behind body
                if landmark_id in [15, 16, 17, 18, 19, 20, 21, 22]:  # Hand landmarks
                    # For hands behind body, keep low confidence
                    # Don't try to predict - it will be wrong

                    # Just boost visibility slightly for drawing
                    frame_data.loc[idx, 'visibility'] = max(visibility, 0.35)

                else:
                    # For other landmarks, try interpolation
                    neighbors = []
                    for wf in window_frames:
                        if wf != frame_id:
                            neighbor = df[(df['frame_id'] == wf) &
                                        (df['landmark_id'] == landmark_id)]
                            if not neighbor.empty and neighbor.iloc[0]['visibility'] > 0.4:
                                neighbors.append(neighbor.iloc[0])

                    if len(neighbors) >= 2:
                        # Interpolate
                        avg_x = np.mean([n['x'] for n in neighbors])
                        avg_y = np.mean([n['y'] for n in neighbors])

                        # Check if interpolation is reasonable
                        distance = np.sqrt((avg_x - landmark.iloc[0]['x'])**2 +
                                         (avg_y - landmark.iloc[0]['y'])**2)

                        if distance < 0.2:  # Reasonable movement
                            alpha = 0.4  # Take more from interpolation
                            frame_data.loc[idx, 'x'] = (alpha * landmark.iloc[0]['x'] +
                                                       (1-alpha) * avg_x)
                            frame_data.loc[idx, 'y'] = (alpha * landmark.iloc[0]['y'] +
                                                       (1-alpha) * avg_y)

                            # Boost confidence for visualization
                            frame_data.loc[idx, 'visibility'] = 0.45

        frames.append(frame_data)

    # Combine all frames
    result = pd.concat(frames, ignore_index=True)

    # Save
    result.to_csv(output_path, index=False)

    print(f"✅ Saved to: {output_path}")

    # Report
    print("\n📊 Processing Report:")
    print(f"  High confidence (>60%): {(result['visibility'] > 0.6).sum()} landmarks")
    print(f"  Medium (30-60%): {((result['visibility'] > 0.3) & (result['visibility'] <= 0.6)).sum()} landmarks")
    print(f"  Low (<30%): {(result['visibility'] <= 0.3).sum()} landmarks")

    return result


def create_final_video_with_visualization():
    """
    Create the final optimized video with proper visualization.
    """
    print("\n🎬 Creating Final Optimized Video")
    print("="*50)

    # Step 1: Use the best detection data
    input_csv = 'creative_output/dance_poses_best_clean.csv'

    if not Path(input_csv).exists():
        # Fall back to rotation targeted
        input_csv = 'creative_output/dance_poses_rotation_targeted.csv'

        if not Path(input_csv).exists():
            print("❌ No optimized detection data found. Run targeted_rotation_fix.py first")
            return False

    print(f"✓ Using detection data: {input_csv}")

    # Step 2: Apply selective temporal smoothing
    smoothed_csv = 'creative_output/dance_poses_final_optimized.csv'
    df = selective_temporal_smoothing(input_csv, smoothed_csv)

    # Step 3: Create video with lower threshold for better visualization
    output_video = 'creative_output/dance_skeleton_FINAL.mp4'

    print("\n🎥 Generating video with optimized visualization...")

    # Use create_skeleton_video.py with custom threshold
    result = subprocess.run([
        'python', 'create_skeleton_video.py',
        '--csv', smoothed_csv,
        '--output', output_video
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Video created: {output_video}")
    else:
        # If that fails, create directly
        print("⚠️ Creating video directly...")
        create_video_direct(smoothed_csv, output_video)

    print("\n" + "="*60)
    print("🏆 FINAL OPTIMIZED VIDEO COMPLETE!")
    print("="*60)
    print(f"📁 Output: {output_video}")
    print("\nThis version combines:")
    print("  ✓ Accurate hand tracking from best detection")
    print("  ✓ Selective smoothing (only where needed)")
    print("  ✓ Preserved high-confidence detections")
    print("  ✓ Gentle interpolation for low-confidence areas")

    return True


def create_video_direct(csv_path, output_path, confidence_threshold=0.35):
    """
    Direct video creation with custom threshold.
    """
    import cv2

    df = pd.read_csv(csv_path)

    cap = cv2.VideoCapture('video/dance.mp4')
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # MediaPipe connections
    POSE_CONNECTIONS = [
        (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
        (11, 23), (12, 24), (23, 24),
        (23, 25), (25, 27), (27, 29), (29, 31), (31, 27),
        (24, 26), (26, 28), (28, 30), (30, 32), (32, 28),
        (15, 17), (15, 19), (15, 21), (16, 18), (16, 20), (16, 22),
        (17, 19), (18, 20)
    ]

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    for frame_id in range(min(frame_count, 404)):
        ret, frame = cap.read()
        if not ret:
            break

        frame_data = df[df['frame_id'] == frame_id]

        if not frame_data.empty:
            # Draw connections
            for connection in POSE_CONNECTIONS:
                start = frame_data[frame_data['landmark_id'] == connection[0]]
                end = frame_data[frame_data['landmark_id'] == connection[1]]

                if not start.empty and not end.empty:
                    start_vis = start.iloc[0]['visibility']
                    end_vis = end.iloc[0]['visibility']

                    if start_vis > confidence_threshold and end_vis > confidence_threshold:
                        x1 = int(start.iloc[0]['x'] * w)
                        y1 = int(start.iloc[0]['y'] * h)
                        x2 = int(end.iloc[0]['x'] * w)
                        y2 = int(end.iloc[0]['y'] * h)

                        avg_vis = (start_vis + end_vis) / 2

                        # Color based on confidence
                        if avg_vis > 0.7:
                            color = (0, 255, 0)  # Green - high confidence
                        elif avg_vis > 0.5:
                            color = (0, 200, 255)  # Yellow-green
                        else:
                            color = (0, 150, 255)  # Orange - smoothed/low

                        thickness = int(2 + 3 * avg_vis)
                        cv2.line(frame, (x1, y1), (x2, y2), color, thickness)

            # Draw landmarks
            for _, landmark in frame_data.iterrows():
                if landmark['visibility'] > confidence_threshold:
                    x = int(landmark['x'] * w)
                    y = int(landmark['y'] * h)
                    vis = landmark['visibility']

                    # Special color for hands
                    if landmark['landmark_id'] in [15, 16, 17, 18, 19, 20, 21, 22]:
                        color = (255, 0, 128) if vis > 0.6 else (128, 0, 255)
                    else:
                        color = (0, 0, 255) if vis > 0.6 else (0, 128, 255)

                    radius = int(3 + vis * 3)
                    cv2.circle(frame, (x, y), radius, color, -1)

            # Add info
            text = f'Frame {frame_id} | FINAL Optimized'
            cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                       0.6, (0, 255, 0), 2)

        out.write(frame)

        if frame_id % 50 == 0:
            print(f'  Processed frame {frame_id}')

    cap.release()
    out.release()

    print(f'✅ Video saved: {output_path}')


if __name__ == "__main__":
    create_final_video_with_visualization()