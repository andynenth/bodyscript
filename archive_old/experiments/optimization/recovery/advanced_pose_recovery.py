#!/usr/bin/env python
"""
Advanced Pose Recovery System
Implements temporal coherence, region-specific enhancement, and intelligent interpolation
"""

import cv2
import numpy as np
import pandas as pd
import mediapipe as mp
from pathlib import Path
from scipy import interpolate
import json


class AdvancedPoseRecovery:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.1,  # Lower threshold to catch more
            min_tracking_confidence=0.1
        )
        self.results_cache = {}

    def detect_with_enhancement(self, frame, region='full'):
        """Apply region-specific enhancement before detection"""
        h, w = frame.shape[:2]

        if region == 'lower':
            # Focus on lower body with aggressive enhancement
            enhanced = frame.copy()
            lower_region = enhanced[h//2:, :]

            # Multiple enhancement strategies for lower body
            # 1. Extreme contrast boost
            lower_contrast = cv2.convertScaleAbs(lower_region, alpha=2.5, beta=30)

            # 2. CLAHE with high clip limit
            lab = cv2.cvtColor(lower_contrast, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
            l = clahe.apply(l)
            lower_enhanced = cv2.merge([l, a, b])
            lower_enhanced = cv2.cvtColor(lower_enhanced, cv2.COLOR_LAB2BGR)

            # 3. Edge enhancement
            edges = cv2.Canny(lower_region, 30, 100)
            edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            lower_final = cv2.addWeighted(lower_enhanced, 0.8, edges_colored, 0.2, 0)

            enhanced[h//2:, :] = lower_final

        elif region == 'upper':
            # Mild enhancement for upper body
            enhanced = frame.copy()
            upper_region = enhanced[:h//2, :]
            lab = cv2.cvtColor(upper_region, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            upper_enhanced = cv2.merge([l, a, b])
            enhanced[:h//2, :] = cv2.cvtColor(upper_enhanced, cv2.COLOR_LAB2BGR)

        else:
            enhanced = frame

        rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        return self.pose.process(rgb)

    def analyze_frame_advanced(self, frame):
        """Comprehensive frame analysis with multiple strategies"""
        results = {}

        # Standard detection
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results['standard'] = self.pose.process(rgb)

        # Region-specific detections
        results['lower_enhanced'] = self.detect_with_enhancement(frame, 'lower')
        results['upper_enhanced'] = self.detect_with_enhancement(frame, 'upper')

        # Rotation handling
        results['mirrored'] = self.pose.process(cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB))

        # Extreme preprocessing for difficult frames
        # Super bright
        bright = cv2.convertScaleAbs(frame, alpha=2.0, beta=50)
        results['bright'] = self.pose.process(cv2.cvtColor(bright, cv2.COLOR_BGR2RGB))

        # High contrast
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        thresh_bgr = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        results['threshold'] = self.pose.process(cv2.cvtColor(thresh_bgr, cv2.COLOR_BGR2RGB))

        return results

    def evaluate_detection_quality(self, result):
        """Evaluate if a detection is usable or catastrophic"""
        if not result or not result.pose_landmarks:
            return 0, 'no_detection'

        landmarks = result.pose_landmarks.landmark

        # Check critical landmarks
        critical_points = {
            'head': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Face and head
            'torso': [11, 12, 23, 24],  # Shoulders and hips
            'legs': [25, 26, 27, 28, 29, 30, 31, 32]  # Legs and feet
        }

        scores = {}
        for region, indices in critical_points.items():
            region_scores = [landmarks[i].visibility for i in indices]
            scores[region] = np.mean(region_scores)

        # Check for anatomical validity
        # Shoulders should be roughly horizontal
        shoulder_diff = abs(landmarks[11].y - landmarks[12].y)
        # Hips should be roughly horizontal
        hip_diff = abs(landmarks[23].y - landmarks[24].y)

        anatomical_score = 1.0
        if shoulder_diff > 0.2:  # Shoulders too tilted
            anatomical_score *= 0.5
        if hip_diff > 0.2:  # Hips too tilted
            anatomical_score *= 0.5

        # Check if legs are detected at all
        leg_detected = scores['legs'] > 0.3

        overall_score = np.mean(list(scores.values())) * anatomical_score

        if not leg_detected:
            return overall_score * 0.5, 'missing_legs'
        elif overall_score < 0.5:
            return overall_score, 'poor'
        elif overall_score < 0.7:
            return overall_score, 'moderate'
        else:
            return overall_score, 'good'

    def merge_best_parts(self, results):
        """Combine best detected parts from multiple strategies"""
        best_landmarks = []

        for landmark_idx in range(33):
            best_score = 0
            best_landmark = None
            best_strategy = None

            for strategy, result in results.items():
                if result and result.pose_landmarks:
                    landmark = result.pose_landmarks.landmark[landmark_idx]

                    # Adjust for mirrored
                    if strategy == 'mirrored':
                        landmark.x = 1.0 - landmark.x

                    if landmark.visibility > best_score:
                        best_score = landmark.visibility
                        best_landmark = landmark
                        best_strategy = strategy

            if best_landmark:
                best_landmarks.append({
                    'idx': landmark_idx,
                    'x': best_landmark.x,
                    'y': best_landmark.y,
                    'z': best_landmark.z,
                    'visibility': best_landmark.visibility,
                    'strategy': best_strategy
                })

        return best_landmarks

    def interpolate_pose(self, prev_frame_data, next_frame_data, t):
        """Intelligent interpolation between two good frames"""
        interpolated = []

        for idx in range(33):
            prev_lm = next((lm for lm in prev_frame_data if lm['idx'] == idx), None)
            next_lm = next((lm for lm in next_frame_data if lm['idx'] == idx), None)

            if prev_lm and next_lm:
                # Cubic interpolation for smooth motion
                x = prev_lm['x'] + (next_lm['x'] - prev_lm['x']) * t
                y = prev_lm['y'] + (next_lm['y'] - prev_lm['y']) * t
                z = prev_lm['z'] + (next_lm['z'] - prev_lm['z']) * t

                # Visibility decreases for interpolated frames
                visibility = min(prev_lm['visibility'], next_lm['visibility']) * 0.8

                interpolated.append({
                    'idx': idx,
                    'x': x,
                    'y': y,
                    'z': z,
                    'visibility': visibility,
                    'strategy': 'interpolated'
                })

        return interpolated

    def process_video_with_recovery(self, frames_dir, output_csv, key_frames_only=False):
        """Process all frames with advanced recovery"""
        frames_dir = Path(frames_dir)
        frame_files = sorted(frames_dir.glob("frame_*.png"))

        if key_frames_only:
            # For testing, only process specific frames
            test_frames = [0, 1, 2, 3, 4, 5, 48, 49, 50, 51, 52]
            frame_files = [f for f in frame_files
                          if int(f.stem.split('_')[1]) in test_frames]

        print(f"\n🔬 Processing {len(frame_files)} frames with advanced recovery...")

        all_detections = {}
        detection_quality = {}

        # Phase 1: Initial detection with multiple strategies
        print("\nPhase 1: Multi-strategy detection...")
        for frame_path in frame_files:
            frame_id = int(frame_path.stem.split('_')[1])
            frame = cv2.imread(str(frame_path))

            if frame is None:
                continue

            # Get all detection strategies
            results = self.analyze_frame_advanced(frame)

            # Merge best parts
            best_merged = self.merge_best_parts(results)

            # Evaluate quality
            # Check the standard result for quality assessment
            quality_score, quality_type = self.evaluate_detection_quality(results.get('standard'))

            all_detections[frame_id] = best_merged
            detection_quality[frame_id] = (quality_score, quality_type)

            if frame_id % 10 == 0:
                print(f"  Frame {frame_id}: {quality_type} (score: {quality_score:.3f})")

        # Phase 2: Identify frames needing interpolation
        print("\nPhase 2: Identifying frames for interpolation...")
        frames_to_interpolate = []

        for frame_id, (score, quality) in detection_quality.items():
            if quality in ['missing_legs', 'poor'] or score < 0.5:
                frames_to_interpolate.append(frame_id)
                print(f"  Frame {frame_id} marked for interpolation ({quality})")

        # Phase 3: Interpolate bad frames
        print("\nPhase 3: Applying intelligent interpolation...")
        for bad_frame in frames_to_interpolate:
            # Find nearest good frames
            prev_good = None
            next_good = None

            # Search backward for good frame
            for fid in range(bad_frame - 1, -1, -1):
                if fid in detection_quality:
                    score, quality = detection_quality[fid]
                    if quality in ['good', 'moderate'] and score > 0.6:
                        prev_good = fid
                        break

            # Search forward for good frame
            for fid in range(bad_frame + 1, max(all_detections.keys()) + 1):
                if fid in detection_quality:
                    score, quality = detection_quality[fid]
                    if quality in ['good', 'moderate'] and score > 0.6:
                        next_good = fid
                        break

            if prev_good is not None and next_good is not None:
                # Calculate interpolation position
                t = (bad_frame - prev_good) / (next_good - prev_good)

                # Interpolate
                interpolated = self.interpolate_pose(
                    all_detections[prev_good],
                    all_detections[next_good],
                    t
                )

                # Replace bad detection with interpolation
                all_detections[bad_frame] = interpolated
                print(f"  Frame {bad_frame}: Interpolated between {prev_good} and {next_good}")
            else:
                print(f"  Frame {bad_frame}: No good neighbors found, keeping merged result")

        # Phase 4: Save results
        print("\nPhase 4: Saving results...")
        rows = []

        for frame_id, landmarks in all_detections.items():
            for lm in landmarks:
                rows.append({
                    'frame_id': frame_id,
                    'landmark_id': lm['idx'],
                    'x': lm['x'],
                    'y': lm['y'],
                    'z': lm['z'],
                    'visibility': lm['visibility'],
                    'strategy': lm.get('strategy', 'unknown')
                })

        df = pd.DataFrame(rows)
        df.to_csv(output_csv, index=False)

        print(f"\n✅ Saved to: {output_csv}")

        # Report
        print("\n📊 RECOVERY REPORT:")
        print("=" * 50)
        print(f"Total frames: {len(all_detections)}")
        print(f"Interpolated frames: {len(frames_to_interpolate)}")
        print(f"Success rate: {(len(all_detections) - len(frames_to_interpolate)) / len(all_detections) * 100:.1f}%")

        # Quality breakdown
        quality_counts = {}
        for score, quality in detection_quality.values():
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        print("\nQuality distribution:")
        for quality, count in quality_counts.items():
            print(f"  {quality}: {count} frames")

        return df


def test_on_problem_frames():
    """Test specifically on known problem frames"""
    recovery = AdvancedPoseRecovery()

    # Process with recovery
    df = recovery.process_video_with_recovery(
        'frames_complete_analysis',
        'creative_output/advanced_recovery_test.csv',
        key_frames_only=True  # Test on subset first
    )

    # Create comparison visualizations
    print("\n🎨 Creating visual comparisons...")
    create_comparison_images(df)


def create_comparison_images(df):
    """Generate before/after comparison images"""
    import matplotlib.pyplot as plt

    test_frames = [3, 50]

    for frame_id in test_frames:
        frame_path = Path('frames_complete_analysis') / f"frame_{frame_id:06d}.png"
        if not frame_path.exists():
            continue

        frame = cv2.imread(str(frame_path))
        h, w = frame.shape[:2]

        # Get recovered pose data
        frame_data = df[df['frame_id'] == frame_id]

        # Draw skeleton
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils

        # Create figure
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))

        # Original (from true_every_frame)
        axes[0].imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        axes[0].set_title(f"Frame {frame_id} - Original Detection\n(Failed/Missing Legs)")
        axes[0].axis('off')

        # Recovered
        frame_copy = frame.copy()

        # Draw landmarks
        for _, landmark in frame_data.iterrows():
            x = int(landmark['x'] * w)
            y = int(landmark['y'] * h)

            # Color based on strategy
            if landmark['strategy'] == 'interpolated':
                color = (255, 0, 0)  # Blue for interpolated
            else:
                color = (0, 255, 0)  # Green for detected

            cv2.circle(frame_copy, (x, y), 4, color, -1)

        # Draw connections
        for connection in mp_pose.POSE_CONNECTIONS:
            start_idx, end_idx = connection

            start_data = frame_data[frame_data['landmark_id'] == start_idx]
            end_data = frame_data[frame_data['landmark_id'] == end_idx]

            if not start_data.empty and not end_data.empty:
                x1 = int(start_data.iloc[0]['x'] * w)
                y1 = int(start_data.iloc[0]['y'] * h)
                x2 = int(end_data.iloc[0]['x'] * w)
                y2 = int(end_data.iloc[0]['y'] * h)

                cv2.line(frame_copy, (x1, y1), (x2, y2), (0, 255, 255), 2)

        axes[1].imshow(cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB))
        axes[1].set_title(f"Frame {frame_id} - Advanced Recovery\n(Interpolated/Enhanced)")
        axes[1].axis('off')

        plt.suptitle(f"Advanced Pose Recovery - Frame {frame_id}")
        plt.tight_layout()

        output_path = f"creative_output/recovery_comparison_frame_{frame_id}.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  Saved comparison: {output_path}")


if __name__ == "__main__":
    print("🚀 ADVANCED POSE RECOVERY SYSTEM")
    print("=" * 60)
    test_on_problem_frames()