#!/usr/bin/env python
"""
Analyze occlusion issues in frames 1-30 to understand why left leg detection fails.
"""

import pandas as pd
import numpy as np
import cv2
import mediapipe as mp
from pathlib import Path

def analyze_frame_characteristics(df, frame_range=(1, 30)):
    """
    Analyze pose characteristics that might cause detection issues.
    """
    print(f"\n📊 Analyzing Frames {frame_range[0]}-{frame_range[1]}")
    print("="*60)

    # Landmark names for reference
    landmark_names = {
        11: "left_shoulder", 12: "right_shoulder",
        13: "left_elbow", 14: "right_elbow",
        15: "left_wrist", 16: "right_wrist",
        23: "left_hip", 24: "right_hip",
        25: "left_knee", 26: "right_knee",
        27: "left_ankle", 28: "right_ankle",
        29: "left_heel", 30: "right_heel",
        31: "left_foot_index", 32: "right_foot_index"
    }

    # Left leg landmarks
    left_leg = [23, 25, 27, 29, 31]
    right_leg = [24, 26, 28, 30, 32]

    analysis_results = []

    for frame_id in range(frame_range[0], frame_range[1] + 1):
        frame_data = df[df['frame_id'] == frame_id]

        if frame_data.empty:
            continue

        # Analyze arm positions
        left_wrist = frame_data[frame_data['landmark_id'] == 15]
        right_wrist = frame_data[frame_data['landmark_id'] == 16]
        left_elbow = frame_data[frame_data['landmark_id'] == 13]
        right_elbow = frame_data[frame_data['landmark_id'] == 14]

        # Check for crossed arms
        crossed_wrists = False
        crossed_elbows = False

        if not left_wrist.empty and not right_wrist.empty:
            # Wrists crossed if left wrist is on right side and vice versa
            crossed_wrists = (left_wrist['x'].values[0] > 0.5 and
                            right_wrist['x'].values[0] < 0.5)

        if not left_elbow.empty and not right_elbow.empty:
            # Elbows crossed
            crossed_elbows = (left_elbow['x'].values[0] > 0.5 and
                            right_elbow['x'].values[0] < 0.5)

        # Check arm-torso proximity (potential occlusion)
        left_shoulder = frame_data[frame_data['landmark_id'] == 11]
        left_hip = frame_data[frame_data['landmark_id'] == 23]

        arm_close_to_body = False
        if not left_wrist.empty and not left_hip.empty:
            # Distance between wrist and hip
            wrist_hip_dist = np.sqrt(
                (left_wrist['x'].values[0] - left_hip['x'].values[0])**2 +
                (left_wrist['y'].values[0] - left_hip['y'].values[0])**2
            )
            arm_close_to_body = wrist_hip_dist < 0.15

        # Analyze leg visibility
        left_leg_data = frame_data[frame_data['landmark_id'].isin(left_leg)]
        right_leg_data = frame_data[frame_data['landmark_id'].isin(right_leg)]

        left_leg_vis = left_leg_data['visibility'].mean() if not left_leg_data.empty else 0
        right_leg_vis = right_leg_data['visibility'].mean() if not right_leg_data.empty else 0

        # Check specific critical landmarks
        left_hip_vis = frame_data[frame_data['landmark_id'] == 23]['visibility'].values
        left_hip_vis = left_hip_vis[0] if len(left_hip_vis) > 0 else 0

        left_knee_vis = frame_data[frame_data['landmark_id'] == 25]['visibility'].values
        left_knee_vis = left_knee_vis[0] if len(left_knee_vis) > 0 else 0

        # Store analysis
        analysis_results.append({
            'frame_id': frame_id,
            'crossed_wrists': crossed_wrists,
            'crossed_elbows': crossed_elbows,
            'arm_close_to_body': arm_close_to_body,
            'left_leg_avg_vis': left_leg_vis,
            'right_leg_avg_vis': right_leg_vis,
            'left_hip_vis': left_hip_vis,
            'left_knee_vis': left_knee_vis,
            'visibility_ratio': left_leg_vis / right_leg_vis if right_leg_vis > 0 else 0
        })

    # Convert to dataframe for analysis
    analysis_df = pd.DataFrame(analysis_results)

    # Print summary
    print("\n🎯 Occlusion Indicators:")
    print(f"  Frames with crossed wrists: {analysis_df['crossed_wrists'].sum()}")
    print(f"  Frames with crossed elbows: {analysis_df['crossed_elbows'].sum()}")
    print(f"  Frames with arms close to body: {analysis_df['arm_close_to_body'].sum()}")

    print("\n📉 Visibility Issues:")
    print(f"  Average left leg visibility: {analysis_df['left_leg_avg_vis'].mean():.2%}")
    print(f"  Average right leg visibility: {analysis_df['right_leg_avg_vis'].mean():.2%}")
    print(f"  Frames with left leg < 30% visibility: {(analysis_df['left_leg_avg_vis'] < 0.3).sum()}")
    print(f"  Frames with left hip < 30% visibility: {(analysis_df['left_hip_vis'] < 0.3).sum()}")
    print(f"  Frames with left knee < 30% visibility: {(analysis_df['left_knee_vis'] < 0.3).sum()}")

    # Identify worst frames
    worst_frames = analysis_df.nsmallest(10, 'left_leg_avg_vis')
    print("\n❌ Worst 10 Frames (lowest left leg visibility):")
    for _, row in worst_frames.iterrows():
        indicators = []
        if row['crossed_wrists']:
            indicators.append('crossed_wrists')
        if row['crossed_elbows']:
            indicators.append('crossed_elbows')
        if row['arm_close_to_body']:
            indicators.append('arm_close')

        print(f"  Frame {row['frame_id']:3d}: {row['left_leg_avg_vis']:.2%} visibility"
              f" - {', '.join(indicators) if indicators else 'no clear occlusion'}")

    return analysis_df

def compare_detection_methods(video_path, frame_id):
    """
    Compare different detection methods on a specific frame.
    """
    print(f"\n🔬 Comparing Detection Methods for Frame {frame_id}")
    print("="*60)

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    ret, frame = cap.read()

    if not ret:
        print("❌ Could not read frame")
        return

    h, w = frame.shape[:2]

    # Different detection configurations
    configs = [
        {
            'name': 'Standard',
            'static_image_mode': False,
            'model_complexity': 1,
            'min_detection_confidence': 0.4,
            'min_tracking_confidence': 0.4
        },
        {
            'name': 'Low Confidence',
            'static_image_mode': False,
            'model_complexity': 1,
            'min_detection_confidence': 0.2,
            'min_tracking_confidence': 0.2
        },
        {
            'name': 'Static High Complexity',
            'static_image_mode': True,
            'model_complexity': 2,
            'min_detection_confidence': 0.2,
            'min_tracking_confidence': 0.2
        },
        {
            'name': 'Ultra Low Confidence',
            'static_image_mode': True,
            'model_complexity': 2,
            'min_detection_confidence': 0.1,
            'min_tracking_confidence': 0.1
        }
    ]

    # Test each configuration
    left_leg = [23, 25, 27, 29, 31]

    for config in configs:
        pose = mp.solutions.pose.Pose(**{k: v for k, v in config.items() if k != 'name'})

        # Process frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            # Calculate left leg visibility
            left_leg_vis = []
            for idx in left_leg:
                if idx < len(results.pose_landmarks.landmark):
                    vis = results.pose_landmarks.landmark[idx].visibility
                    left_leg_vis.append(vis)

            avg_vis = np.mean(left_leg_vis) if left_leg_vis else 0
            print(f"  {config['name']:25s}: {avg_vis:.2%} left leg visibility")

            # Show specific landmarks
            hip_vis = results.pose_landmarks.landmark[23].visibility
            knee_vis = results.pose_landmarks.landmark[25].visibility
            ankle_vis = results.pose_landmarks.landmark[27].visibility
            print(f"    └─ Hip: {hip_vis:.2f}, Knee: {knee_vis:.2f}, Ankle: {ankle_vis:.2f}")
        else:
            print(f"  {config['name']:25s}: No detection")

        pose.close()

    cap.release()

def test_preprocessing_effects(video_path, frame_id):
    """
    Test different preprocessing methods on a problematic frame.
    """
    print(f"\n🎨 Testing Preprocessing Methods for Frame {frame_id}")
    print("="*60)

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    ret, frame = cap.read()

    if not ret:
        print("❌ Could not read frame")
        return

    # Preprocessing methods
    def enhance_contrast(img):
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    def brighten(img):
        return cv2.convertScaleAbs(img, alpha=1.3, beta=30)

    def enhance_lower_body(img):
        h, w = img.shape[:2]
        result = img.copy()
        lower = result[h//2:, :]
        lower = enhance_contrast(lower)
        result[h//2:, :] = lower
        return result

    methods = [
        ('Original', frame),
        ('CLAHE Enhanced', enhance_contrast(frame)),
        ('Brightened', brighten(frame)),
        ('Lower Body Enhanced', enhance_lower_body(frame)),
        ('Mirrored', cv2.flip(frame, 1)),
        ('Blurred', cv2.GaussianBlur(frame, (5, 5), 0))
    ]

    # Test each preprocessing
    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.15
    )

    left_leg = [23, 25, 27, 29, 31]

    for method_name, processed_frame in methods:
        rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results.pose_landmarks:
            # Calculate left leg visibility
            left_leg_vis = []
            for idx in left_leg:
                vis = results.pose_landmarks.landmark[idx].visibility
                left_leg_vis.append(vis)

            avg_vis = np.mean(left_leg_vis)
            print(f"  {method_name:20s}: {avg_vis:.2%} left leg visibility")
        else:
            print(f"  {method_name:20s}: No detection")

    pose.close()
    cap.release()

def main():
    """
    Main analysis of occlusion issues.
    """
    print("🔍 Occlusion Analysis for Dance Video")
    print("="*60)

    # Check which CSV files exist
    csv_files = {
        'original': 'creative_output/dance_poses.csv',
        'best_clean': 'creative_output/dance_poses_best_clean.csv',
        'rotation_targeted': 'creative_output/dance_poses_rotation_targeted.csv'
    }

    for name, path in csv_files.items():
        if Path(path).exists():
            print(f"\n📁 Analyzing: {name} ({path})")

            df = pd.read_csv(path)
            print(f"  Total frames: {df['frame_id'].nunique()}")
            print(f"  Total landmarks: {len(df)}")

            # Analyze frames 1-30
            analysis_df = analyze_frame_characteristics(df, (1, 30))

            # Save analysis
            analysis_path = f'creative_output/occlusion_analysis_{name}.csv'
            analysis_df.to_csv(analysis_path, index=False)
            print(f"\n💾 Analysis saved to {analysis_path}")

    # Test specific problematic frames
    video_path = 'video/dance.mp4'
    if Path(video_path).exists():
        # Test frame 3 (known to have missing left leg)
        compare_detection_methods(video_path, 3)
        test_preprocessing_effects(video_path, 3)

        # Test frame 15 (middle of problematic range)
        compare_detection_methods(video_path, 15)

if __name__ == "__main__":
    main()