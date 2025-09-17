#!/usr/bin/env python
"""
Minimal fix - ONLY reprocess frames 40-60 where rotation is actually a problem.
Keep everything else from original.
"""

import cv2
import numpy as np
import pandas as pd
import mediapipe as mp
from pathlib import Path

def minimal_rotation_fix(video_path: str, original_csv: str, output_csv: str):
    """
    Minimal intervention - only fix frames 40-60 rotation issue.
    Keep ALL other frames from original.
    """
    print("🎯 Minimal Rotation Fix (Frames 40-60 ONLY)")
    print("="*60)

    # Load original data
    df_original = pd.read_csv(original_csv)

    # ONLY fix rotation frames - leave everything else alone!
    rotation_frames = list(range(40, 61))  # Just frames 40-60

    print(f"📊 Minimal Intervention:")
    print(f"  Total frames: {df_original['frame_id'].nunique()}")
    print(f"  Frames to fix: {len(rotation_frames)} (frames 40-60 only)")
    print(f"  Frames to keep: {df_original['frame_id'].nunique() - len(rotation_frames)}")
    print(f"  Preservation rate: {(1 - len(rotation_frames)/404) * 100:.1f}%")

    # Initialize MediaPipe with static detection
    mp_pose = mp.solutions.pose
    pose_static = mp_pose.Pose(
        static_image_mode=True,  # No tracking for these frames
        model_complexity=2,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3
    )

    # Open video
    cap = cv2.VideoCapture(video_path)

    # Reprocess ONLY rotation frames
    reprocessed_data = []

    print("\n🔧 Reprocessing rotation frames only...")
    for frame_id in rotation_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()

        if ret:
            # Try original frame first
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose_static.process(rgb_frame)

            # If detection is poor, try enhanced
            if results.pose_landmarks:
                avg_vis = np.mean([lm.visibility for lm in results.pose_landmarks.landmark])

                if avg_vis < 0.6:  # Try enhancement if visibility is low
                    # Enhance contrast
                    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    l = clahe.apply(l)
                    enhanced = cv2.merge([l, a, b])
                    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

                    rgb_enhanced = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
                    results_enhanced = pose_static.process(rgb_enhanced)

                    if results_enhanced.pose_landmarks:
                        avg_vis_enhanced = np.mean([lm.visibility for lm in results_enhanced.pose_landmarks.landmark])
                        if avg_vis_enhanced > avg_vis:
                            results = results_enhanced

            # Convert to dataframe format
            if results and results.pose_landmarks:
                for idx, landmark in enumerate(results.pose_landmarks.landmark):
                    # Get the original row to preserve column structure
                    orig_row = df_original[(df_original['frame_id'] == frame_id) &
                                          (df_original['landmark_id'] == idx)]

                    if not orig_row.empty:
                        row_dict = orig_row.iloc[0].to_dict()
                        # Update only the coordinate and visibility data
                        row_dict['x'] = landmark.x
                        row_dict['y'] = landmark.y
                        row_dict['z'] = landmark.z
                        row_dict['visibility'] = landmark.visibility
                        if 'x_norm' in row_dict:
                            row_dict['x_norm'] = landmark.x
                            row_dict['y_norm'] = landmark.y
                            row_dict['z_norm'] = landmark.z
                        reprocessed_data.append(row_dict)

    pose_static.close()
    cap.release()

    print(f"  Reprocessed {len(rotation_frames)} frames")

    # Combine: keep original for ALL frames except 40-60
    print("\n📊 Preserving original data...")

    # Get original data for all non-rotation frames
    good_frames = df_original[~df_original['frame_id'].isin(rotation_frames)]

    # Add reprocessed rotation frames
    if reprocessed_data:
        df_reprocessed = pd.DataFrame(reprocessed_data)
        df_final = pd.concat([good_frames, df_reprocessed], ignore_index=True)
    else:
        df_final = good_frames

    # Sort by frame and landmark
    df_final = df_final.sort_values(['frame_id', 'landmark_id'])

    # Save
    df_final.to_csv(output_csv, index=False)

    print(f"\n✅ Minimal fix complete!")
    print(f"📁 Saved to: {output_csv}")

    # Verify preservation
    for test_frame in [0, 3, 10, 18, 100, 400]:
        orig = df_original[df_original['frame_id'] == test_frame]
        final = df_final[df_final['frame_id'] == test_frame]

        if not orig.empty and not final.empty:
            if test_frame in rotation_frames:
                print(f"  Frame {test_frame}: Reprocessed")
            else:
                # Check if data is identical
                orig_vis = orig['visibility'].mean()
                final_vis = final['visibility'].mean()
                if abs(orig_vis - final_vis) < 0.001:
                    print(f"  Frame {test_frame}: ✅ Preserved (visibility {orig_vis:.3f})")
                else:
                    print(f"  Frame {test_frame}: ⚠️ Changed somehow")

if __name__ == "__main__":
    minimal_rotation_fix(
        video_path='video/dance.mp4',
        original_csv='creative_output/dance_poses.csv',
        output_csv='creative_output/dance_poses_minimal_fix.csv'
    )