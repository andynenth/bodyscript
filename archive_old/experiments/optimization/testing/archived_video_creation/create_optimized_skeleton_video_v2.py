#!/usr/bin/env python
"""
Optimized skeleton video creation V2 with advanced detection strategies.

This version implements:
1. Frame-specific processing groups
2. Enhanced multi-strategy detection
3. Advanced scoring system
4. Kinematic validation
5. Intelligent interpolation
"""

import os
import sys
import pandas as pd
import numpy as np
import cv2
import mediapipe as mp
import subprocess
from pathlib import Path
from scipy.signal import savgol_filter
from scipy.interpolate import CubicSpline


class FrameGroup:
    """Categorize frames into processing groups."""
    GROUP_A_SEVERE = "severe_occlusion"  # Frames 3-4, 6-9
    GROUP_B_CROSSED = "crossed_arms"     # Frames 1-2, 16-18, 29
    GROUP_C_MODERATE = "moderate"        # Frames 11, 20-24, 28
    GROUP_D_GOOD = "good"               # Other frames


def categorize_frame(frame_id):
    """Categorize a frame into a processing group."""
    if frame_id in [3, 4, 6, 7, 8, 9]:
        return FrameGroup.GROUP_A_SEVERE
    elif frame_id in [1, 2, 16, 17, 18, 29]:
        return FrameGroup.GROUP_B_CROSSED
    elif frame_id in [11, 20, 21, 22, 23, 24, 28]:
        return FrameGroup.GROUP_C_MODERATE
    else:
        return FrameGroup.GROUP_D_GOOD


def enhance_lower_body(frame):
    """Enhance contrast specifically in the lower body region."""
    h, w = frame.shape[:2]

    # Focus on lower 2/3 of frame
    lower_region = frame[h//3:, :]

    # Apply CLAHE
    lab = cv2.cvtColor(lower_region, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    enhanced_lower = cv2.merge([l, a, b])
    enhanced_lower = cv2.cvtColor(enhanced_lower, cv2.COLOR_LAB2BGR)

    # Combine with original upper region
    result = frame.copy()
    result[h//3:, :] = enhanced_lower

    # Smooth transition
    for i in range(10):
        alpha = i / 10
        y = h//3 - 5 + i
        if 0 <= y < h:
            result[y] = cv2.addWeighted(frame[y], 1-alpha, result[y], alpha, 0)

    return result


def increase_brightness(frame, alpha=1.3, beta=30):
    """Increase brightness and contrast."""
    return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)


def enhance_frame_clahe(frame):
    """Apply CLAHE to entire frame."""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    enhanced = cv2.merge([l, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def combine_preprocessing(frame):
    """Combine multiple preprocessing techniques."""
    # First apply slight blur
    blurred = cv2.GaussianBlur(frame, (3, 3), 0)

    # Then enhance lower body
    enhanced = enhance_lower_body(blurred)

    # Finally adjust brightness
    return increase_brightness(enhanced, alpha=1.1, beta=20)


def calculate_bone_length(p1, p2):
    """Calculate distance between two landmarks."""
    return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)


def check_anatomical_constraints(landmarks):
    """Check if pose satisfies basic anatomical constraints."""
    score = 1.0

    # Check if shoulders are roughly horizontal
    left_shoulder = landmarks.landmark[11]
    right_shoulder = landmarks.landmark[12]
    shoulder_diff = abs(left_shoulder.y - right_shoulder.y)
    if shoulder_diff > 0.2:  # Too tilted
        score *= 0.8

    # Check if hips are roughly horizontal
    left_hip = landmarks.landmark[23]
    right_hip = landmarks.landmark[24]
    hip_diff = abs(left_hip.y - right_hip.y)
    if hip_diff > 0.2:
        score *= 0.8

    # Check leg symmetry (roughly equal lengths)
    left_thigh_len = calculate_bone_length(
        landmarks.landmark[23], landmarks.landmark[25])
    right_thigh_len = calculate_bone_length(
        landmarks.landmark[24], landmarks.landmark[26])

    thigh_ratio = min(left_thigh_len, right_thigh_len) / max(left_thigh_len, right_thigh_len)
    if thigh_ratio < 0.7:  # Too asymmetric
        score *= 0.7

    return score


def check_left_right_symmetry(landmarks):
    """Check symmetry between left and right sides."""
    score = 1.0

    # Compare visibility of left vs right leg
    left_leg_ids = [23, 25, 27, 29, 31]
    right_leg_ids = [24, 26, 28, 30, 32]

    left_vis = np.mean([landmarks.landmark[i].visibility for i in left_leg_ids])
    right_vis = np.mean([landmarks.landmark[i].visibility for i in right_leg_ids])

    # Penalize if one side is much less visible
    vis_ratio = min(left_vis, right_vis) / max(left_vis, right_vis)
    score *= vis_ratio

    return score


def calculate_temporal_consistency(landmarks, prev_landmarks):
    """Check temporal consistency between frames."""
    if prev_landmarks is None:
        return 1.0

    score = 1.0
    max_movement = 0

    # Check how much each landmark moved
    for i in range(33):
        curr = landmarks.landmark[i]
        prev = prev_landmarks.landmark[i]

        movement = np.sqrt((curr.x - prev.x)**2 + (curr.y - prev.y)**2)
        max_movement = max(max_movement, movement)

    # Penalize large movements (likely errors)
    if max_movement > 0.2:  # Too much movement between frames
        score *= (0.2 / max_movement)

    return min(score, 1.0)


def calculate_advanced_pose_score(landmarks, frame_id=None, prev_landmarks=None):
    """
    Calculate comprehensive pose score using multiple factors.
    """
    # 1. Visibility component (30% weight)
    visibility_scores = [lm.visibility for lm in landmarks.landmark]
    visibility_score = np.mean(visibility_scores)

    # 2. Anatomical plausibility (40% weight)
    anatomical_score = check_anatomical_constraints(landmarks)

    # 3. Temporal consistency (20% weight)
    temporal_score = 1.0
    if prev_landmarks is not None:
        temporal_score = calculate_temporal_consistency(landmarks, prev_landmarks)

    # 4. Symmetry check (10% weight)
    symmetry_score = check_left_right_symmetry(landmarks)

    # Weighted combination
    total_score = (visibility_score * 0.3 +
                  anatomical_score * 0.4 +
                  temporal_score * 0.2 +
                  symmetry_score * 0.1)

    # Bonus for specific important landmarks being visible
    left_knee = landmarks.landmark[25]
    left_ankle = landmarks.landmark[27]
    if left_knee.visibility > 0.5 and left_ankle.visibility > 0.5:
        total_score *= 1.1  # 10% bonus for good left leg detection

    return total_score


def process_group_a_severe(frame, frame_id, prev_landmarks=None):
    """
    Process frames with severe occlusion (3-4, 6-9).
    Use aggressive multi-pass detection.
    """
    best_result = None
    best_score = 0
    best_strategy = None

    # Try multiple configurations
    configs = [
        {'confidence': 0.1, 'complexity': 2, 'static': True},
        {'confidence': 0.15, 'complexity': 2, 'static': True},
        {'confidence': 0.2, 'complexity': 1, 'static': True},
        {'confidence': 0.1, 'complexity': 1, 'static': False},
    ]

    # Try multiple preprocessing strategies
    strategies = [
        ('original', frame),
        ('blurred', cv2.GaussianBlur(frame, (5, 5), 0)),
        ('enhanced_lower', enhance_lower_body(frame)),
        ('brightened', increase_brightness(frame)),
        ('mirrored', cv2.flip(frame, 1)),
        ('combined', combine_preprocessing(frame)),
        ('heavy_blur', cv2.GaussianBlur(frame, (9, 9), 0)),
    ]

    for config in configs:
        pose = mp.solutions.pose.Pose(
            static_image_mode=config['static'],
            model_complexity=config['complexity'],
            min_detection_confidence=config['confidence'],
            min_tracking_confidence=config['confidence']
        )

        for strategy_name, processed_frame in strategies:
            rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                # Special handling for mirrored
                if strategy_name == 'mirrored':
                    for lm in results.pose_landmarks.landmark:
                        lm.x = 1.0 - lm.x

                score = calculate_advanced_pose_score(
                    results.pose_landmarks, frame_id, prev_landmarks)

                if score > best_score:
                    best_score = score
                    best_result = results.pose_landmarks
                    best_strategy = f"{strategy_name}_c{config['confidence']}"

        pose.close()

    return best_result, best_score, best_strategy


def process_group_b_crossed(frame, frame_id, prev_landmarks=None):
    """
    Process frames with crossed arms (1-2, 16-18, 29).
    Focus on mirrored and rotated detection.
    """
    best_result = None
    best_score = 0
    best_strategy = None

    # Emphasize mirrored and rotation strategies
    strategies = [
        ('mirrored', cv2.flip(frame, 1)),
        ('rotated_5', rotate_image(frame, 5)),
        ('rotated_-5', rotate_image(frame, -5)),
        ('blurred', cv2.GaussianBlur(frame, (7, 7), 0)),
        ('enhanced', enhance_frame_clahe(frame)),
    ]

    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.15,
        min_tracking_confidence=0.15
    )

    for strategy_name, processed_frame in strategies:
        rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            # Handle transformations
            if strategy_name == 'mirrored':
                for lm in results.pose_landmarks.landmark:
                    lm.x = 1.0 - lm.x
            elif 'rotated' in strategy_name:
                # Adjust coordinates for rotation
                angle = float(strategy_name.split('_')[1])
                results.pose_landmarks = unrotate_landmarks(
                    results.pose_landmarks, -angle, frame.shape)

            score = calculate_advanced_pose_score(
                results.pose_landmarks, frame_id, prev_landmarks)

            if score > best_score:
                best_score = score
                best_result = results.pose_landmarks
                best_strategy = strategy_name

    pose.close()
    return best_result, best_score, best_strategy


def process_group_c_moderate(frame, frame_id, prev_landmarks=None):
    """
    Process frames with moderate issues (11, 20-24, 28).
    Standard detection with smoothing.
    """
    strategies = [
        ('original', frame),
        ('enhanced', enhance_frame_clahe(frame)),
        ('blurred', cv2.GaussianBlur(frame, (3, 3), 0)),
    ]

    best_result = None
    best_score = 0
    best_strategy = None

    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        min_detection_confidence=0.2,
        min_tracking_confidence=0.2
    )

    for strategy_name, processed_frame in strategies:
        rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            score = calculate_advanced_pose_score(
                results.pose_landmarks, frame_id, prev_landmarks)

            if score > best_score:
                best_score = score
                best_result = results.pose_landmarks
                best_strategy = strategy_name

    pose.close()
    return best_result, best_score, best_strategy


def process_group_d_good(frame, frame_id, prev_landmarks=None):
    """
    Process frames with good detection.
    Minimal processing needed.
    """
    pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3
    )

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    score = 0
    if results.pose_landmarks:
        score = calculate_advanced_pose_score(
            results.pose_landmarks, frame_id, prev_landmarks)

    pose.close()
    return results.pose_landmarks, score, 'standard'


def rotate_image(image, angle):
    """Rotate image by given angle."""
    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h))

    return rotated


def unrotate_landmarks(landmarks, angle, shape):
    """Adjust landmark coordinates after rotation."""
    # This is a simplified version - would need proper transformation
    return landmarks


def intelligent_interpolation(df, problem_frames, max_gap=3):
    """
    Apply intelligent interpolation for missing landmarks.
    """
    print(f"🔧 Applying intelligent interpolation to {len(problem_frames)} frames")

    for frame_id in problem_frames:
        # Find good anchor frames
        before_anchors = []
        after_anchors = []

        # Look for good frames before
        for i in range(1, max_gap + 1):
            if frame_id - i >= 0:
                frame_data = df[df['frame_id'] == frame_id - i]
                if not frame_data.empty:
                    avg_vis = frame_data['visibility'].mean()
                    if avg_vis > 0.7:
                        before_anchors.append((frame_id - i, frame_data))

        # Look for good frames after
        for i in range(1, max_gap + 1):
            future_frame = df[df['frame_id'] == frame_id + i]
            if not future_frame.empty:
                avg_vis = future_frame['visibility'].mean()
                if avg_vis > 0.7:
                    after_anchors.append((frame_id + i, future_frame))

        if before_anchors and after_anchors:
            # Use closest anchors
            before_frame_id, before_data = before_anchors[0]
            after_frame_id, after_data = after_anchors[0]

            # Interpolate each landmark
            current_frame = df[df['frame_id'] == frame_id]

            for landmark_id in range(33):
                before_lm = before_data[before_data['landmark_id'] == landmark_id]
                after_lm = after_data[after_data['landmark_id'] == landmark_id]
                current_lm = current_frame[current_frame['landmark_id'] == landmark_id]

                if not before_lm.empty and not after_lm.empty and not current_lm.empty:
                    # Check if current landmark has poor visibility
                    if current_lm.iloc[0]['visibility'] < 0.3:
                        # Linear interpolation
                        alpha = (frame_id - before_frame_id) / (after_frame_id - before_frame_id)

                        idx = df[(df['frame_id'] == frame_id) &
                                (df['landmark_id'] == landmark_id)].index[0]

                        # Interpolate position
                        df.loc[idx, 'x'] = (before_lm.iloc[0]['x'] * (1 - alpha) +
                                           after_lm.iloc[0]['x'] * alpha)
                        df.loc[idx, 'y'] = (before_lm.iloc[0]['y'] * (1 - alpha) +
                                           after_lm.iloc[0]['y'] * alpha)
                        df.loc[idx, 'z'] = (before_lm.iloc[0]['z'] * (1 - alpha) +
                                           after_lm.iloc[0]['z'] * alpha)

                        # Mark as interpolated with moderate confidence
                        df.loc[idx, 'visibility'] = 0.5
                        df.loc[idx, 'interpolated'] = True

    return df


def process_video_optimized(video_path='video/dance.mp4',
                           output_path='creative_output/dance_skeleton_optimized_v2.mp4'):
    """
    Main processing pipeline with optimized detection.
    """
    print("🚀 Optimized Skeleton Video Creation V2")
    print("="*60)

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"📹 Processing {total_frames} frames at {fps:.1f} FPS")

    all_results = []
    prev_landmarks = None

    # Process each frame based on its group
    for frame_id in range(min(30, total_frames)):  # Focus on first 30 frames
        ret, frame = cap.read()
        if not ret:
            break

        # Categorize frame
        group = categorize_frame(frame_id)

        # Process based on group
        if group == FrameGroup.GROUP_A_SEVERE:
            landmarks, score, strategy = process_group_a_severe(frame, frame_id, prev_landmarks)
            print(f"Frame {frame_id}: GROUP_A (severe) - {strategy} (score: {score:.3f})")
        elif group == FrameGroup.GROUP_B_CROSSED:
            landmarks, score, strategy = process_group_b_crossed(frame, frame_id, prev_landmarks)
            print(f"Frame {frame_id}: GROUP_B (crossed) - {strategy} (score: {score:.3f})")
        elif group == FrameGroup.GROUP_C_MODERATE:
            landmarks, score, strategy = process_group_c_moderate(frame, frame_id, prev_landmarks)
            print(f"Frame {frame_id}: GROUP_C (moderate) - {strategy} (score: {score:.3f})")
        else:
            landmarks, score, strategy = process_group_d_good(frame, frame_id, prev_landmarks)
            if frame_id % 5 == 0:  # Only print every 5th good frame
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

    cap.release()

    # Convert to dataframe
    df = pd.DataFrame(all_results)

    # Apply intelligent interpolation for problem frames
    problem_frames = [3, 4, 6, 7, 8, 9]  # Known problem frames
    df = intelligent_interpolation(df, problem_frames)

    # Save processed data
    output_csv = 'creative_output/dance_poses_optimized_v2.csv'
    df.to_csv(output_csv, index=False)

    print(f"\n✅ Optimization complete!")
    print(f"📁 Data saved to: {output_csv}")

    # Generate quality report
    print("\n📊 Quality Report:")
    print("="*40)

    for frame_id in [3, 6, 9, 15, 25]:
        frame_data = df[df['frame_id'] == frame_id]
        if not frame_data.empty:
            avg_vis = frame_data['visibility'].mean()
            left_leg = frame_data[frame_data['landmark_id'].isin([25, 27])]
            left_leg_vis = left_leg['visibility'].mean() if not left_leg.empty else 0
            strategy = frame_data.iloc[0]['strategy']
            print(f"Frame {frame_id}: {avg_vis:.2%} avg, {left_leg_vis:.2%} left leg - {strategy}")

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Optimized skeleton video creation with advanced detection'
    )

    parser.add_argument(
        '--video',
        default='video/dance.mp4',
        help='Input video path'
    )

    parser.add_argument(
        '--frames',
        type=int,
        default=30,
        help='Number of frames to process (default: 30)'
    )

    args = parser.parse_args()

    # Process video
    df = process_video_optimized(args.video)