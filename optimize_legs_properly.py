#!/usr/bin/env python
"""
Proper optimization focusing on LEG detection issues.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path


def detect_with_leg_focus(frame, frame_id):
    """
    Detection specifically optimized for legs.
    """
    h, w = frame.shape[:2]

    # Strategies specifically for leg detection
    strategies = []

    # 1. Original
    strategies.append(('original', frame, 0.3))

    # 2. Lower body enhancement
    lower_enhanced = frame.copy()
    lower_region = lower_enhanced[h//3:, :]
    lab = cv2.cvtColor(lower_region, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    enhanced_lower = cv2.merge([l, a, b])
    enhanced_lower = cv2.cvtColor(enhanced_lower, cv2.COLOR_LAB2BGR)
    lower_enhanced[h//3:, :] = enhanced_lower
    strategies.append(('lower_enhanced', lower_enhanced, 0.2))

    # 3. Crop and zoom lower body
    cropped = frame[h//4:, :]  # Focus on lower 3/4
    cropped_resized = cv2.resize(cropped, (w, h))
    strategies.append(('lower_zoom', cropped_resized, 0.2))

    # 4. Increase brightness on lower body
    bright_lower = frame.copy()
    bright_lower[h//3:, :] = cv2.convertScaleAbs(bright_lower[h//3:, :], alpha=1.3, beta=30)
    strategies.append(('bright_lower', bright_lower, 0.2))

    # 5. Heavy blur (sometimes helps with noisy backgrounds)
    heavy_blur = cv2.GaussianBlur(frame, (11, 11), 0)
    strategies.append(('heavy_blur', heavy_blur, 0.15))

    # 6. Try multiple confidence levels with enhancement
    strategies.append(('enhanced_low_conf', lower_enhanced, 0.1))

    best_result = None
    best_leg_score = 0
    best_strategy = None

    for strategy_name, processed_frame, confidence in strategies:
        pose = mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=confidence,
            min_tracking_confidence=confidence
        )

        rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        if results and results.pose_landmarks:
            # Calculate LEG-SPECIFIC score
            leg_score = 0
            leg_count = 0

            # Leg landmarks
            leg_landmarks = [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]

            for idx in leg_landmarks:
                if idx < len(results.pose_landmarks.landmark):
                    vis = results.pose_landmarks.landmark[idx].visibility
                    leg_score += vis
                    leg_count += 1

            # Critical landmarks (knees and ankles) get extra weight
            for idx in [25, 26, 27, 28]:  # knees and ankles
                if idx < len(results.pose_landmarks.landmark):
                    vis = results.pose_landmarks.landmark[idx].visibility
                    leg_score += vis * 0.5  # Extra weight

            if leg_count > 0:
                leg_score = leg_score / (leg_count + 4 * 0.5)  # Normalize

                # For lower_zoom, adjust coordinates back
                if strategy_name == 'lower_zoom':
                    for lm in results.pose_landmarks.landmark:
                        lm.y = lm.y * (3/4) + (1/4)  # Adjust y coordinate

                if leg_score > best_leg_score:
                    best_leg_score = leg_score
                    best_result = results
                    best_strategy = strategy_name

        pose.close()

    if best_result:
        data = []
        for idx, lm in enumerate(best_result.pose_landmarks.landmark):
            data.append({
                'frame_id': frame_id,
                'landmark_id': idx,
                'x': lm.x,
                'y': lm.y,
                'z': lm.z,
                'visibility': lm.visibility,
                'strategy': best_strategy
            })
        return pd.DataFrame(data), best_leg_score, best_strategy

    return None, 0, 'failed'


def main():
    """
    Re-optimize all frames with focus on leg detection.
    """
    print("🦵 LEG-FOCUSED OPTIMIZATION")
    print("="*60)

    frames_dir = Path('frames_complete_analysis')
    frame_files = sorted(frames_dir.glob("frame_*.png"))

    print(f"Processing {len(frame_files)} frames with leg-specific optimization...")

    all_results = []
    strategy_count = {}
    leg_scores = []

    for i, frame_path in enumerate(frame_files):
        frame_id = int(frame_path.stem.split('_')[1])
        frame = cv2.imread(str(frame_path))

        result, leg_score, strategy = detect_with_leg_focus(frame, frame_id)

        if result is not None:
            all_results.append(result)
            strategy_count[strategy] = strategy_count.get(strategy, 0) + 1
            leg_scores.append(leg_score)

            if frame_id % 20 == 0:
                print(f"Frame {frame_id:3d}: {strategy:15s} (leg score: {leg_score:.3f})")

        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{len(frame_files)}")

    # Save results
    if all_results:
        df_final = pd.concat(all_results, ignore_index=True)
        output_csv = 'creative_output/leg_optimized.csv'
        df_final.to_csv(output_csv, index=False)

        print(f"\n✅ Optimization complete!")
        print(f"📁 Saved to: {output_csv}")

        # Analyze leg performance
        print("\n📊 LEG DETECTION REPORT:")
        print("="*40)

        left_leg = [23, 25, 27, 29, 31]
        right_leg = [24, 26, 28, 30, 32]

        left_data = df_final[df_final['landmark_id'].isin(left_leg)]
        right_data = df_final[df_final['landmark_id'].isin(right_leg)]

        print(f"Left leg avg visibility: {left_data['visibility'].mean():.2%}")
        print(f"Right leg avg visibility: {right_data['visibility'].mean():.2%}")

        # Check critical landmarks
        left_knee = df_final[df_final['landmark_id'] == 25]
        right_knee = df_final[df_final['landmark_id'] == 26]

        print(f"Left knee avg: {left_knee['visibility'].mean():.2%}")
        print(f"Right knee avg: {right_knee['visibility'].mean():.2%}")

        print("\nStrategy usage:")
        for strategy, count in sorted(strategy_count.items(), key=lambda x: -x[1]):
            print(f"  {strategy:15s}: {count:3d} frames")

        # Create video
        print("\n🎬 Creating leg-optimized video...")
        import subprocess
        subprocess.run([
            'python', 'create_skeleton_video.py',
            '--csv', output_csv,
            '--output', 'creative_output/leg_optimized.mp4'
        ])


if __name__ == "__main__":
    main()