#!/usr/bin/env python
"""
Optimized skeleton video creation with targeted fixes for occlusion issues.

This version specifically addresses:
1. Frames 1-30: Self-occlusion from crossed arms causing missing left leg
2. Frames 40-60: Rotation tracking issues (already handled)
3. Overall: Better detection scoring and ensemble methods
"""

import os
import sys
import pandas as pd
import numpy as np
import subprocess
from pathlib import Path
import cv2
import mediapipe as mp

def detect_crossed_arms(df, frame_id):
    """
    Detect if arms are crossed based on wrist and elbow positions.
    """
    frame_data = df[df['frame_id'] == frame_id]
    if frame_data.empty:
        return False

    # Get arm landmarks
    left_wrist = frame_data[frame_data['landmark_id'] == 15]
    right_wrist = frame_data[frame_data['landmark_id'] == 16]
    left_elbow = frame_data[frame_data['landmark_id'] == 13]
    right_elbow = frame_data[frame_data['landmark_id'] == 14]

    if left_wrist.empty or right_wrist.empty:
        return False

    # Check if wrists are crossed (left wrist on right side and vice versa)
    midline = 0.5
    left_on_right = left_wrist['x'].values[0] > midline
    right_on_left = right_wrist['x'].values[0] < midline

    return left_on_right and right_on_left

def detect_occlusion_frames(df):
    """
    Identify frames with potential occlusion issues based on low leg visibility.
    """
    occlusion_frames = []

    # Leg landmark IDs
    left_leg_ids = [23, 25, 27, 29, 31]  # hip, knee, ankle, heel, foot

    for frame_id in df['frame_id'].unique():
        frame_data = df[df['frame_id'] == frame_id]

        # Check left leg visibility
        left_leg = frame_data[frame_data['landmark_id'].isin(left_leg_ids)]
        if not left_leg.empty:
            avg_visibility = left_leg['visibility'].mean()

            # Also check for crossed arms
            has_crossed_arms = detect_crossed_arms(df, frame_id)

            # Mark as occlusion frame if low visibility AND crossed arms
            if avg_visibility < 0.3 and has_crossed_arms:
                occlusion_frames.append(frame_id)
            # Or just very low visibility
            elif avg_visibility < 0.2:
                occlusion_frames.append(frame_id)

    return occlusion_frames

def apply_occlusion_fix(video_path, occlusion_frames, output_csv):
    """
    Apply targeted detection strategies for occluded frames.

    Strategies:
    1. Region-of-interest enhancement around hip/leg areas
    2. Multiple detection passes with different preprocessing
    3. Temporal interpolation for missing landmarks
    """

    print(f"🔧 Applying occlusion fix for {len(occlusion_frames)} frames")

    cap = cv2.VideoCapture(video_path)
    pose = mp.solutions.pose.Pose(
        static_image_mode=True,  # Treat each frame independently
        model_complexity=2,       # Maximum complexity
        min_detection_confidence=0.15,  # Lower threshold for occluded parts
        min_tracking_confidence=0.15
    )

    results = []

    for frame_id in occlusion_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()

        if not ret:
            continue

        # Strategy 1: Enhanced contrast for lower body
        enhanced_frame = enhance_lower_body(frame)

        # Strategy 2: Try multiple preprocessing approaches
        strategies = [
            ('original', frame),
            ('enhanced', enhanced_frame),
            ('brightened', cv2.convertScaleAbs(frame, alpha=1.3, beta=30)),
            ('mirrored', cv2.flip(frame, 1)),
            ('clahe', apply_clahe(frame))
        ]

        best_result = None
        best_score = 0

        for strategy_name, processed_frame in strategies:
            # Process frame
            rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            pose_results = pose.process(rgb)

            if pose_results.pose_landmarks:
                # Score based on leg visibility
                score = score_leg_detection(pose_results.pose_landmarks)

                if score > best_score:
                    best_score = score
                    best_result = (strategy_name, pose_results.pose_landmarks)

        if best_result:
            strategy_name, landmarks = best_result
            print(f"  Frame {frame_id}: Using {strategy_name} strategy (score: {best_score:.2f})")

            # If mirrored was best, need to flip x-coordinates back
            if strategy_name == 'mirrored':
                for lm in landmarks.landmark:
                    lm.x = 1.0 - lm.x

            # Store results
            for idx, lm in enumerate(landmarks.landmark):
                results.append({
                    'frame_id': frame_id,
                    'landmark_id': idx,
                    'x': lm.x,
                    'y': lm.y,
                    'z': lm.z,
                    'visibility': lm.visibility
                })

    cap.release()
    pose.close()

    # Create dataframe from results
    if results:
        df_fixed = pd.DataFrame(results)
        return df_fixed

    return pd.DataFrame()

def enhance_lower_body(frame):
    """
    Enhance contrast specifically in the lower body region.
    """
    h, w = frame.shape[:2]

    # Focus on lower 2/3 of frame where legs are
    lower_region = frame[h//3:, :]

    # Apply CLAHE to lower region
    lab = cv2.cvtColor(lower_region, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    enhanced_lower = cv2.merge([l, a, b])
    enhanced_lower = cv2.cvtColor(enhanced_lower, cv2.COLOR_LAB2BGR)

    # Combine with original upper region
    result = frame.copy()
    result[h//3:, :] = enhanced_lower

    # Smooth the transition
    transition_height = 20
    for i in range(transition_height):
        alpha = i / transition_height
        y = h//3 - transition_height//2 + i
        if 0 <= y < h:
            result[y] = cv2.addWeighted(frame[y], 1-alpha, result[y], alpha, 0)

    return result

def apply_clahe(frame):
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).
    """
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    return enhanced

def score_leg_detection(landmarks):
    """
    Score the quality of leg detection.
    """
    # Leg landmark indices
    left_leg = [23, 25, 27, 29, 31]  # hip, knee, ankle, heel, foot
    right_leg = [24, 26, 28, 30, 32]

    total_visibility = 0
    count = 0

    for idx in left_leg + right_leg:
        if idx < len(landmarks.landmark):
            visibility = landmarks.landmark[idx].visibility
            total_visibility += visibility
            count += 1

    if count > 0:
        avg_visibility = total_visibility / count

        # Bonus for having both legs detected
        left_detected = sum(1 for idx in left_leg if landmarks.landmark[idx].visibility > 0.3)
        right_detected = sum(1 for idx in right_leg if landmarks.landmark[idx].visibility > 0.3)

        completeness_bonus = (left_detected + right_detected) / 10.0

        return avg_visibility + completeness_bonus

    return 0

def interpolate_missing_landmarks(df):
    """
    Interpolate missing landmarks using temporal information.
    """
    print("📊 Interpolating missing landmarks...")

    # For each landmark
    for landmark_id in range(33):
        landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')

        if landmark_data.empty:
            continue

        # Find gaps where visibility is very low
        low_vis_frames = landmark_data[landmark_data['visibility'] < 0.2]['frame_id'].values

        for frame_id in low_vis_frames:
            # Find nearby frames with good visibility
            before = landmark_data[(landmark_data['frame_id'] < frame_id) &
                                  (landmark_data['visibility'] > 0.5)]
            after = landmark_data[(landmark_data['frame_id'] > frame_id) &
                                 (landmark_data['visibility'] > 0.5)]

            if not before.empty and not after.empty:
                # Get closest frames
                before_frame = before.iloc[-1]
                after_frame = after.iloc[0]

                # Linear interpolation
                alpha = (frame_id - before_frame['frame_id']) / \
                       (after_frame['frame_id'] - before_frame['frame_id'])

                # Update the low visibility frame
                idx = df[(df['frame_id'] == frame_id) &
                        (df['landmark_id'] == landmark_id)].index

                if len(idx) > 0:
                    df.loc[idx[0], 'x'] = before_frame['x'] * (1-alpha) + after_frame['x'] * alpha
                    df.loc[idx[0], 'y'] = before_frame['y'] * (1-alpha) + after_frame['y'] * alpha
                    df.loc[idx[0], 'z'] = before_frame['z'] * (1-alpha) + after_frame['z'] * alpha
                    df.loc[idx[0], 'visibility'] = 0.4  # Mark as interpolated

    return df

def create_optimized_skeleton_video(video_path='video/dance.mp4',
                                   output_path='creative_output/dance_skeleton_optimized.mp4'):
    """
    Create optimized skeleton video with targeted fixes for occlusion and rotation issues.

    This approach:
    1. Identifies occlusion frames (1-30) with crossed arms
    2. Applies targeted occlusion fixes
    3. Handles rotation issues (40-60) with existing fix
    4. Uses temporal interpolation for missing landmarks
    5. Creates smooth, complete skeleton overlay
    """

    print("🚀 Creating Optimized Skeleton Video")
    print("="*60)

    # Step 1: Load existing pose data
    poses_csv = 'creative_output/dance_poses.csv'

    if not Path(poses_csv).exists():
        print("📹 Running initial pose detection...")
        result = subprocess.run(['./run_creative.sh', video_path],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Initial pose detection failed")
            return False

    # Load the data
    df = pd.read_csv(poses_csv)
    print(f"✓ Loaded {len(df)} landmarks from {df['frame_id'].nunique()} frames")

    # Step 2: Identify problem frames
    print("\n🔍 Analyzing problem frames...")

    # Identify occlusion frames (crossed arms, missing legs)
    occlusion_frames = detect_occlusion_frames(df)
    occlusion_frames = [f for f in occlusion_frames if f <= 30]  # Focus on frames 1-30

    print(f"  Found {len(occlusion_frames)} occlusion frames: {occlusion_frames[:10]}...")

    # Rotation frames (already identified)
    rotation_frames = list(range(40, 61))
    print(f"  Rotation frames: {rotation_frames[0]}-{rotation_frames[-1]}")

    # Step 3: Apply occlusion fix for frames 1-30
    if occlusion_frames:
        print(f"\n🔧 Fixing occlusion issues in {len(occlusion_frames)} frames...")
        df_occlusion_fixed = apply_occlusion_fix(video_path, occlusion_frames,
                                                'creative_output/occlusion_fixed.csv')

        if not df_occlusion_fixed.empty:
            # Replace original data with fixed data for occlusion frames
            df = df[~df['frame_id'].isin(occlusion_frames)]
            df = pd.concat([df, df_occlusion_fixed], ignore_index=True)
            print(f"✅ Applied occlusion fixes")

    # Step 4: Apply rotation fix for frames 40-60
    print("\n🔧 Applying rotation fix...")
    result = subprocess.run(['python', 'targeted_rotation_fix.py'],
                          capture_output=True, text=True)

    if result.returncode == 0:
        # Load the rotation-fixed data
        rotation_fixed = pd.read_csv('creative_output/dance_poses_rotation_targeted.csv')

        # Keep only rotation frames from the fixed data
        rotation_fixed = rotation_fixed[rotation_fixed['frame_id'].isin(rotation_frames)]

        # Replace in main dataframe
        df = df[~df['frame_id'].isin(rotation_frames)]
        df = pd.concat([df, rotation_fixed], ignore_index=True)
        print("✅ Applied rotation fixes")

    # Step 5: Apply temporal interpolation
    df = interpolate_missing_landmarks(df)

    # Step 6: Final cleanup
    print("\n🧹 Final data cleanup...")

    # Sort by frame and landmark
    df = df.sort_values(['frame_id', 'landmark_id'])

    # Remove NaN values
    df['x'] = df['x'].fillna(0.5)
    df['y'] = df['y'].fillna(0.5)
    df['z'] = df['z'].fillna(0.0)
    df['visibility'] = df['visibility'].fillna(0.3)

    # Remove norm columns if present
    df = df.drop(['x_norm', 'y_norm', 'z_norm'], axis=1, errors='ignore')

    # Save optimized data
    optimized_csv = 'creative_output/dance_poses_optimized.csv'
    df.to_csv(optimized_csv, index=False)
    print(f"✓ Saved optimized data to {optimized_csv}")

    # Step 7: Create skeleton video
    print("\n🎬 Creating skeleton overlay video...")

    result = subprocess.run([
        'python', 'create_skeleton_video.py',
        '--csv', optimized_csv,
        '--output', output_path
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Video created successfully: {output_path}")
    else:
        print(f"❌ Video creation failed: {result.stderr}")
        return False

    # Step 8: Quality report
    print("\n📊 Quality Report:")
    print("="*60)

    # Overall statistics
    print(f"Total frames: {df['frame_id'].nunique()}")
    print(f"Average visibility: {df['visibility'].mean():.2%}")

    # Check specific problem areas
    print("\n🎯 Problem Area Analysis:")

    # Frames 1-30 (occlusion)
    early_frames = df[df['frame_id'].isin(range(1, 31))]
    left_leg_ids = [23, 25, 27, 29, 31]
    early_left_leg = early_frames[early_frames['landmark_id'].isin(left_leg_ids)]
    print(f"Frames 1-30 left leg visibility: {early_left_leg['visibility'].mean():.2%}")

    # Frame 3 specifically
    frame_3 = df[df['frame_id'] == 3]
    frame_3_legs = frame_3[frame_3['landmark_id'].isin(left_leg_ids)]
    print(f"Frame 3 left leg visibility: {frame_3_legs['visibility'].mean():.2%}")

    # Frames 40-60 (rotation)
    rotation_data = df[df['frame_id'].isin(rotation_frames)]
    print(f"Frames 40-60 visibility: {rotation_data['visibility'].mean():.2%}")

    # Frame 50 specifically
    frame_50 = df[df['frame_id'] == 50]
    shoulders = frame_50[frame_50['landmark_id'].isin([11, 12])]
    if len(shoulders) == 2:
        shoulder_width = abs(shoulders.iloc[0]['x'] - shoulders.iloc[1]['x'])
        print(f"Frame 50 shoulder width: {shoulder_width:.3f} {'(profile)' if shoulder_width < 0.15 else '(frontal)'}")

    print("\n✨ Optimized skeleton video complete!")
    print("="*60)

    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Create optimized skeleton video with occlusion and rotation fixes'
    )

    parser.add_argument(
        '--video',
        default='video/dance.mp4',
        help='Input video path'
    )

    parser.add_argument(
        '--output',
        default='creative_output/dance_skeleton_optimized.mp4',
        help='Output video path'
    )

    args = parser.parse_args()

    create_optimized_skeleton_video(args.video, args.output)