#!/usr/bin/env python
"""
Comprehensive frame-by-frame analysis and optimization system.

Extracts all frames, analyzes each for specific issues, and creates
targeted fixes for optimal pose detection.
"""

import cv2
import pandas as pd
import numpy as np
import os
import shutil
from pathlib import Path
import mediapipe as mp
from typing import Dict, List, Tuple


class FrameAnalyzer:
    """Analyzes individual frames for pose detection issues."""

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.issues_found = {}

    def analyze_frame(self, frame_path: str, frame_id: int,
                      pose_data: pd.DataFrame) -> Dict:
        """
        Analyze a single frame for issues.

        Returns dict of issues found:
        - missing_limbs: Which limbs are disconnected
        - low_confidence: Which landmarks have low visibility
        - anatomical_errors: Impossible poses
        - temporal_jumps: Large movements from previous frame
        """
        issues = {
            'frame_id': frame_id,
            'missing_limbs': [],
            'low_confidence': [],
            'anatomical_errors': [],
            'temporal_jumps': [],
            'severity': 0  # 0=good, 1=minor, 2=moderate, 3=severe
        }

        # Get frame data
        frame_data = pose_data[pose_data['frame_id'] == frame_id]

        if frame_data.empty:
            issues['missing_limbs'] = ['all']
            issues['severity'] = 3
            return issues

        # Check for missing limbs (disconnected skeleton)
        limb_connections = [
            ('left_arm', [11, 13, 15]),
            ('right_arm', [12, 14, 16]),
            ('left_leg', [23, 25, 27, 29, 31]),
            ('right_leg', [24, 26, 28, 30, 32])
        ]

        for limb_name, landmarks in limb_connections:
            visibilities = []
            for lm_id in landmarks:
                lm_data = frame_data[frame_data['landmark_id'] == lm_id]
                if not lm_data.empty:
                    visibilities.append(lm_data.iloc[0]['visibility'])
                else:
                    visibilities.append(0)

            # Check if any part of limb has very low visibility
            if min(visibilities) < 0.3:
                issues['missing_limbs'].append(limb_name)

        # Check for low confidence landmarks
        low_conf = frame_data[frame_data['visibility'] < 0.5]
        if len(low_conf) > 0:
            landmark_names = {
                15: 'left_wrist', 16: 'right_wrist',
                25: 'left_knee', 26: 'right_knee',
                27: 'left_ankle', 28: 'right_ankle'
            }
            for _, row in low_conf.iterrows():
                lm_id = row['landmark_id']
                if lm_id in landmark_names:
                    issues['low_confidence'].append(
                        f"{landmark_names[lm_id]}:{row['visibility']:.2f}"
                    )

        # Check anatomical constraints
        # Example: Check if shoulders are reasonable distance apart
        left_shoulder = frame_data[frame_data['landmark_id'] == 11]
        right_shoulder = frame_data[frame_data['landmark_id'] == 12]

        if not left_shoulder.empty and not right_shoulder.empty:
            shoulder_dist = np.sqrt(
                (left_shoulder.iloc[0]['x'] - right_shoulder.iloc[0]['x'])**2 +
                (left_shoulder.iloc[0]['y'] - right_shoulder.iloc[0]['y'])**2
            )

            if shoulder_dist < 0.05 or shoulder_dist > 0.5:
                issues['anatomical_errors'].append(f'shoulder_width:{shoulder_dist:.3f}')

        # Calculate severity
        severity = 0
        if len(issues['missing_limbs']) > 0:
            severity = max(severity, 2)
        if len(issues['low_confidence']) > 3:
            severity = max(severity, 1)
        if len(issues['anatomical_errors']) > 0:
            severity = max(severity, 2)

        issues['severity'] = severity

        return issues


class FrameOptimizer:
    """Optimizes problematic frames with targeted strategies."""

    def __init__(self):
        self.strategies = {
            'missing_limbs': self.fix_missing_limbs,
            'low_confidence': self.fix_low_confidence,
            'anatomical_errors': self.fix_anatomical_errors
        }

    def fix_missing_limbs(self, frame: np.ndarray, issues: Dict) -> Dict:
        """Apply strategies to detect missing limbs."""
        results = {}

        # Try different preprocessing for each missing limb
        for limb in issues['missing_limbs']:
            if 'leg' in limb:
                # Enhance lower body
                enhanced = self.enhance_lower_body(frame)
                results[f'{limb}_enhanced'] = self.detect_pose(enhanced)

                # Try with blur
                blurred = cv2.GaussianBlur(frame, (7, 7), 0)
                results[f'{limb}_blurred'] = self.detect_pose(blurred)

            elif 'arm' in limb:
                # Try mirrored for arms
                mirrored = cv2.flip(frame, 1)
                results[f'{limb}_mirrored'] = self.detect_pose(mirrored, flip_back=True)

        return results

    def fix_low_confidence(self, frame: np.ndarray, issues: Dict) -> Dict:
        """Boost detection for low confidence landmarks."""
        results = {}

        # Apply CLAHE
        enhanced = self.apply_clahe(frame)
        results['clahe'] = self.detect_pose(enhanced)

        # Try multiple confidence levels
        for conf in [0.1, 0.15, 0.2]:
            results[f'conf_{conf}'] = self.detect_pose(
                frame, min_confidence=conf
            )

        return results

    def fix_anatomical_errors(self, frame: np.ndarray, issues: Dict) -> Dict:
        """Fix anatomically impossible poses."""
        results = {}

        # Use static detection to break tracking errors
        results['static'] = self.detect_pose(frame, static_mode=True)

        # Try with higher model complexity
        results['complex'] = self.detect_pose(frame, model_complexity=2)

        return results

    def enhance_lower_body(self, frame: np.ndarray) -> np.ndarray:
        """Enhance contrast in lower body region."""
        h, w = frame.shape[:2]
        result = frame.copy()

        # Apply CLAHE to lower 2/3
        lower = result[h//3:, :]
        lab = cv2.cvtColor(lower, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        result[h//3:, :] = enhanced

        return result

    def apply_clahe(self, frame: np.ndarray) -> np.ndarray:
        """Apply CLAHE to entire frame."""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    def detect_pose(self, frame: np.ndarray,
                   min_confidence: float = 0.2,
                   static_mode: bool = True,
                   model_complexity: int = 1,
                   flip_back: bool = False) -> pd.DataFrame:
        """Run pose detection with specified parameters."""

        pose = mp.solutions.pose.Pose(
            static_image_mode=static_mode,
            model_complexity=model_complexity,
            min_detection_confidence=min_confidence,
            min_tracking_confidence=min_confidence
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
        return pd.DataFrame(data)


def extract_all_frames(video_path: str, output_dir: str,
                       chunk_size: int = 50) -> List[str]:
    """Extract all frames from video in chunks."""
    print(f"📸 Extracting all frames from {video_path}")
    print("="*60)

    # Clean/create output directory
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True)

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frame_paths = []

    for i in range(total_frames):
        ret, frame = cap.read()
        if not ret:
            break

        frame_path = output_path / f"frame_{i:04d}.png"
        cv2.imwrite(str(frame_path), frame)
        frame_paths.append(str(frame_path))

        if (i + 1) % chunk_size == 0:
            print(f"  Extracted frames {i-chunk_size+2} to {i+1}")

    cap.release()
    print(f"✅ Extracted {len(frame_paths)} frames to {output_dir}")

    return frame_paths


def analyze_frame_batch(frame_paths: List[str],
                        start_idx: int,
                        pose_data: pd.DataFrame) -> pd.DataFrame:
    """Analyze a batch of frames for issues."""

    analyzer = FrameAnalyzer()
    optimizer = FrameOptimizer()

    all_issues = []
    fixes = []

    print(f"\n🔍 Analyzing frames {start_idx} to {start_idx + len(frame_paths) - 1}")

    for i, frame_path in enumerate(frame_paths):
        frame_id = start_idx + i

        # Analyze frame
        issues = analyzer.analyze_frame(frame_path, frame_id, pose_data)
        all_issues.append(issues)

        # If severe issues, try to fix
        if issues['severity'] >= 2:
            frame = cv2.imread(frame_path)

            # Try fixes based on issue type
            if issues['missing_limbs']:
                fix_results = optimizer.fix_missing_limbs(frame, issues)

                # Find best result
                best_score = 0
                best_data = None

                for strategy_name, data in fix_results.items():
                    if not data.empty:
                        score = data['visibility'].mean()
                        if score > best_score:
                            best_score = score
                            best_data = data

                if best_data is not None and best_score > 0.5:
                    best_data['frame_id'] = frame_id
                    fixes.append(best_data)
                    print(f"  Frame {frame_id}: Fixed with score {best_score:.2f}")

    # Create fixes dataframe
    if fixes:
        fixes_df = pd.concat(fixes, ignore_index=True)
        return fixes_df

    return pd.DataFrame()


def iterative_optimization(video_path: str = 'video/dance.mp4',
                          max_iterations: int = 3):
    """
    Iteratively optimize all frames until acceptable quality.
    """
    print("🚀 Starting Comprehensive Frame Optimization")
    print("="*60)

    # Load current best pose data
    pose_csv = 'creative_output/dance_poses_final_optimized.csv'
    if not Path(pose_csv).exists():
        pose_csv = 'creative_output/dance_poses_best_clean.csv'

    pose_data = pd.read_csv(pose_csv)

    iteration = 0
    chunk_size = 50

    while iteration < max_iterations:
        iteration += 1
        print(f"\n📊 ITERATION {iteration}")
        print("-"*40)

        # Extract all frames
        frame_dir = 'frames_analysis'
        frame_paths = extract_all_frames(video_path, frame_dir, chunk_size)

        # Analyze in chunks
        all_fixes = []
        problem_frames = []

        for chunk_start in range(0, len(frame_paths), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(frame_paths))
            chunk_paths = frame_paths[chunk_start:chunk_end]

            fixes_df = analyze_frame_batch(
                chunk_paths, chunk_start, pose_data
            )

            if not fixes_df.empty:
                all_fixes.append(fixes_df)
                problem_frames.extend(
                    fixes_df['frame_id'].unique().tolist()
                )

        print(f"\n📈 Iteration {iteration} Results:")
        print(f"  Problem frames found: {len(problem_frames)}")

        if len(problem_frames) == 0:
            print("✅ No severe issues found - optimization complete!")
            break

        # Apply fixes
        if all_fixes:
            fixes_df = pd.concat(all_fixes, ignore_index=True)

            # Merge with original data
            for frame_id in problem_frames:
                # Remove old data for this frame
                pose_data = pose_data[pose_data['frame_id'] != frame_id]

            # Add fixed data
            pose_data = pd.concat([pose_data, fixes_df], ignore_index=True)
            pose_data = pose_data.sort_values(['frame_id', 'landmark_id'])

            # Save updated data
            output_csv = f'creative_output/optimized_iter{iteration}.csv'
            pose_data.to_csv(output_csv, index=False)

            print(f"  Saved optimized data: {output_csv}")

            # Create video for this iteration
            output_video = f'creative_output/optimized_iter{iteration}.mp4'
            create_video(output_csv, output_video)

            print(f"  Created video: {output_video}")

        # Check if quality is acceptable
        high_conf = (pose_data['visibility'] > 0.6).sum()
        total = len(pose_data)
        quality = high_conf / total

        print(f"  Overall quality: {quality:.1%} high confidence")

        if quality > 0.85:
            print("🎯 Target quality reached!")
            break

    print("\n" + "="*60)
    print("✅ OPTIMIZATION COMPLETE")
    print(f"  Final quality: {quality:.1%}")
    print(f"  Iterations: {iteration}")


def create_video(csv_path: str, output_path: str):
    """Create skeleton overlay video."""
    import subprocess

    result = subprocess.run([
        'python', 'create_skeleton_video.py',
        '--csv', csv_path,
        '--output', output_path
    ], capture_output=True, text=True)

    return result.returncode == 0


if __name__ == "__main__":
    iterative_optimization()