#!/usr/bin/env python
"""
Targeted fix for rotation tracking issues - reprocess specific problem frames.
"""

import cv2
import numpy as np
import pandas as pd
import mediapipe as mp
from pathlib import Path

def identify_rotation_failures(csv_path: str):
    """
    Identify frames where rotation tracking likely failed.
    """
    df = pd.read_csv(csv_path)

    problem_frames = []

    for frame_id in df['frame_id'].unique():
        frame_data = df[df['frame_id'] == frame_id]

        # Check shoulder width - narrow = likely profile
        left_shoulder = frame_data[frame_data['landmark_id'] == 11]
        right_shoulder = frame_data[frame_data['landmark_id'] == 12]

        if not left_shoulder.empty and not right_shoulder.empty:
            shoulder_width = abs(right_shoulder.iloc[0]['x'] - left_shoulder.iloc[0]['x'])

            # Check hip width too
            left_hip = frame_data[frame_data['landmark_id'] == 23]
            right_hip = frame_data[frame_data['landmark_id'] == 24]
            hip_width = abs(right_hip.iloc[0]['x'] - left_hip.iloc[0]['x'])

            # Problem: narrow shoulders but wide hips (or vice versa) = incorrect detection
            width_ratio = shoulder_width / (hip_width + 0.001)  # Avoid division by zero

            # Suspicious if ratio is way off (should be close to 1.0-1.5)
            if width_ratio < 0.7 or width_ratio > 2.0:
                problem_frames.append(frame_id)

            # Also check if both are very narrow (profile) but confidence is high (wrong)
            elif shoulder_width < 0.15 and hip_width < 0.12:
                avg_conf = frame_data['visibility'].mean()
                if avg_conf > 0.8:  # High confidence but narrow = likely wrong
                    problem_frames.append(frame_id)

        # NEW: Check for crossed arms
        left_wrist = frame_data[frame_data['landmark_id'] == 15]
        right_wrist = frame_data[frame_data['landmark_id'] == 16]
        left_elbow = frame_data[frame_data['landmark_id'] == 13]
        right_elbow = frame_data[frame_data['landmark_id'] == 14]

        if not any([left_wrist.empty, right_wrist.empty, left_elbow.empty, right_elbow.empty]):
            # Check if wrists are crossed (left wrist on right side)
            if left_wrist.iloc[0]['x'] > right_wrist.iloc[0]['x']:
                problem_frames.append(frame_id)
            # Check if elbows are crossed
            elif left_elbow.iloc[0]['x'] > right_elbow.iloc[0]['x']:
                problem_frames.append(frame_id)
            # Check for arms very close together (possible occlusion)
            elif abs(left_wrist.iloc[0]['x'] - right_wrist.iloc[0]['x']) < 0.05:
                problem_frames.append(frame_id)

    return problem_frames

def reprocess_frames_with_static_detection(video_path: str, frame_numbers: list):
    """
    Reprocess specific frames using static detection (no tracking).
    """
    cap = cv2.VideoCapture(video_path)
    mp_pose = mp.solutions.pose

    # Use static mode - treats each frame independently
    pose_static = mp_pose.Pose(
        static_image_mode=True,  # KEY: No tracking between frames
        model_complexity=2,       # Best model
        min_detection_confidence=0.2,  # Lower threshold
        min_tracking_confidence=0.2
    )

    reprocessed_data = []

    for frame_id in frame_numbers:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()

        if ret:
            # Try multiple strategies
            strategies = [
                ('original', frame),
                ('enhanced', enhance_frame(frame)),
                ('mirrored', cv2.flip(frame, 1)),
            ]

            best_result = None
            best_score = 0

            for strategy_name, processed_frame in strategies:
                rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                results = pose_static.process(rgb_frame)

                if results.pose_landmarks:
                    # Score based on visibility and anatomical plausibility
                    score = calculate_pose_score(results.pose_landmarks)

                    if score > best_score:
                        best_score = score
                        best_result = results.pose_landmarks
                        best_strategy = strategy_name

            if best_result:
                # Convert to dataframe format
                for idx, landmark in enumerate(best_result.landmark):
                    x = landmark.x
                    if best_strategy == 'mirrored':
                        x = 1.0 - x  # Flip back

                    reprocessed_data.append({
                        'frame_id': frame_id,
                        'landmark_id': idx,
                        'x': x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility,
                        'reprocessed': True,
                        'strategy': best_strategy
                    })

    pose_static.close()
    cap.release()

    return pd.DataFrame(reprocessed_data)

def enhance_frame(frame):
    """Apply enhancement for better detection."""
    # Increase contrast
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    return enhanced

def calculate_pose_score(landmarks):
    """Calculate quality score for pose detection."""
    # Average visibility
    avg_vis = np.mean([lm.visibility for lm in landmarks.landmark])

    # Check key points visibility
    key_points = [0, 11, 12, 23, 24]  # nose, shoulders, hips
    key_vis = np.mean([landmarks.landmark[i].visibility for i in key_points])

    # Check anatomical plausibility (shoulders should be above hips)
    shoulder_y = (landmarks.landmark[11].y + landmarks.landmark[12].y) / 2
    hip_y = (landmarks.landmark[23].y + landmarks.landmark[24].y) / 2

    plausible = 1.0 if shoulder_y < hip_y else 0.5

    return avg_vis * 0.5 + key_vis * 0.3 + plausible * 0.2

def apply_targeted_fix(csv_path: str, video_path: str, output_path: str):
    """
    Apply targeted fix to rotation tracking issues.
    """
    print("🎯 Applying Targeted Rotation Fix")
    print("="*60)

    # Step 1: Identify problem frames
    print("Step 1: Identifying rotation tracking failures...")
    problem_frames = identify_rotation_failures(csv_path)

    # Focus on known problem areas
    # Frames 0-10: Crossed arms at beginning
    problem_frames.extend(range(0, 11))
    # Frames 40-60: Fast rotation
    problem_frames.extend(range(40, 61))
    problem_frames = sorted(list(set(problem_frames)))

    print(f"  Found {len(problem_frames)} frames to reprocess")
    if len(problem_frames) > 20:
        print(f"  Sample frames: {problem_frames[:10]}...{problem_frames[-5:]}")
    else:
        print(f"  Frames: {problem_frames}")

    # Step 2: Reprocess with static detection
    print("\nStep 2: Reprocessing with static detection (no tracking)...")
    reprocessed_df = reprocess_frames_with_static_detection(video_path, problem_frames)

    # Step 3: Merge with original data
    print("\nStep 3: Merging reprocessed data...")
    original_df = pd.read_csv(csv_path)

    # Remove old data for reprocessed frames
    df_fixed = original_df[~original_df['frame_id'].isin(problem_frames)].copy()

    # Add reprocessed data
    df_fixed = pd.concat([df_fixed, reprocessed_df], ignore_index=True)
    df_fixed = df_fixed.sort_values(['frame_id', 'landmark_id'])

    # Step 4: Apply temporal smoothing
    print("\nStep 4: Applying temporal smoothing...")
    df_fixed = apply_selective_smoothing(df_fixed, problem_frames)

    # Save result
    df_fixed.to_csv(output_path, index=False)
    print(f"\n✅ Fixed data saved to: {output_path}")

    # Report improvements
    strategies = reprocessed_df['strategy'].value_counts() if 'strategy' in reprocessed_df else {}
    print(f"\n📊 Reprocessing Statistics:")
    for strategy, count in strategies.items():
        print(f"  {strategy}: {count} landmarks")

    return df_fixed

def apply_selective_smoothing(df, reprocessed_frames, window=5):
    """
    Apply smoothing only around reprocessed frames.
    """
    from scipy.signal import savgol_filter

    df_smooth = df.copy()

    for landmark_id in range(33):
        landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')

        if len(landmark_data) > window:
            x_values = landmark_data['x'].values
            y_values = landmark_data['y'].values

            # Create weight mask (lower weight for reprocessed frames)
            weights = np.ones(len(x_values))
            for i, frame_id in enumerate(landmark_data['frame_id'].values):
                if frame_id in reprocessed_frames:
                    # Smooth transition around reprocessed frames
                    for j in range(max(0, i-2), min(len(weights), i+3)):
                        weights[j] *= 0.7

            # Apply weighted smoothing
            if len(x_values) > window:
                window_length = min(window, len(x_values))
                if window_length % 2 == 0:
                    window_length -= 1
                if window_length >= 3:
                    x_smooth = savgol_filter(x_values, window_length, 2)
                    y_smooth = savgol_filter(y_values, window_length, 2)

                    # Apply weighted blend
                    x_final = x_values * (1 - weights) + x_smooth * weights
                    y_final = y_values * (1 - weights) + y_smooth * weights

                    # Update dataframe
                    for i, frame_id in enumerate(landmark_data['frame_id'].values):
                        df_smooth.loc[(df_smooth['frame_id'] == frame_id) &
                                    (df_smooth['landmark_id'] == landmark_id), 'x'] = x_final[i]
                        df_smooth.loc[(df_smooth['frame_id'] == frame_id) &
                                    (df_smooth['landmark_id'] == landmark_id), 'y'] = y_final[i]

    return df_smooth

if __name__ == "__main__":
    apply_targeted_fix(
        'creative_output/dance_poses.csv',
        'video/dance.mp4',
        'creative_output/dance_poses_rotation_targeted.csv'
    )