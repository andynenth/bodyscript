#!/usr/bin/env python
"""
Fix rotation/profile detection issues in pose tracking.
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import sys
from typing import Tuple, List, Dict

def detect_profile_frames(pose_df: pd.DataFrame, threshold: float = 0.12) -> List[int]:
    """
    Detect frames where person is in profile view.

    Profile indicators:
    - Narrow shoulder width
    - Narrow hip width
    - Large difference in left/right visibility
    """
    profile_frames = []

    for frame_id in pose_df['frame_id'].unique():
        frame_data = pose_df[pose_df['frame_id'] == frame_id]

        # Get shoulder landmarks
        left_shoulder = frame_data[frame_data['landmark_id'] == 11]
        right_shoulder = frame_data[frame_data['landmark_id'] == 12]
        left_hip = frame_data[frame_data['landmark_id'] == 23]
        right_hip = frame_data[frame_data['landmark_id'] == 24]

        if not any([left_shoulder.empty, right_shoulder.empty,
                   left_hip.empty, right_hip.empty]):

            # Calculate widths
            if 'x_norm' in frame_data.columns:
                shoulder_width = abs(right_shoulder.iloc[0]['x_norm'] -
                                   left_shoulder.iloc[0]['x_norm'])
                hip_width = abs(right_hip.iloc[0]['x_norm'] -
                              left_hip.iloc[0]['x_norm'])
            else:
                shoulder_width = abs(right_shoulder.iloc[0]['x'] -
                                   left_shoulder.iloc[0]['x'])
                hip_width = abs(right_hip.iloc[0]['x'] -
                              left_hip.iloc[0]['x'])

            # Check for profile (narrow width)
            if shoulder_width < threshold or hip_width < threshold:
                profile_frames.append(frame_id)

    return profile_frames

def calculate_pose_quality(frame_data: pd.DataFrame) -> Dict[str, float]:
    """Calculate quality metrics for a single frame."""

    metrics = {}

    # 1. Width ratio (detects profile)
    left_shoulder = frame_data[frame_data['landmark_id'] == 11]
    right_shoulder = frame_data[frame_data['landmark_id'] == 12]
    left_hip = frame_data[frame_data['landmark_id'] == 23]
    right_hip = frame_data[frame_data['landmark_id'] == 24]

    if not any([left_shoulder.empty, right_shoulder.empty]):
        if 'x_norm' in frame_data.columns:
            shoulder_width = abs(right_shoulder.iloc[0]['x_norm'] -
                               left_shoulder.iloc[0]['x_norm'])
        else:
            shoulder_width = abs(right_shoulder.iloc[0]['x'] -
                               left_shoulder.iloc[0]['x'])
        metrics['shoulder_width'] = shoulder_width

    # 2. Visibility asymmetry
    left_side_landmarks = [11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31]
    right_side_landmarks = [12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]

    left_visibility = frame_data[frame_data['landmark_id'].isin(left_side_landmarks)]['visibility'].mean()
    right_visibility = frame_data[frame_data['landmark_id'].isin(right_side_landmarks)]['visibility'].mean()

    metrics['visibility_asymmetry'] = abs(left_visibility - right_visibility)

    # 3. Overall confidence
    metrics['avg_confidence'] = frame_data['visibility'].mean()

    # 4. Pose quality score
    # Good pose: wide shoulders, symmetric visibility, high confidence
    if 'shoulder_width' in metrics:
        width_score = min(metrics['shoulder_width'] / 0.2, 1.0)  # Normalize
    else:
        width_score = 0.5

    symmetry_score = 1.0 - metrics['visibility_asymmetry']
    confidence_score = metrics['avg_confidence']

    metrics['quality_score'] = (width_score * 0.4 +
                                symmetry_score * 0.3 +
                                confidence_score * 0.3)

    return metrics

def interpolate_bad_frames(pose_df: pd.DataFrame,
                          bad_frames: List[int],
                          window: int = 5) -> pd.DataFrame:
    """Interpolate pose data for frames with bad detection."""

    df_fixed = pose_df.copy()

    for bad_frame in bad_frames:
        # Find surrounding good frames
        all_frames = sorted(pose_df['frame_id'].unique())
        frame_idx = all_frames.index(bad_frame)

        # Find previous good frame
        prev_good = None
        for i in range(frame_idx - 1, max(-1, frame_idx - window - 1), -1):
            if i >= 0 and all_frames[i] not in bad_frames:
                prev_good = all_frames[i]
                break

        # Find next good frame
        next_good = None
        for i in range(frame_idx + 1, min(len(all_frames), frame_idx + window + 1)):
            if i < len(all_frames) and all_frames[i] not in bad_frames:
                next_good = all_frames[i]
                break

        if prev_good is not None and next_good is not None:
            # Interpolate each landmark
            alpha = (bad_frame - prev_good) / (next_good - prev_good)

            for landmark_id in range(33):
                prev_lm = pose_df[(pose_df['frame_id'] == prev_good) &
                                 (pose_df['landmark_id'] == landmark_id)]
                next_lm = pose_df[(pose_df['frame_id'] == next_good) &
                                 (pose_df['landmark_id'] == landmark_id)]

                if not prev_lm.empty and not next_lm.empty:
                    # Interpolate position
                    for col in ['x', 'y', 'z', 'x_norm', 'y_norm']:
                        if col in pose_df.columns:
                            interp_val = (prev_lm.iloc[0][col] * (1 - alpha) +
                                        next_lm.iloc[0][col] * alpha)

                            df_fixed.loc[(df_fixed['frame_id'] == bad_frame) &
                                       (df_fixed['landmark_id'] == landmark_id),
                                       col] = interp_val

                    # Mark as interpolated with lower confidence
                    df_fixed.loc[(df_fixed['frame_id'] == bad_frame) &
                               (df_fixed['landmark_id'] == landmark_id),
                               'visibility'] = 0.5  # Mark as interpolated

    return df_fixed

def analyze_rotation_issues(csv_path: str) -> Dict:
    """Analyze and report rotation/profile detection issues."""

    print("🔍 Analyzing Rotation Detection Issues...")
    print("="*60)

    # Load pose data
    df = pd.read_csv(csv_path)

    # Detect profile frames
    profile_frames = detect_profile_frames(df, threshold=0.12)

    # Calculate quality metrics for all frames
    quality_scores = {}
    for frame_id in df['frame_id'].unique():
        frame_data = df[df['frame_id'] == frame_id]
        metrics = calculate_pose_quality(frame_data)
        quality_scores[frame_id] = metrics

    # Identify bad frames (low quality score)
    bad_frames = [f for f, m in quality_scores.items()
                  if m.get('quality_score', 0) < 0.6]

    # Report findings
    total_frames = len(df['frame_id'].unique())
    print(f"📊 Analysis Results:")
    print(f"  Total frames: {total_frames}")
    print(f"  Profile frames detected: {len(profile_frames)} ({len(profile_frames)/total_frames*100:.1f}%)")
    print(f"  Low quality frames: {len(bad_frames)} ({len(bad_frames)/total_frames*100:.1f}%)")

    # Show specific problem frames
    if profile_frames:
        print(f"\n⚠️  Profile view frames (need attention):")
        print(f"  {profile_frames[:10]}{'...' if len(profile_frames) > 10 else ''}")

    # Quality distribution
    scores = [m.get('quality_score', 0) for m in quality_scores.values()]
    print(f"\n📈 Quality Score Distribution:")
    print(f"  Excellent (>0.8): {sum(1 for s in scores if s > 0.8)} frames")
    print(f"  Good (0.6-0.8): {sum(1 for s in scores if 0.6 <= s <= 0.8)} frames")
    print(f"  Poor (<0.6): {sum(1 for s in scores if s < 0.6)} frames")

    return {
        'profile_frames': profile_frames,
        'bad_frames': bad_frames,
        'quality_scores': quality_scores
    }

def fix_rotation_issues(csv_path: str, output_path: str = None):
    """Fix rotation issues by interpolating bad frames."""

    print("\n🔧 Fixing Rotation Issues...")
    print("="*60)

    # Analyze issues
    analysis = analyze_rotation_issues(csv_path)

    if not analysis['bad_frames']:
        print("✅ No significant rotation issues found!")
        return

    # Load data
    df = pd.read_csv(csv_path)

    # Interpolate bad frames
    print(f"\n🔄 Interpolating {len(analysis['bad_frames'])} problematic frames...")
    df_fixed = interpolate_bad_frames(df, analysis['bad_frames'])

    # Save fixed version
    if output_path is None:
        output_path = csv_path.replace('.csv', '_rotation_fixed.csv')

    df_fixed.to_csv(output_path, index=False)
    print(f"✅ Fixed data saved to: {output_path}")

    # Verify improvement
    print(f"\n📊 Verification:")
    profile_frames_after = detect_profile_frames(df_fixed, threshold=0.12)
    print(f"  Profile frames after fix: {len(profile_frames_after)}")

    return df_fixed

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyze and fix rotation detection issues in pose data'
    )

    parser.add_argument(
        '--csv',
        default='creative_output/dance_poses.csv',
        help='Path to pose data CSV'
    )

    parser.add_argument(
        '--fix',
        action='store_true',
        help='Apply fixes (interpolation) to problematic frames'
    )

    parser.add_argument(
        '--output',
        help='Output path for fixed CSV (default: adds _rotation_fixed suffix)'
    )

    args = parser.parse_args()

    if args.fix:
        fix_rotation_issues(args.csv, args.output)
    else:
        analyze_rotation_issues(args.csv)

if __name__ == "__main__":
    main()