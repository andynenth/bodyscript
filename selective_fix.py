#!/usr/bin/env python
"""
Selective fix - only reprocess specific problem frames, keep good frames intact.
"""

import cv2
import numpy as np
import pandas as pd
import mediapipe as mp
from pathlib import Path

def selective_reprocess(video_path: str, original_csv: str, output_csv: str):
    """
    Selectively reprocess only problem frames.

    Frames 1-18: Crossed arms issue
    Frames 40-60: Rotation issue
    Everything else: Keep original
    """
    print("🎯 Selective Frame Reprocessing")
    print("="*60)

    # Load original data
    df_original = pd.read_csv(original_csv)

    # Define problem ranges
    crossed_arms_frames = list(range(1, 19))  # Frames 1-18
    rotation_frames = list(range(40, 61))     # Frames 40-60
    problem_frames = crossed_arms_frames + rotation_frames

    print(f"📊 Frame Analysis:")
    print(f"  Total frames: {df_original['frame_id'].nunique()}")
    print(f"  Frames to reprocess: {len(problem_frames)}")
    print(f"    - Crossed arms (1-18): {len(crossed_arms_frames)} frames")
    print(f"    - Rotation (40-60): {len(rotation_frames)} frames")
    print(f"  Frames to keep: {df_original['frame_id'].nunique() - len(problem_frames)}")

    # Initialize MediaPipe with static detection
    mp_pose = mp.solutions.pose
    pose_static = mp_pose.Pose(
        static_image_mode=True,  # No tracking
        model_complexity=2,       # Best model
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3
    )

    # Open video
    cap = cv2.VideoCapture(video_path)

    # Reprocess only problem frames
    reprocessed_data = []

    print("\n🔧 Reprocessing problem frames...")
    for frame_id in problem_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()

        if ret:
            # For crossed arms, try original first
            if frame_id in crossed_arms_frames:
                # Use lower confidence threshold for crossed arms
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose_static.process(rgb_frame)

                if results.pose_landmarks:
                    # Check if we got good leg detection
                    leg_landmarks = [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
                    leg_visibility = np.mean([results.pose_landmarks.landmark[i].visibility
                                             for i in leg_landmarks])

                    # If legs are poorly detected, try enhanced frame
                    if leg_visibility < 0.5:
                        enhanced = enhance_frame(frame)
                        rgb_enhanced = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
                        results_enhanced = pose_static.process(rgb_enhanced)

                        if results_enhanced.pose_landmarks:
                            leg_vis_enhanced = np.mean([results_enhanced.pose_landmarks.landmark[i].visibility
                                                       for i in leg_landmarks])
                            if leg_vis_enhanced > leg_visibility:
                                results = results_enhanced

            # For rotation frames, try multiple strategies
            elif frame_id in rotation_frames:
                best_results = None
                best_score = 0

                # Try original, enhanced, and mirrored
                for strategy, processed_frame in [
                    ('original', frame),
                    ('enhanced', enhance_frame(frame))
                ]:
                    rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    test_results = pose_static.process(rgb_frame)

                    if test_results.pose_landmarks:
                        score = calculate_pose_score(test_results.pose_landmarks)
                        if score > best_score:
                            best_score = score
                            best_results = test_results

                results = best_results

            # Convert results to dataframe format
            if results and results.pose_landmarks:
                for idx, landmark in enumerate(results.pose_landmarks.landmark):
                    reprocessed_data.append({
                        'frame_id': frame_id,
                        'landmark_id': idx,
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility
                    })

        if frame_id % 10 == 0:
            print(f"  Processed frame {frame_id}")

    pose_static.close()
    cap.release()

    # Combine data: keep original for good frames, use reprocessed for problem frames
    print("\n📊 Combining data...")

    # Get original data for good frames
    good_frames = df_original[~df_original['frame_id'].isin(problem_frames)]

    # Get reprocessed data
    df_reprocessed = pd.DataFrame(reprocessed_data)

    # Add missing columns to match original structure
    if 'bone' in df_original.columns and 'bone' not in df_reprocessed.columns:
        # Map landmark_id to bone names
        bone_map = {i: f'landmark_{i}' for i in range(33)}  # Simplified
        df_reprocessed['bone'] = df_reprocessed['landmark_id'].map(bone_map)

    # Ensure column consistency
    for col in df_original.columns:
        if col not in df_reprocessed.columns:
            if col in ['x_norm', 'y_norm', 'z_norm']:
                df_reprocessed[col] = df_reprocessed[col.replace('_norm', '')]
            else:
                df_reprocessed[col] = 0

    # Combine
    df_final = pd.concat([good_frames, df_reprocessed], ignore_index=True)
    df_final = df_final.sort_values(['frame_id', 'landmark_id'])

    # Save
    df_final.to_csv(output_csv, index=False)

    print(f"\n✅ Selective fix complete!")
    print(f"📁 Saved to: {output_csv}")

    # Report statistics
    reprocessed_frames = df_reprocessed['frame_id'].nunique() if not df_reprocessed.empty else 0
    kept_frames = good_frames['frame_id'].nunique() if not good_frames.empty else 0

    print(f"\n📈 Final Statistics:")
    print(f"  Frames kept from original: {kept_frames}")
    print(f"  Frames reprocessed: {reprocessed_frames}")
    print(f"  Success rate: {(kept_frames / df_original['frame_id'].nunique()) * 100:.1f}% preserved")

def enhance_frame(frame):
    """Simple frame enhancement."""
    # Increase contrast
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    enhanced = cv2.merge([l, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

def calculate_pose_score(landmarks):
    """Calculate quality score for pose."""
    # Average visibility
    avg_vis = np.mean([lm.visibility for lm in landmarks.landmark])

    # Check if major body parts are detected
    torso_vis = np.mean([landmarks.landmark[i].visibility for i in [11, 12, 23, 24]])
    leg_vis = np.mean([landmarks.landmark[i].visibility for i in [25, 26, 27, 28]])

    return avg_vis * 0.5 + torso_vis * 0.3 + leg_vis * 0.2

if __name__ == "__main__":
    selective_reprocess(
        video_path='video/dance.mp4',
        original_csv='creative_output/dance_poses.csv',
        output_csv='creative_output/dance_poses_selective_fix.csv'
    )