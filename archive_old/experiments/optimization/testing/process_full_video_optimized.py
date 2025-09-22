#!/usr/bin/env python
"""
Process full video with optimized detection, extending the successful
approach from frames 1-30 to the entire video.
"""

import pandas as pd
import numpy as np
import cv2
import mediapipe as mp
import subprocess
from pathlib import Path
import sys
sys.path.append('.')

# Import the optimized processing functions
from create_optimized_skeleton_video_v2 import (
    categorize_frame,
    process_group_a_severe,
    process_group_b_crossed,
    process_group_c_moderate,
    process_group_d_good,
    intelligent_interpolation,
    FrameGroup
)


def extend_frame_categorization(frame_id):
    """
    Extend categorization beyond frame 30 based on patterns.
    For frames 31-404, use targeted rotation fix for known problem areas.
    """
    # Original categorization for frames 0-30
    if frame_id <= 30:
        return categorize_frame(frame_id)

    # Rotation problem frames (40-60) need special handling
    elif 40 <= frame_id <= 60:
        return FrameGroup.GROUP_A_SEVERE  # Use aggressive detection

    # Most other frames should be good
    else:
        return FrameGroup.GROUP_D_GOOD


def process_full_video(video_path='video/dance.mp4'):
    """
    Process the entire video using optimized detection.
    """
    print("🚀 Processing Full Video with Optimized Detection")
    print("="*60)

    # First, check if we already have data for frames 0-30
    optimized_csv = 'creative_output/dance_poses_optimized_v2.csv'

    if Path(optimized_csv).exists():
        print("✓ Loading existing optimized data for frames 0-30")
        df_existing = pd.read_csv(optimized_csv)
        start_frame = 30
    else:
        df_existing = pd.DataFrame()
        start_frame = 0

    # Open video
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"📹 Processing frames {start_frame}-{total_frames} at {fps:.1f} FPS")

    all_results = []
    prev_landmarks = None

    # If we have existing data, get the last landmarks for continuity
    if not df_existing.empty:
        last_frame = df_existing[df_existing['frame_id'] == 29]
        if not last_frame.empty:
            # Create a mock landmarks object from the data
            class MockLandmarks:
                def __init__(self, df_frame):
                    self.landmark = []
                    for i in range(33):
                        lm_data = df_frame[df_frame['landmark_id'] == i]
                        if not lm_data.empty:
                            class MockLandmark:
                                def __init__(self, row):
                                    self.x = row['x']
                                    self.y = row['y']
                                    self.z = row['z']
                                    self.visibility = row['visibility']
                            self.landmark.append(MockLandmark(lm_data.iloc[0]))

            prev_landmarks = MockLandmarks(last_frame)

    # Process remaining frames
    for frame_id in range(start_frame, total_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()

        if not ret:
            break

        # Categorize frame
        group = extend_frame_categorization(frame_id)

        # Process based on group
        if group == FrameGroup.GROUP_A_SEVERE:
            landmarks, score, strategy = process_group_a_severe(frame, frame_id, prev_landmarks)
            if frame_id % 10 == 0 or frame_id <= 60:
                print(f"Frame {frame_id}: GROUP_A (severe) - {strategy} (score: {score:.3f})")
        elif group == FrameGroup.GROUP_B_CROSSED:
            landmarks, score, strategy = process_group_b_crossed(frame, frame_id, prev_landmarks)
            print(f"Frame {frame_id}: GROUP_B (crossed) - {strategy} (score: {score:.3f})")
        elif group == FrameGroup.GROUP_C_MODERATE:
            landmarks, score, strategy = process_group_c_moderate(frame, frame_id, prev_landmarks)
            if frame_id % 20 == 0:
                print(f"Frame {frame_id}: GROUP_C (moderate) - {strategy} (score: {score:.3f})")
        else:
            landmarks, score, strategy = process_group_d_good(frame, frame_id, prev_landmarks)
            if frame_id % 50 == 0:
                print(f"Frame {frame_id}: GROUP_D (good) - {strategy} (score: {score:.3f})")

        # Store results
        if landmarks:
            for idx, lm in enumerate(landmarks.landmark):
                all_results.append({
                    'frame_id': frame_id,
                    'landmark_id': idx,
                    'x': lm.x,
                    'y': lm.y,
                    'z': lm.z,
                    'visibility': lm.visibility,
                    'score': score,
                    'strategy': strategy,
                    'interpolated': False
                })
            prev_landmarks = landmarks

        # Progress update
        if frame_id % 30 == 0:
            progress = (frame_id / total_frames) * 100
            print(f"  Progress: {progress:.1f}% ({frame_id}/{total_frames})")

    cap.release()

    # Convert to dataframe
    df_new = pd.DataFrame(all_results)

    # Combine with existing data
    if not df_existing.empty:
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    # Apply intelligent interpolation for known problem areas
    problem_frames = list(range(3, 10)) + list(range(40, 61))  # Known problem areas
    print(f"\n🔧 Applying interpolation to {len(problem_frames)} problem frames")
    df_combined = intelligent_interpolation(df_combined, problem_frames)

    # Save complete data
    output_csv = 'creative_output/dance_poses_optimized_full.csv'
    df_combined.to_csv(output_csv, index=False)

    print(f"\n✅ Full video processing complete!")
    print(f"📁 Data saved to: {output_csv}")

    # Generate quality report
    print("\n📊 Quality Report:")
    print("="*40)

    for frame_id in [3, 30, 50, 100, 200, 300, 400]:
        frame_data = df_combined[df_combined['frame_id'] == frame_id]
        if not frame_data.empty:
            avg_vis = frame_data['visibility'].mean()
            left_leg = frame_data[frame_data['landmark_id'].isin([25, 27])]
            left_leg_vis = left_leg['visibility'].mean() if not left_leg.empty else 0
            strategy = frame_data.iloc[0]['strategy'] if 'strategy' in frame_data else 'unknown'
            print(f"Frame {frame_id}: {avg_vis:.2%} avg, {left_leg_vis:.2%} left leg - {strategy}")

    return df_combined


def create_full_skeleton_video(csv_path='creative_output/dance_poses_optimized_full.csv',
                               video_path='video/dance.mp4',
                               output_path='creative_output/dance_skeleton_optimized_full.mp4'):
    """
    Create the complete skeleton overlay video.
    """
    print("\n🎬 Creating Full Skeleton Overlay Video")
    print("="*60)

    # Use the existing create_skeleton_video.py script
    result = subprocess.run([
        'python', 'create_skeleton_video.py',
        '--csv', csv_path,
        '--output', output_path
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Video created successfully: {output_path}")
        return True
    else:
        print(f"❌ Video creation failed: {result.stderr}")
        return False


if __name__ == "__main__":
    # Process full video
    df = process_full_video()

    # Create skeleton overlay
    success = create_full_skeleton_video()

    if success:
        print("\n" + "="*60)
        print("🏆 COMPLETE!")
        print("="*60)
        print("📁 Output files:")
        print("  • Data: creative_output/dance_poses_optimized_full.csv")
        print("  • Video: creative_output/dance_skeleton_optimized_full.mp4")
        print("\n💡 The optimized version includes:")
        print("  • Frame-specific detection strategies")
        print("  • Enhanced processing for problem areas")
        print("  • Intelligent interpolation")
        print("  • Temporal consistency")