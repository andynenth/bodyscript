#!/usr/bin/env python
"""
FINAL OPTIMIZED MediaPipe Implementation
Combines all strategies and learnings for best possible MediaPipe-only results
"""

import cv2
import numpy as np
import pandas as pd
import mediapipe as mp
from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional


class MediaPipeFinalOptimized:
    """Ultimate MediaPipe optimization combining all successful strategies"""

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        # Multiple pose detectors with different settings
        self.detectors = {
            'high_accuracy': self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                min_detection_confidence=0.1,
                min_tracking_confidence=0.1
            ),
            'balanced': self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=1,
                min_detection_confidence=0.3,
                min_tracking_confidence=0.3
            ),
            'fast': self.mp_pose.Pose(
                static_image_mode=False,  # Use tracking
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        }

    def preprocess_strategies(self, frame: np.ndarray) -> Dict[str, np.ndarray]:
        """Generate all preprocessing variations"""
        h, w = frame.shape[:2]
        strategies = {}

        # 1. Original
        strategies['original'] = frame

        # 2. Brightness variations
        strategies['bright'] = cv2.convertScaleAbs(frame, alpha=1.5, beta=30)
        strategies['very_bright'] = cv2.convertScaleAbs(frame, alpha=2.0, beta=50)

        # 3. Contrast enhancement
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        strategies['clahe'] = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

        # 4. Noise reduction
        strategies['bilateral'] = cv2.bilateralFilter(frame, 9, 75, 75)
        strategies['gaussian'] = cv2.GaussianBlur(frame, (5, 5), 0)

        # 5. Sharpening
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        strategies['sharpened'] = cv2.filter2D(frame, -1, kernel)

        # 6. Histogram equalization
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
        strategies['hist_eq'] = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

        # 7. Mirrored
        strategies['mirrored'] = cv2.flip(frame, 1)

        # 8. Region-specific enhancement (lower body)
        enhanced_lower = frame.copy()
        lower_region = enhanced_lower[h//2:, :]
        lower_bright = cv2.convertScaleAbs(lower_region, alpha=2.5, beta=40)
        enhanced_lower[h//2:, :] = lower_bright
        strategies['lower_enhanced'] = enhanced_lower

        # 9. Edge enhancement
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        strategies['edge_enhanced'] = cv2.addWeighted(frame, 0.7, edges_colored, 0.3, 0)

        # 10. Gamma correction
        gamma = 1.5
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255
                         for i in np.arange(0, 256)]).astype("uint8")
        strategies['gamma_corrected'] = cv2.LUT(frame, table)

        return strategies

    def detect_all_strategies(self, frame: np.ndarray) -> Dict:
        """Run detection on all preprocessing strategies with all models"""
        strategies = self.preprocess_strategies(frame)
        results = {}

        for strategy_name, processed_frame in strategies.items():
            rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)

            # Try with different detectors
            for detector_name, detector in self.detectors.items():
                key = f"{strategy_name}_{detector_name}"
                try:
                    result = detector.process(rgb)
                    if result and result.pose_landmarks:
                        results[key] = {
                            'result': result,
                            'strategy': strategy_name,
                            'detector': detector_name
                        }
                except:
                    continue

        return results

    def calculate_landmark_quality(self, landmarks) -> Dict:
        """Calculate quality metrics for landmarks"""
        if not landmarks:
            return {'overall': 0, 'upper': 0, 'lower': 0, 'visibility': 0}

        # Group landmarks by body region
        upper_indices = list(range(0, 11)) + [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
        lower_indices = [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]

        upper_vis = [landmarks.landmark[i].visibility for i in upper_indices]
        lower_vis = [landmarks.landmark[i].visibility for i in lower_indices]
        all_vis = [lm.visibility for lm in landmarks.landmark]

        # Check anatomical constraints
        shoulder_width = abs(landmarks.landmark[11].x - landmarks.landmark[12].x)
        hip_width = abs(landmarks.landmark[23].x - landmarks.landmark[24].x)

        # Penalize impossible poses
        anatomical_score = 1.0
        if shoulder_width < 0.05 or shoulder_width > 0.5:
            anatomical_score *= 0.5
        if hip_width < 0.05 or hip_width > 0.4:
            anatomical_score *= 0.5

        return {
            'overall': np.mean(all_vis) * anatomical_score,
            'upper': np.mean(upper_vis),
            'lower': np.mean(lower_vis),
            'visibility': np.mean(all_vis),
            'anatomical': anatomical_score
        }

    def select_best_detection(self, results: Dict) -> Tuple[Optional[object], str, Dict]:
        """Select best detection from all attempts"""
        best_score = 0
        best_result = None
        best_key = None
        best_metrics = None

        for key, data in results.items():
            metrics = self.calculate_landmark_quality(data['result'].pose_landmarks)

            # Weighted score prioritizing lower body and anatomical correctness
            score = (metrics['overall'] * 0.3 +
                    metrics['lower'] * 0.4 +
                    metrics['anatomical'] * 0.3)

            if score > best_score:
                best_score = score
                best_result = data['result']
                best_key = key
                best_metrics = metrics

        return best_result, best_key, best_metrics

    def smart_temporal_smoothing(self, all_frames_data: Dict, window_size: int = 5) -> Dict:
        """Apply temporal smoothing while preserving good detections"""
        smoothed = {}
        frame_ids = sorted(all_frames_data.keys())

        for frame_id in frame_ids:
            current_data = all_frames_data[frame_id]

            # Check if current frame needs smoothing
            if current_data['metrics']['overall'] > 0.7:
                # Good detection, keep as is
                smoothed[frame_id] = current_data
            else:
                # Poor detection, apply smoothing
                window_start = max(0, frame_id - window_size // 2)
                window_end = min(max(frame_ids), frame_id + window_size // 2)

                # Collect neighboring good frames
                good_neighbors = []
                for fid in range(window_start, window_end + 1):
                    if fid in all_frames_data and all_frames_data[fid]['metrics']['overall'] > 0.6:
                        good_neighbors.append(all_frames_data[fid])

                if len(good_neighbors) >= 2:
                    # Apply weighted average based on quality
                    smoothed[frame_id] = self.weighted_average_poses(good_neighbors, current_data)
                else:
                    # Not enough good neighbors, keep original
                    smoothed[frame_id] = current_data

        return smoothed

    def weighted_average_poses(self, good_poses: List, current_pose: Dict) -> Dict:
        """Compute weighted average of poses based on quality"""
        weights = [p['metrics']['overall'] for p in good_poses]
        total_weight = sum(weights)

        if total_weight == 0:
            return current_pose

        # Average landmarks
        averaged_landmarks = []
        for i in range(33):
            x, y, z, vis = 0, 0, 0, 0

            for pose, weight in zip(good_poses, weights):
                if pose['result'] and pose['result'].pose_landmarks:
                    lm = pose['result'].pose_landmarks.landmark[i]
                    x += lm.x * weight
                    y += lm.y * weight
                    z += lm.z * weight
                    vis += lm.visibility * weight

            x /= total_weight
            y /= total_weight
            z /= total_weight
            vis /= total_weight

            averaged_landmarks.append({
                'x': x, 'y': y, 'z': z, 'visibility': vis
            })

        current_pose['smoothed_landmarks'] = averaged_landmarks
        current_pose['smoothed'] = True

        return current_pose

    def process_video_final(self, frames_dir: str, output_csv: str,
                           sample_only: bool = False) -> pd.DataFrame:
        """Final optimized processing pipeline"""
        frames_dir = Path(frames_dir)
        frame_files = sorted(frames_dir.glob("frame_*.png"))

        if sample_only:
            # Test on problematic frames
            test_frames = [1, 2, 3, 4, 5, 48, 49, 50, 51, 52, 100, 200, 300, 400]
            frame_files = [f for f in frame_files
                          if int(f.stem.split('_')[1]) in test_frames]

        print(f"\n🎯 FINAL MediaPipe Processing")
        print(f"{'='*60}")
        print(f"Processing {len(frame_files)} frames...")
        print(f"Strategies: 10 preprocessing × 3 models = 30 attempts per frame")
        print()

        all_detections = {}

        # Process each frame
        for idx, frame_path in enumerate(frame_files):
            frame_id = int(frame_path.stem.split('_')[1])
            frame = cv2.imread(str(frame_path))

            if frame is None:
                continue

            # Try all strategies
            results = self.detect_all_strategies(frame)

            # Select best
            best_result, best_key, metrics = self.select_best_detection(results)

            if best_result:
                all_detections[frame_id] = {
                    'result': best_result,
                    'strategy': best_key,
                    'metrics': metrics,
                    'frame_path': frame_path
                }

                if frame_id in [3, 50] or frame_id % 50 == 0:
                    print(f"Frame {frame_id:3d}: {best_key:25s} "
                          f"(overall: {metrics['overall']:.2f}, "
                          f"lower: {metrics['lower']:.2f})")
            else:
                print(f"Frame {frame_id:3d}: FAILED - no detection")

            if (idx + 1) % 100 == 0:
                print(f"Progress: {idx+1}/{len(frame_files)}")

        # Apply temporal smoothing
        print("\nApplying temporal smoothing...")
        smoothed_data = self.smart_temporal_smoothing(all_detections)

        # Convert to DataFrame
        rows = []
        for frame_id, data in smoothed_data.items():
            if 'smoothed_landmarks' in data:
                # Use smoothed landmarks
                for idx, lm in enumerate(data['smoothed_landmarks']):
                    rows.append({
                        'frame_id': frame_id,
                        'landmark_id': idx,
                        'x': lm['x'],
                        'y': lm['y'],
                        'z': lm['z'],
                        'visibility': lm['visibility'],
                        'strategy': f"{data['strategy']}_smoothed"
                    })
            elif data['result'] and data['result'].pose_landmarks:
                # Use original detection
                for idx, lm in enumerate(data['result'].pose_landmarks.landmark):
                    # Handle mirrored
                    x = lm.x
                    if 'mirrored' in data['strategy']:
                        x = 1.0 - x

                    rows.append({
                        'frame_id': frame_id,
                        'landmark_id': idx,
                        'x': x,
                        'y': lm.y,
                        'z': lm.z,
                        'visibility': lm.visibility,
                        'strategy': data['strategy']
                    })

        df = pd.DataFrame(rows)
        df.to_csv(output_csv, index=False)

        # Generate report
        print(f"\n{'='*60}")
        print("📊 FINAL RESULTS REPORT")
        print(f"{'='*60}")
        print(f"Frames processed: {len(all_detections)}")
        print(f"Successful detections: {len([d for d in all_detections.values() if d['result']])}")

        # Strategy distribution
        strategy_counts = {}
        for data in all_detections.values():
            strategy = data['strategy'].split('_')[0]
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        print("\nTop strategies used:")
        for strategy, count in sorted(strategy_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"  {strategy:20s}: {count:3d} frames")

        # Quality analysis
        avg_overall = np.mean([d['metrics']['overall'] for d in all_detections.values()])
        avg_lower = np.mean([d['metrics']['lower'] for d in all_detections.values()])

        print(f"\nAverage quality scores:")
        print(f"  Overall: {avg_overall:.2%}")
        print(f"  Lower body: {avg_lower:.2%}")

        print(f"\n✅ Saved to: {output_csv}")

        return df


def main():
    """Run final optimized MediaPipe processing"""

    processor = MediaPipeFinalOptimized()

    # Test on sample frames first
    print("Testing on sample frames...")
    df = processor.process_video_final(
        'frames_complete_analysis',
        'creative_output/mediapipe_final_sample.csv',
        sample_only=True
    )

    print("\n" + "="*60)
    print("Sample processing complete!")
    print("To process full video, set sample_only=False")


if __name__ == "__main__":
    main()