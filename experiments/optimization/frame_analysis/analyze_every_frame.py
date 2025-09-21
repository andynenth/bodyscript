#!/usr/bin/env python
"""
TRUE comprehensive analysis - analyze and optimize EVERY SINGLE FRAME.
No assumptions, no shortcuts.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
import os


class TrueFrameAnalyzer:
    """Analyze EVERY frame without assumptions."""

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.all_frame_results = {}

    def analyze_single_frame(self, frame_path: str, frame_id: int,
                            existing_data: pd.DataFrame = None):
        """
        Thoroughly analyze a single frame.
        Test multiple strategies and pick the best.
        """
        print(f"Analyzing frame {frame_id}...", end='')

        frame = cv2.imread(frame_path)
        if frame is None:
            print(f" ERROR: Cannot read frame")
            return None

        # Test ALL strategies on EVERY frame
        strategies = {
            'original': frame,
            'blur5': cv2.GaussianBlur(frame, (5, 5), 0),
            'blur7': cv2.GaussianBlur(frame, (7, 7), 0),
            'enhanced': self.enhance_contrast(frame),
            'lower_enhanced': self.enhance_lower_body(frame),
            'brightened': cv2.convertScaleAbs(frame, alpha=1.2, beta=20),
            'darkened': cv2.convertScaleAbs(frame, alpha=0.8, beta=-10),
            'mirrored': cv2.flip(frame, 1),
            'sharpened': self.sharpen(frame),
            'denoised': cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
        }

        # Test each strategy with different confidence levels
        confidence_levels = [0.1, 0.2, 0.3, 0.4, 0.5]

        best_result = None
        best_score = 0
        best_strategy = None
        best_confidence = None

        for strategy_name, processed_frame in strategies.items():
            for confidence in confidence_levels:
                # Run detection
                result = self.detect_pose(processed_frame, confidence,
                                        flip_back=(strategy_name == 'mirrored'))

                if result is not None and not result.empty:
                    # Calculate comprehensive score
                    score = self.calculate_score(result, existing_data, frame_id)

                    if score > best_score:
                        best_score = score
                        best_result = result
                        best_strategy = strategy_name
                        best_confidence = confidence

        if best_result is not None:
            best_result['frame_id'] = frame_id
            best_result['strategy'] = best_strategy
            best_result['confidence_used'] = best_confidence
            print(f" {best_strategy}@{best_confidence:.1f} (score: {best_score:.3f})")
        else:
            print(f" FAILED - no detection")

        return best_result

    def detect_pose(self, frame, confidence=0.3, flip_back=False):
        """Run pose detection on frame."""
        pose = mp.solutions.pose.Pose(
            static_image_mode=True,  # Always treat as static for consistency
            model_complexity=2,       # Always use highest complexity
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

    def calculate_score(self, result, existing_data, frame_id):
        """
        Calculate comprehensive quality score for detection.
        """
        score = 0.0

        # 1. Visibility score (40%)
        vis_score = result['visibility'].mean()
        high_vis_count = (result['visibility'] > 0.7).sum()
        vis_score = (vis_score * 0.7 + (high_vis_count / 33) * 0.3)
        score += vis_score * 0.4

        # 2. Completeness (30%)
        if len(result) == 33:
            score += 0.3
        else:
            score += (len(result) / 33) * 0.3

        # 3. Anatomical plausibility (20%)
        anat_score = self.check_anatomy(result)
        score += anat_score * 0.2

        # 4. Temporal consistency if we have previous frame (10%)
        if existing_data is not None and frame_id > 0:
            prev_frame = existing_data[existing_data['frame_id'] == frame_id - 1]
            if not prev_frame.empty:
                temp_score = self.check_temporal_consistency(result, prev_frame)
                score += temp_score * 0.1
        else:
            score += 0.1  # No penalty for first frame

        return score

    def check_anatomy(self, result):
        """Check if pose is anatomically plausible."""
        score = 1.0

        # Check shoulder width
        left_shoulder = result[result['landmark_id'] == 11]
        right_shoulder = result[result['landmark_id'] == 12]

        if not left_shoulder.empty and not right_shoulder.empty:
            shoulder_dist = np.sqrt(
                (left_shoulder.iloc[0]['x'] - right_shoulder.iloc[0]['x'])**2 +
                (left_shoulder.iloc[0]['y'] - right_shoulder.iloc[0]['y'])**2
            )

            # Reasonable shoulder width: 0.1 to 0.4
            if shoulder_dist < 0.05 or shoulder_dist > 0.5:
                score *= 0.5

        # Check if head is above hips
        nose = result[result['landmark_id'] == 0]
        left_hip = result[result['landmark_id'] == 23]

        if not nose.empty and not left_hip.empty:
            if nose.iloc[0]['y'] > left_hip.iloc[0]['y']:  # Head below hips
                score *= 0.3

        return score

    def check_temporal_consistency(self, current, previous):
        """Check movement consistency between frames."""
        score = 1.0
        max_movement = 0

        for landmark_id in range(33):
            curr_lm = current[current['landmark_id'] == landmark_id]
            prev_lm = previous[previous['landmark_id'] == landmark_id]

            if not curr_lm.empty and not prev_lm.empty:
                movement = np.sqrt(
                    (curr_lm.iloc[0]['x'] - prev_lm.iloc[0]['x'])**2 +
                    (curr_lm.iloc[0]['y'] - prev_lm.iloc[0]['y'])**2
                )
                max_movement = max(max_movement, movement)

        # Penalize large movements (likely errors)
        if max_movement > 0.3:  # More than 30% of frame
            score *= (0.3 / max_movement)

        return min(score, 1.0)

    def enhance_contrast(self, frame):
        """Enhance contrast using CLAHE."""
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

    def sharpen(self, frame):
        """Apply sharpening filter."""
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        return cv2.filter2D(frame, -1, kernel)


def analyze_all_frames():
    """
    Main function to analyze EVERY SINGLE FRAME.
    """
    print("🔬 TRUE COMPREHENSIVE FRAME-BY-FRAME ANALYSIS")
    print("="*60)
    print("Analyzing ALL 404 frames individually...")
    print("This will test 50 strategy combinations per frame (10 strategies × 5 confidence levels)")
    print("Total analyses: 404 × 50 = 20,200 detection attempts")
    print()

    # Extract frames if not already done
    video_path = 'video/dance.mp4'
    frames_dir = Path('frames_complete_analysis')

    if not frames_dir.exists():
        print("📸 Extracting all frames...")
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

            if frame_count % 50 == 0:
                print(f"  Extracted {frame_count} frames...")

        cap.release()
        print(f"✅ Extracted {frame_count} frames")

    # Analyze EVERY frame
    analyzer = TrueFrameAnalyzer()
    all_results = []

    frame_files = sorted(frames_dir.glob("frame_*.png"))
    print(f"\n🔍 Analyzing {len(frame_files)} frames...")

    for frame_path in frame_files:
        # Extract frame number from filename
        frame_id = int(frame_path.stem.split('_')[1])

        # Get existing data for temporal consistency check
        existing_data = pd.DataFrame(all_results) if all_results else None

        # Analyze this frame
        result = analyzer.analyze_single_frame(
            str(frame_path),
            frame_id,
            existing_data
        )

        if result is not None:
            for _, row in result.iterrows():
                all_results.append(row.to_dict())

    # Save results
    df_final = pd.DataFrame(all_results)
    output_path = 'creative_output/every_frame_optimized.csv'
    df_final.to_csv(output_path, index=False)

    print(f"\n✅ Analysis complete!")
    print(f"📁 Saved to: {output_path}")

    # Generate report
    print("\n📊 FINAL REPORT:")
    print("="*40)

    total_frames = df_final['frame_id'].nunique()
    print(f"Frames analyzed: {total_frames}/404")

    # Strategy usage
    strategy_counts = df_final.groupby('frame_id')['strategy'].first().value_counts()
    print("\nStrategy usage:")
    for strategy, count in strategy_counts.items():
        print(f"  {strategy}: {count} frames")

    # Confidence distribution
    high_conf = (df_final['visibility'] > 0.7).sum()
    total = len(df_final)
    print(f"\nHigh confidence landmarks: {high_conf}/{total} ({high_conf/total*100:.1f}%)")

    # Create video
    print("\n🎬 Creating optimized video...")
    import subprocess
    result = subprocess.run([
        'python', 'create_skeleton_video.py',
        '--csv', output_path,
        '--output', 'creative_output/every_frame_optimized.mp4'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Video created: creative_output/every_frame_optimized.mp4")
    else:
        print(f"❌ Video creation failed: {result.stderr}")


if __name__ == "__main__":
    analyze_all_frames()