#!/usr/bin/env python
"""
Fix fast motion tracking issues by adjusting detection/tracking balance.
"""

import cv2
import numpy as np
import pandas as pd
import mediapipe as mp
from pathlib import Path

def detect_motion_speed(frame1, frame2):
    """Calculate motion between two frames."""
    # Convert to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Calculate optical flow
    flow = cv2.calcOpticalFlowFarneback(
        gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0
    )

    # Calculate magnitude of motion
    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
    avg_motion = np.mean(magnitude)

    return avg_motion

def process_with_adaptive_detection(video_path: str, output_csv: str):
    """
    Process video with adaptive detection based on motion speed.
    """
    print("🎯 Processing with Motion-Adaptive Detection")
    print("="*60)

    cap = cv2.VideoCapture(video_path)

    # Initialize MediaPipe
    mp_pose = mp.solutions.pose

    # Read first frame
    ret, prev_frame = cap.read()
    if not ret:
        print("❌ Cannot read video")
        return

    all_poses = []
    frame_idx = 0

    # Motion threshold
    FAST_MOTION_THRESHOLD = 2.0

    while cap.isOpened():
        ret, curr_frame = cap.read()
        if not ret:
            break

        # Calculate motion speed
        motion_speed = detect_motion_speed(prev_frame, curr_frame)

        # Adaptive parameters based on motion
        if motion_speed > FAST_MOTION_THRESHOLD:
            # Fast motion: prioritize detection over tracking
            print(f"Frame {frame_idx}: Fast motion detected ({motion_speed:.2f})")

            # Use static image mode for better detection
            pose = mp_pose.Pose(
                static_image_mode=True,  # Treat each frame independently
                model_complexity=2,       # Use best model
                min_detection_confidence=0.3,
                min_tracking_confidence=0.1  # Low tracking reliance
            )
        else:
            # Slow motion: normal tracking
            pose = mp_pose.Pose(
                static_image_mode=False,  # Use tracking
                model_complexity=1,
                min_detection_confidence=0.4,
                min_tracking_confidence=0.5  # Normal tracking
            )

        # Process frame
        rgb_frame = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        if results.pose_landmarks:
            # Convert to dataframe
            frame_data = []
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                frame_data.append({
                    'frame_id': frame_idx,
                    'landmark_id': idx,
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility,
                    'motion_speed': motion_speed,
                    'detection_mode': 'static' if motion_speed > FAST_MOTION_THRESHOLD else 'tracking'
                })
            all_poses.extend(frame_data)

        pose.close()
        prev_frame = curr_frame
        frame_idx += 1

        if frame_idx % 30 == 0:
            print(f"Processed {frame_idx} frames...")

    cap.release()

    # Save results
    df = pd.DataFrame(all_poses)
    df.to_csv(output_csv, index=False)

    print(f"\n✅ Saved to: {output_csv}")

    # Report statistics
    static_frames = len(df[df['detection_mode'] == 'static']['frame_id'].unique())
    tracking_frames = len(df[df['detection_mode'] == 'tracking']['frame_id'].unique())

    print(f"\n📊 Statistics:")
    print(f"  Frames with static detection: {static_frames}")
    print(f"  Frames with tracking: {tracking_frames}")
    print(f"  Average motion speed: {df['motion_speed'].mean():.2f}")

def reprocess_fast_sections(csv_path: str, video_path: str, output_csv: str):
    """
    Identify and reprocess sections with fast motion.
    """
    print("🔧 Reprocessing Fast Motion Sections")
    print("="*60)

    # Load existing data
    df = pd.read_csv(csv_path)

    # Identify problem areas (where skeleton doesn't match movement)
    problem_frames = []

    for frame_id in range(1, df['frame_id'].max()):
        curr_frame = df[df['frame_id'] == frame_id]
        prev_frame = df[df['frame_id'] == frame_id - 1]

        # Check for sudden jumps or orientation issues
        for landmark_id in [11, 12, 23, 24]:  # Key body points
            curr_lm = curr_frame[curr_frame['landmark_id'] == landmark_id]
            prev_lm = prev_frame[prev_frame['landmark_id'] == landmark_id]

            if not curr_lm.empty and not prev_lm.empty:
                dx = abs(curr_lm.iloc[0]['x'] - prev_lm.iloc[0]['x'])
                dy = abs(curr_lm.iloc[0]['y'] - prev_lm.iloc[0]['y'])

                # Large movement might indicate tracking failure
                if dx > 0.1 or dy > 0.1:
                    problem_frames.append(frame_id)
                    break

    problem_frames = list(set(problem_frames))
    print(f"Found {len(problem_frames)} frames with potential tracking issues")

    if not problem_frames:
        print("✅ No fast motion issues detected")
        return df

    # Reprocess problem sections with static detection
    cap = cv2.VideoCapture(video_path)
    mp_pose = mp.solutions.pose

    # Use static detection for problem frames
    pose_static = mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.2,
        min_tracking_confidence=0.1
    )

    df_fixed = df.copy()

    for frame_id in problem_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()

        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose_static.process(rgb_frame)

            if results.pose_landmarks:
                # Update dataframe with reprocessed data
                for idx, landmark in enumerate(results.pose_landmarks.landmark):
                    df_fixed.loc[(df_fixed['frame_id'] == frame_id) &
                                (df_fixed['landmark_id'] == idx),
                                ['x', 'y', 'z', 'visibility']] = [
                        landmark.x, landmark.y, landmark.z, landmark.visibility
                    ]

    pose_static.close()
    cap.release()

    # Save fixed version
    df_fixed.to_csv(output_csv, index=False)
    print(f"\n✅ Fixed data saved to: {output_csv}")

    return df_fixed

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--reprocess':
        # Reprocess existing data
        reprocess_fast_sections(
            'creative_output/dance_poses.csv',
            'video/dance.mp4',
            'creative_output/dance_poses_motion_fixed.csv'
        )
    else:
        # Process from scratch with adaptive detection
        process_with_adaptive_detection(
            'video/dance.mp4',
            'creative_output/dance_poses_adaptive.csv'
        )