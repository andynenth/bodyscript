#!/usr/bin/env python
"""
Unified optimization approach combining best strategies from all tests.
Key findings:
- lower_enhance performs best for leg detection (59.3% avg, 76.9% success)
- CLAHE enhancement helps (57% avg, 69.2% success)
- Mirror strategy excellent for rotation frames (86-95% on frames 50-52)
- Low confidence helps but not always
- Blur can help specific frames
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
import json


class UnifiedOptimizer:
    """Unified optimization combining all learnings."""

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.leg_landmarks = [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        self.critical_leg = [25, 26, 27, 28]  # knees and ankles

    def optimize_frame(self, frame, frame_id):
        """
        Optimize a single frame using unified strategy selection.
        """
        h, w = frame.shape[:2]

        # Categorize frame
        category = self.categorize_frame(frame_id)

        # Select strategies based on category
        strategies = self.select_strategies_for_category(category, frame)

        best_result = None
        best_score = 0
        best_strategy = None

        for strategy_name, processed_frame, confidence in strategies:
            result = self.detect_pose(processed_frame, confidence,
                                    flip_back=(strategy_name.startswith('mirror')))

            if result is not None:
                # Calculate comprehensive score
                score = self.calculate_comprehensive_score(result, frame_id, strategy_name)

                if score > best_score:
                    best_score = score
                    best_result = result
                    best_strategy = strategy_name

        if best_result is not None:
            best_result['frame_id'] = frame_id
            best_result['strategy'] = best_strategy
            best_result['score'] = best_score
            return best_result

        # Fallback if nothing worked
        return self.fallback_detection(frame, frame_id)

    def categorize_frame(self, frame_id):
        """Categorize frame based on known patterns."""
        if frame_id <= 10:
            return 'early_difficult'  # Early frames with leg issues
        elif 40 <= frame_id <= 60:
            return 'rotation'  # Rotation tracking issues
        elif frame_id in [73, 100, 206]:
            return 'known_problem'  # Specific problem frames
        elif frame_id <= 30:
            return 'early_moderate'  # Early but less problematic
        else:
            return 'standard'  # Regular frames

    def select_strategies_for_category(self, category, frame):
        """Select strategies based on frame category."""
        strategies = []

        if category == 'early_difficult':
            # These frames have severe leg issues
            strategies.extend([
                ('lower_enhance_strong', self.enhance_lower_body(frame, strength=1.5), 0.15),
                ('lower_enhance', self.enhance_lower_body(frame), 0.2),
                ('bright_lower', self.brighten_lower_body(frame), 0.2),
                ('blur5', cv2.GaussianBlur(frame, (5, 5), 0), 0.2),
                ('clahe', self.enhance_contrast(frame), 0.25),
            ])

        elif category == 'rotation':
            # Rotation frames benefit from mirror strategy
            strategies.extend([
                ('mirror', cv2.flip(frame, 1), 0.2),
                ('mirror_enhanced', cv2.flip(self.enhance_contrast(frame), 1), 0.2),
                ('blur7', cv2.GaussianBlur(frame, (7, 7), 0), 0.3),
                ('standard', frame, 0.3),
            ])

        elif category == 'known_problem':
            # Known problem frames need aggressive strategies
            strategies.extend([
                ('lower_enhance', self.enhance_lower_body(frame), 0.2),
                ('bright', cv2.convertScaleAbs(frame, alpha=1.3, beta=30), 0.2),
                ('blur5', cv2.GaussianBlur(frame, (5, 5), 0), 0.25),
                ('clahe', self.enhance_contrast(frame), 0.2),
                ('low_conf', frame, 0.1),
            ])

        elif category == 'early_moderate':
            # Moderate enhancement for early frames
            strategies.extend([
                ('clahe', self.enhance_contrast(frame), 0.25),
                ('lower_enhance', self.enhance_lower_body(frame), 0.25),
                ('standard', frame, 0.3),
            ])

        else:  # standard
            # Most frames work well with standard approach
            strategies.extend([
                ('standard', frame, 0.3),
                ('clahe_light', self.enhance_contrast(frame, clip=1.5), 0.3),
            ])

        return strategies

    def detect_pose(self, frame, confidence=0.3, flip_back=False):
        """Run pose detection."""
        pose = mp.solutions.pose.Pose(
            static_image_mode=True,  # Always static to prevent tracking lock
            model_complexity=2,       # Maximum complexity
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

    def calculate_comprehensive_score(self, result, frame_id, strategy_name):
        """Calculate comprehensive quality score."""
        score = 0.0

        # 1. Leg visibility (50% weight for leg-focused optimization)
        leg_data = result[result['landmark_id'].isin(self.leg_landmarks)]
        if not leg_data.empty:
            leg_vis = leg_data['visibility'].mean()
            # Bonus for high leg visibility
            if leg_vis > 0.7:
                leg_vis *= 1.2
            score += leg_vis * 0.5
        else:
            return 0  # No legs = bad detection

        # 2. Critical joints (20% weight)
        critical_data = result[result['landmark_id'].isin(self.critical_leg)]
        if not critical_data.empty:
            critical_vis = critical_data['visibility'].mean()
            score += critical_vis * 0.2

        # 3. Overall visibility (20% weight)
        overall_vis = result['visibility'].mean()
        high_conf_ratio = (result['visibility'] > 0.7).sum() / len(result)
        score += (overall_vis * 0.7 + high_conf_ratio * 0.3) * 0.2

        # 4. Anatomical validity (10% weight)
        if self.is_anatomically_valid(result):
            score += 0.1

        # Strategy bonuses for specific frame types
        if 'mirror' in strategy_name and 40 <= frame_id <= 60:
            score *= 1.1  # Mirror bonus for rotation frames
        if 'lower_enhance' in strategy_name and frame_id <= 30:
            score *= 1.05  # Lower enhance bonus for early frames

        return score

    def is_anatomically_valid(self, result):
        """Check basic anatomical validity."""
        # Check if head is above hips
        nose = result[result['landmark_id'] == 0]
        left_hip = result[result['landmark_id'] == 23]
        right_hip = result[result['landmark_id'] == 24]

        if not nose.empty and not left_hip.empty:
            # In standing/dancing, head should be above hips
            avg_hip_y = (left_hip.iloc[0]['y'] + right_hip.iloc[0]['y']) / 2 if not right_hip.empty else left_hip.iloc[0]['y']
            if nose.iloc[0]['y'] > avg_hip_y + 0.1:  # Head significantly below hips
                return False

        # Check shoulder width is reasonable
        left_shoulder = result[result['landmark_id'] == 11]
        right_shoulder = result[result['landmark_id'] == 12]

        if not left_shoulder.empty and not right_shoulder.empty:
            shoulder_dist = abs(left_shoulder.iloc[0]['x'] - right_shoulder.iloc[0]['x'])
            if shoulder_dist < 0.05 or shoulder_dist > 0.5:
                return False

        return True

    def enhance_contrast(self, frame, clip=2.0):
        """CLAHE enhancement."""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    def enhance_lower_body(self, frame, strength=1.0):
        """Enhance lower body with adjustable strength."""
        h, w = frame.shape[:2]
        result = frame.copy()

        # Process lower 2/3
        lower_start = h // 3
        lower = result[lower_start:, :]

        # CLAHE enhancement
        lab = cv2.cvtColor(lower, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0 * strength, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        # Brightness adjustment
        if strength > 1.0:
            enhanced = cv2.convertScaleAbs(enhanced, alpha=1.1 * strength, beta=20)

        result[lower_start:, :] = enhanced
        return result

    def brighten_lower_body(self, frame):
        """Specifically brighten lower body."""
        h, w = frame.shape[:2]
        result = frame.copy()
        result[h//3:, :] = cv2.convertScaleAbs(result[h//3:, :], alpha=1.3, beta=30)
        return result

    def fallback_detection(self, frame, frame_id):
        """Last resort detection with very low confidence."""
        pose = mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.05,  # Extremely low
            min_tracking_confidence=0.05
        )

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        data = []
        if results.pose_landmarks:
            for idx, lm in enumerate(results.pose_landmarks.landmark):
                data.append({
                    'landmark_id': idx,
                    'x': lm.x,
                    'y': lm.y,
                    'z': lm.z,
                    'visibility': lm.visibility * 0.5  # Penalize low confidence
                })

        pose.close()

        if data:
            df = pd.DataFrame(data)
            df['frame_id'] = frame_id
            df['strategy'] = 'fallback_ultra_low'
            df['score'] = 0.1
            return df

        return None


def optimize_all_frames():
    """Optimize all 404 frames with unified approach."""
    print("🎯 UNIFIED OPTIMIZATION - COMBINING ALL LEARNINGS")
    print("="*60)

    optimizer = UnifiedOptimizer()
    frames_dir = Path('frames_complete_analysis')
    frame_files = sorted(frames_dir.glob("frame_*.png"))

    print(f"Processing {len(frame_files)} frames with unified optimization...")
    print("\nStrategy selection by category:")
    print("  - Early difficult (1-10): lower_enhance, brightness, blur")
    print("  - Rotation (40-60): mirror, blur7")
    print("  - Known problems: aggressive multi-strategy")
    print("  - Standard: minimal processing")
    print()

    all_results = []
    strategy_usage = {}
    category_count = {}

    for i, frame_path in enumerate(frame_files):
        frame_id = int(frame_path.stem.split('_')[1])
        frame = cv2.imread(str(frame_path))

        if frame is not None:
            category = optimizer.categorize_frame(frame_id)
            category_count[category] = category_count.get(category, 0) + 1

            result = optimizer.optimize_frame(frame, frame_id)

            if result is not None:
                strategy = result.iloc[0]['strategy'] if 'strategy' in result.columns else 'unknown'
                score = result.iloc[0]['score'] if 'score' in result.columns else 0
                strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1

                # Calculate leg visibility
                leg_data = result[result['landmark_id'].isin(optimizer.leg_landmarks)]
                leg_vis = leg_data['visibility'].mean() if not leg_data.empty else 0

                if frame_id % 20 == 0 or frame_id <= 10 or (40 <= frame_id <= 60 and frame_id % 5 == 0):
                    print(f"Frame {frame_id:3d}: {category:15s} -> {strategy:20s} (leg vis: {leg_vis:.3f}, score: {score:.3f})")

                for _, row in result.iterrows():
                    all_results.append(row.to_dict())

        if (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{len(frame_files)}")

    # Save results
    df_final = pd.DataFrame(all_results)
    output_path = 'creative_output/unified_optimized.csv'
    df_final.to_csv(output_path, index=False)

    print(f"\n✅ Optimization complete!")
    print(f"📁 Saved to: {output_path}")

    # Analysis
    print("\n📊 UNIFIED OPTIMIZATION REPORT")
    print("="*50)

    # Frame categories
    print("\nFrame Categories:")
    for cat, count in sorted(category_count.items()):
        print(f"  {cat:20s}: {count:3d} frames")

    # Strategy usage
    print("\nStrategy Usage:")
    for strategy, count in sorted(strategy_usage.items(), key=lambda x: -x[1])[:10]:
        print(f"  {strategy:20s}: {count:3d} frames")

    # Quality metrics
    total_frames = df_final['frame_id'].nunique()
    avg_vis = df_final['visibility'].mean()

    leg_data = df_final[df_final['landmark_id'].isin(optimizer.leg_landmarks)]
    avg_leg_vis = leg_data['visibility'].mean()

    critical_data = df_final[df_final['landmark_id'].isin(optimizer.critical_leg)]
    avg_critical_vis = critical_data['visibility'].mean()

    # Per-frame leg quality
    frames_with_good_legs = 0
    frames_with_poor_legs = 0

    for fid in range(404):
        frame_legs = df_final[(df_final['frame_id'] == fid) &
                              (df_final['landmark_id'].isin(optimizer.leg_landmarks))]
        if not frame_legs.empty:
            leg_mean = frame_legs['visibility'].mean()
            if leg_mean > 0.7:
                frames_with_good_legs += 1
            elif leg_mean < 0.5:
                frames_with_poor_legs += 1

    print(f"\nQuality Metrics:")
    print(f"  Total frames processed: {total_frames}/404")
    print(f"  Average visibility: {avg_vis:.3f}")
    print(f"  Average leg visibility: {avg_leg_vis:.3f}")
    print(f"  Average critical joint visibility: {avg_critical_vis:.3f}")
    print(f"  Frames with good legs (>70%): {frames_with_good_legs}")
    print(f"  Frames with poor legs (<50%): {frames_with_poor_legs}")

    # Early frames analysis
    early_frames = df_final[df_final['frame_id'] <= 30]
    early_leg_data = early_frames[early_frames['landmark_id'].isin(optimizer.leg_landmarks)]
    print(f"\nEarly frames (1-30) leg visibility: {early_leg_data['visibility'].mean():.3f}")

    # Rotation frames analysis
    rotation_frames = df_final[(df_final['frame_id'] >= 40) & (df_final['frame_id'] <= 60)]
    rotation_leg_data = rotation_frames[rotation_frames['landmark_id'].isin(optimizer.leg_landmarks)]
    print(f"Rotation frames (40-60) leg visibility: {rotation_leg_data['visibility'].mean():.3f}")

    return df_final


if __name__ == "__main__":
    optimize_all_frames()