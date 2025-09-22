#!/usr/bin/env python
"""
Efficient analysis of EVERY frame - no assumptions, but smarter processing.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
import concurrent.futures
import os


class EfficientFrameOptimizer:
    """Optimize every frame efficiently."""

    def __init__(self):
        self.mp_pose = mp.solutions.pose

    def process_frame(self, frame_id: int, frame_path: str) -> dict:
        """
        Process a single frame with smart strategy selection.
        """
        frame = cv2.imread(frame_path)
        if frame is None:
            return None

        # Start with standard detection
        standard_result = self.detect_pose(frame, confidence=0.3)

        if standard_result is not None:
            standard_score = standard_result['visibility'].mean()

            # If standard is good enough, use it
            if standard_score > 0.8:
                standard_result['frame_id'] = frame_id
                standard_result['strategy'] = 'standard'
                return standard_result

            # Otherwise, try targeted improvements
            best_result = standard_result
            best_score = standard_score
            best_strategy = 'standard'

            # Identify what needs improvement
            problems = self.identify_problems(standard_result)

            # Apply targeted strategies based on problems
            strategies_to_try = self.select_strategies(problems)

            for strategy_name, processed_frame, confidence in strategies_to_try:
                result = self.detect_pose(processed_frame, confidence,
                                        flip_back=(strategy_name == 'mirrored'))

                if result is not None:
                    score = result['visibility'].mean()

                    # Check for anatomical validity
                    if self.is_valid_pose(result):
                        score *= 1.1  # Bonus for valid pose

                    if score > best_score:
                        best_score = score
                        best_result = result
                        best_strategy = strategy_name

            best_result['frame_id'] = frame_id
            best_result['strategy'] = best_strategy

            return best_result

        # If standard failed, try recovery strategies
        recovery_strategies = [
            ('blur', cv2.GaussianBlur(frame, (5, 5), 0), 0.2),
            ('enhanced', self.enhance_contrast(frame), 0.2),
            ('mirrored', cv2.flip(frame, 1), 0.15),
            ('low_conf', frame, 0.1)
        ]

        for strategy_name, processed_frame, confidence in recovery_strategies:
            result = self.detect_pose(processed_frame, confidence,
                                    flip_back=(strategy_name == 'mirrored'))

            if result is not None:
                result['frame_id'] = frame_id
                result['strategy'] = strategy_name
                return result

        return None

    def identify_problems(self, result):
        """Identify what needs improvement."""
        problems = []

        # Check for low visibility landmarks
        low_vis = result[result['visibility'] < 0.5]

        # Identify which body parts have issues
        left_arm = [11, 13, 15]
        right_arm = [12, 14, 16]
        left_leg = [23, 25, 27, 29, 31]
        right_leg = [24, 26, 28, 30, 32]

        for part_name, landmarks in [('left_arm', left_arm),
                                    ('right_arm', right_arm),
                                    ('left_leg', left_leg),
                                    ('right_leg', right_leg)]:
            part_data = result[result['landmark_id'].isin(landmarks)]
            if part_data['visibility'].mean() < 0.5:
                problems.append(part_name)

        return problems

    def select_strategies(self, problems):
        """Select strategies based on identified problems."""
        strategies = []

        if 'left_leg' in problems or 'right_leg' in problems:
            # Leg problems - try lower body enhancement
            strategies.append(('lower_enhanced', self.enhance_lower_body, 0.2))
            strategies.append(('blur_legs', lambda f: cv2.GaussianBlur(f, (7, 7), 0), 0.2))

        if 'left_arm' in problems or 'right_arm' in problems:
            # Arm problems - try mirroring
            strategies.append(('mirrored', lambda f: cv2.flip(f, 1), 0.2))

        # Always try these as fallback
        strategies.append(('enhanced', self.enhance_contrast, 0.25))
        strategies.append(('low_conf', lambda f: f, 0.15))

        # Apply strategies to frame
        processed = []
        for name, func, conf in strategies:
            if callable(func):
                frame = func(self.current_frame)
            else:
                frame = func
            processed.append((name, frame, conf))

        return processed

    def detect_pose(self, frame, confidence=0.3, flip_back=False):
        """Run pose detection."""
        self.current_frame = frame  # Store for strategy functions

        pose = mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=confidence,
            min_tracking_confidence=confidence
        )

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        data = []
        if results.pose_landmarks:
            for idx, lm in enumerate(results.pose_landmarks.landmark):
                x = 1.0 - lm.x if flip_back else lm.x
                data.append({
                    'landmark_id': idx,
                    'x': x,
                    'y': lm.y,
                    'z': lm.z,
                    'visibility': lm.visibility
                })

        pose.close()

        if data:
            return pd.DataFrame(data)
        return None

    def is_valid_pose(self, result):
        """Quick check for anatomical validity."""
        # Check if head is above hips
        nose = result[result['landmark_id'] == 0]
        hip = result[result['landmark_id'] == 23]

        if not nose.empty and not hip.empty:
            if nose.iloc[0]['y'] > hip.iloc[0]['y'] + 0.2:  # Head way below hips
                return False

        return True

    def enhance_contrast(self, frame):
        """CLAHE enhancement."""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    def enhance_lower_body(self, frame):
        """Enhance lower body region."""
        h, w = frame.shape[:2]
        result = frame.copy()
        lower = result[h//3:, :]
        lower = self.enhance_contrast(lower)
        result[h//3:, :] = lower
        return result


def process_frame_batch(frames_batch):
    """Process a batch of frames."""
    optimizer = EfficientFrameOptimizer()
    results = []

    for frame_id, frame_path in frames_batch:
        print(f"Processing frame {frame_id}...")
        result = optimizer.process_frame(frame_id, frame_path)

        if result is not None:
            for _, row in result.iterrows():
                results.append(row.to_dict())
        else:
            print(f"  Warning: Frame {frame_id} failed")

    return results


def analyze_all_frames_efficiently():
    """
    Efficiently analyze ALL frames.
    """
    print("🚀 EFFICIENT FRAME-BY-FRAME OPTIMIZATION")
    print("="*60)

    # Extract frames
    video_path = 'video/dance.mp4'
    frames_dir = Path('frames_complete_analysis')

    if not frames_dir.exists():
        print("📸 Extracting frames...")
        frames_dir.mkdir(parents=True)

        cap = cv2.VideoCapture(video_path)
        frame_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_path = frames_dir / f"frame_{frame_count:04d}.png"
            cv2.imwrite(str(frame_path), frame)
            frame_count += 1

        cap.release()
        print(f"✅ Extracted {frame_count} frames")

    # Process all frames
    frame_files = sorted(frames_dir.glob("frame_*.png"))
    print(f"\n🔍 Processing {len(frame_files)} frames...")

    all_results = []

    # Process in batches of 10 for progress reporting
    batch_size = 10
    optimizer = EfficientFrameOptimizer()

    for i in range(0, len(frame_files), batch_size):
        batch_end = min(i + batch_size, len(frame_files))
        print(f"\n📦 Processing frames {i}-{batch_end-1}...")

        for j in range(i, batch_end):
            frame_path = frame_files[j]
            frame_id = int(frame_path.stem.split('_')[1])

            result = optimizer.process_frame(frame_id, str(frame_path))

            if result is not None:
                strategy_used = result.iloc[0]['strategy'] if 'strategy' in result else 'unknown'
                avg_vis = result['visibility'].mean()
                print(f"  Frame {frame_id}: {strategy_used} (vis: {avg_vis:.2f})")

                for _, row in result.iterrows():
                    all_results.append(row.to_dict())
            else:
                print(f"  Frame {frame_id}: FAILED")

    # Save results
    df_final = pd.DataFrame(all_results)
    output_path = 'creative_output/all_frames_optimized.csv'
    df_final.to_csv(output_path, index=False)

    print(f"\n✅ Processed all {len(frame_files)} frames!")
    print(f"📁 Saved to: {output_path}")

    # Generate comprehensive report
    print("\n📊 COMPREHENSIVE REPORT:")
    print("="*50)

    frames_processed = df_final['frame_id'].nunique()
    print(f"Frames successfully processed: {frames_processed}/404")

    # Strategy distribution
    strategy_usage = {}
    for frame_id in df_final['frame_id'].unique():
        frame_data = df_final[df_final['frame_id'] == frame_id]
        strategy = frame_data.iloc[0]['strategy']
        strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1

    print("\n📈 Strategy Usage:")
    for strategy, count in sorted(strategy_usage.items(), key=lambda x: -x[1]):
        print(f"  {strategy:15s}: {count:3d} frames ({count/frames_processed*100:.1f}%)")

    # Quality metrics
    high_conf = (df_final['visibility'] > 0.7).sum()
    total = len(df_final)
    print(f"\n✨ Quality Metrics:")
    print(f"  High confidence (>70%): {high_conf}/{total} ({high_conf/total*100:.1f}%)")

    # Per-frame quality
    frame_qualities = []
    for frame_id in range(404):
        frame_data = df_final[df_final['frame_id'] == frame_id]
        if not frame_data.empty:
            avg_vis = frame_data['visibility'].mean()
            frame_qualities.append(avg_vis)
        else:
            frame_qualities.append(0)

    excellent_frames = sum(1 for q in frame_qualities if q > 0.8)
    good_frames = sum(1 for q in frame_qualities if 0.6 <= q <= 0.8)
    poor_frames = sum(1 for q in frame_qualities if q < 0.6)

    print(f"\n📊 Frame Quality Distribution:")
    print(f"  Excellent (>80%): {excellent_frames} frames")
    print(f"  Good (60-80%): {good_frames} frames")
    print(f"  Poor (<60%): {poor_frames} frames")

    # Create final video
    print("\n🎬 Creating final video...")
    import subprocess
    result = subprocess.run([
        'python', 'create_skeleton_video.py',
        '--csv', output_path,
        '--output', 'creative_output/all_frames_optimized.mp4'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Video created: creative_output/all_frames_optimized.mp4")
    else:
        print("❌ Video creation failed")

    return df_final


if __name__ == "__main__":
    analyze_all_frames_efficiently()