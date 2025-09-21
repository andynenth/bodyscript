#!/usr/bin/env python
"""
TRUE analysis of EVERY frame - simplified and direct.
No assumptions. Every frame gets individually optimized.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path


def analyze_single_frame(frame_path, frame_id):
    """
    Analyze ONE frame completely.
    """
    frame = cv2.imread(str(frame_path))
    if frame is None:
        return None

    # Initialize pose detector
    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.2,
        min_tracking_confidence=0.2
    )

    # Strategy 1: Original
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result_orig = pose.process(rgb)

    # Strategy 2: Blurred
    blurred = cv2.GaussianBlur(frame, (7, 7), 0)
    rgb_blur = cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB)
    result_blur = pose.process(rgb_blur)

    # Strategy 3: Enhanced
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    rgb_enh = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
    result_enh = pose.process(rgb_enh)

    # Strategy 4: Mirrored
    mirrored = cv2.flip(frame, 1)
    rgb_mir = cv2.cvtColor(mirrored, cv2.COLOR_BGR2RGB)
    result_mir = pose.process(rgb_mir)

    pose.close()

    # Choose best result
    results = [
        ('original', result_orig),
        ('blurred', result_blur),
        ('enhanced', result_enh),
        ('mirrored', result_mir)
    ]

    best_score = 0
    best_result = None
    best_strategy = None

    for strategy, result in results:
        if result and result.pose_landmarks:
            # Calculate score
            score = 0
            for lm in result.pose_landmarks.landmark:
                score += lm.visibility

            score = score / 33  # Average visibility

            if score > best_score:
                best_score = score
                best_result = result
                best_strategy = strategy

    if best_result:
        data = []
        for idx, lm in enumerate(best_result.pose_landmarks.landmark):
            x = lm.x
            if best_strategy == 'mirrored':
                x = 1.0 - x  # Flip back

            data.append({
                'frame_id': frame_id,
                'landmark_id': idx,
                'x': x,
                'y': lm.y,
                'z': lm.z,
                'visibility': lm.visibility,
                'strategy': best_strategy
            })
        return pd.DataFrame(data), best_score, best_strategy

    return None, 0, 'failed'


def main():
    """
    Analyze ALL 404 frames individually.
    """
    print("🎯 TRUE FRAME-BY-FRAME ANALYSIS OF ALL 404 FRAMES")
    print("="*60)

    frames_dir = Path('frames_complete_analysis')

    # Get all frame files
    frame_files = sorted(frames_dir.glob("frame_*.png"))
    print(f"Found {len(frame_files)} frames to analyze")

    all_results = []
    strategy_count = {}

    print("\nAnalyzing each frame:")
    print("-"*40)

    for i, frame_path in enumerate(frame_files):
        frame_id = int(frame_path.stem.split('_')[1])

        # Analyze this specific frame
        result, score, strategy = analyze_single_frame(frame_path, frame_id)

        if result is not None:
            all_results.append(result)
            strategy_count[strategy] = strategy_count.get(strategy, 0) + 1

            # Print progress
            if frame_id % 10 == 0:
                print(f"Frame {frame_id:3d}: {strategy:10s} (score: {score:.3f})")
        else:
            print(f"Frame {frame_id:3d}: FAILED")

        # Progress indicator
        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{len(frame_files)} frames analyzed")

    # Combine all results
    if all_results:
        df_final = pd.concat(all_results, ignore_index=True)
        output_csv = 'creative_output/true_every_frame_optimized.csv'
        df_final.to_csv(output_csv, index=False)

        print(f"\n✅ Analysis complete!")
        print(f"📁 Saved to: {output_csv}")

        # Report
        print("\n📊 FINAL REPORT:")
        print("="*40)

        print(f"Frames analyzed: {len(frame_files)}")
        print(f"Successful: {len(df_final['frame_id'].unique())}")

        print("\nStrategy usage:")
        for strategy, count in sorted(strategy_count.items(), key=lambda x: -x[1]):
            print(f"  {strategy:10s}: {count:3d} frames ({count/len(frame_files)*100:.1f}%)")

        # Quality assessment
        high_conf = (df_final['visibility'] > 0.7).sum()
        total = len(df_final)
        print(f"\nQuality:")
        print(f"  High confidence (>70%): {high_conf}/{total} ({high_conf/total*100:.1f}%)")

        # Frame-by-frame quality
        print("\nPer-frame average visibility:")
        for frame_id in range(0, min(10, len(frame_files))):
            frame_data = df_final[df_final['frame_id'] == frame_id]
            if not frame_data.empty:
                avg_vis = frame_data['visibility'].mean()
                strategy = frame_data.iloc[0]['strategy']
                print(f"  Frame {frame_id}: {avg_vis:.3f} ({strategy})")

        print("  ...")

        for frame_id in range(max(0, len(frame_files)-10), len(frame_files)):
            frame_data = df_final[df_final['frame_id'] == frame_id]
            if not frame_data.empty:
                avg_vis = frame_data['visibility'].mean()
                strategy = frame_data.iloc[0]['strategy']
                print(f"  Frame {frame_id}: {avg_vis:.3f} ({strategy})")

        # Create video
        print("\n🎬 Creating optimized video...")
        import subprocess
        result = subprocess.run([
            'python', 'create_skeleton_video.py',
            '--csv', output_csv,
            '--output', 'creative_output/true_every_frame_optimized.mp4'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Video created: creative_output/true_every_frame_optimized.mp4")
        else:
            print("❌ Video creation failed")


if __name__ == "__main__":
    main()