#!/usr/bin/env python
"""
Smart rotation detection and fixing with multiple criteria.
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import sys

def detect_rotation_issues(pose_df: pd.DataFrame) -> dict:
    """
    Detect rotation issues using multiple criteria.
    """
    issues = {
        'sudden_jumps': [],
        'impossible_poses': [],
        'low_confidence': [],
        'actual_profile': []
    }

    frames = sorted(pose_df['frame_id'].unique())

    for i, frame_id in enumerate(frames):
        frame_data = pose_df[pose_df['frame_id'] == frame_id]

        # 1. Check for sudden position jumps (impossible movement)
        if i > 0:
            prev_frame = pose_df[pose_df['frame_id'] == frames[i-1]]

            # Check major landmarks for sudden jumps
            for landmark_id in [11, 12, 23, 24]:  # Shoulders and hips
                curr = frame_data[frame_data['landmark_id'] == landmark_id]
                prev = prev_frame[prev_frame['landmark_id'] == landmark_id]

                if not curr.empty and not prev.empty:
                    movement = np.sqrt(
                        (curr.iloc[0]['x'] - prev.iloc[0]['x'])**2 +
                        (curr.iloc[0]['y'] - prev.iloc[0]['y'])**2
                    )

                    # Sudden jump threshold (>10% of frame in one frame)
                    if movement > 0.1:
                        issues['sudden_jumps'].append(frame_id)
                        break

        # 2. Check for anatomically impossible poses
        # Check if shoulders are behind hips (z-coordinate)
        left_shoulder = frame_data[frame_data['landmark_id'] == 11]
        left_hip = frame_data[frame_data['landmark_id'] == 23]

        if not left_shoulder.empty and not left_hip.empty:
            # If shoulder z is much different than hip z, it's suspicious
            z_diff = abs(left_shoulder.iloc[0]['z'] - left_hip.iloc[0]['z'])
            if z_diff > 0.3:  # Large z-difference indicates depth confusion
                issues['impossible_poses'].append(frame_id)

        # 3. Check for low overall confidence
        avg_confidence = frame_data['visibility'].mean()
        if avg_confidence < 0.7:
            issues['low_confidence'].append(frame_id)

        # 4. Better profile detection (multiple criteria)
        # Check shoulder-to-shoulder line vs nose position
        nose = frame_data[frame_data['landmark_id'] == 0]
        right_shoulder = frame_data[frame_data['landmark_id'] == 12]

        if not all([left_shoulder.empty, right_shoulder.empty, nose.empty]):
            # Calculate if nose is aligned with shoulder line (frontal)
            # or offset (profile)
            shoulder_center_x = (left_shoulder.iloc[0]['x'] + right_shoulder.iloc[0]['x']) / 2
            nose_offset = abs(nose.iloc[0]['x'] - shoulder_center_x)

            # Large offset indicates profile
            if nose_offset > 0.1:
                issues['actual_profile'].append(frame_id)

    # Remove duplicates and create combined problem frames list
    all_problems = set()
    for problem_list in issues.values():
        all_problems.update(problem_list)

    issues['all_problems'] = sorted(list(all_problems))

    return issues

def smart_interpolation(pose_df: pd.DataFrame, problem_frames: list) -> pd.DataFrame:
    """
    Smart interpolation that preserves good data and only fixes problems.
    """
    df_fixed = pose_df.copy()

    # Group consecutive problem frames
    frame_groups = []
    current_group = []

    for frame in problem_frames:
        if not current_group or frame == current_group[-1] + 1:
            current_group.append(frame)
        else:
            frame_groups.append(current_group)
            current_group = [frame]

    if current_group:
        frame_groups.append(current_group)

    print(f"Found {len(frame_groups)} groups of problematic frames to fix")

    for group in frame_groups:
        # Only interpolate if group is small (< 10 frames)
        # Larger groups might be legitimate movement
        if len(group) < 10:
            # Find good frames before and after
            all_frames = sorted(pose_df['frame_id'].unique())

            start_idx = all_frames.index(group[0])
            end_idx = all_frames.index(group[-1])

            prev_good = all_frames[start_idx - 1] if start_idx > 0 else None
            next_good = all_frames[end_idx + 1] if end_idx < len(all_frames) - 1 else None

            if prev_good is not None and next_good is not None:
                # Smooth interpolation across the group
                for i, bad_frame in enumerate(group):
                    alpha = (i + 1) / (len(group) + 1)

                    for landmark_id in range(33):
                        prev_lm = pose_df[(pose_df['frame_id'] == prev_good) &
                                         (pose_df['landmark_id'] == landmark_id)]
                        next_lm = pose_df[(pose_df['frame_id'] == next_good) &
                                         (pose_df['landmark_id'] == landmark_id)]

                        if not prev_lm.empty and not next_lm.empty:
                            # Interpolate with easing
                            # Use cosine interpolation for smoother results
                            alpha_smooth = (1 - np.cos(alpha * np.pi)) / 2

                            for col in ['x', 'y', 'z']:
                                if col in pose_df.columns:
                                    interp_val = (prev_lm.iloc[0][col] * (1 - alpha_smooth) +
                                                next_lm.iloc[0][col] * alpha_smooth)

                                    df_fixed.loc[(df_fixed['frame_id'] == bad_frame) &
                                               (df_fixed['landmark_id'] == landmark_id),
                                               col] = interp_val

                            # Mark as interpolated
                            df_fixed.loc[(df_fixed['frame_id'] == bad_frame) &
                                       (df_fixed['landmark_id'] == landmark_id),
                                       'interpolated'] = True

    return df_fixed

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Smart rotation detection and fixing'
    )

    parser.add_argument(
        '--csv',
        default='creative_output/dance_poses.csv',
        help='Input CSV path'
    )

    parser.add_argument(
        '--output',
        default='creative_output/dance_poses_smart_fixed.csv',
        help='Output CSV path'
    )

    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze, do not fix'
    )

    args = parser.parse_args()

    print("🔍 Smart Rotation Analysis")
    print("="*60)

    # Load data
    df = pd.read_csv(args.csv)

    # Detect issues
    issues = detect_rotation_issues(df)

    # Report findings
    total_frames = len(df['frame_id'].unique())

    print(f"📊 Detection Results:")
    print(f"  Total frames: {total_frames}")
    print(f"  Sudden jumps: {len(issues['sudden_jumps'])} frames")
    print(f"  Impossible poses: {len(issues['impossible_poses'])} frames")
    print(f"  Low confidence: {len(issues['low_confidence'])} frames")
    print(f"  Profile views: {len(issues['actual_profile'])} frames")
    print(f"  Total problems: {len(issues['all_problems'])} frames ({len(issues['all_problems'])/total_frames*100:.1f}%)")

    # Show sample problem frames
    if issues['sudden_jumps']:
        print(f"\n⚠️  Sudden jump frames: {issues['sudden_jumps'][:5]}...")
    if issues['impossible_poses']:
        print(f"⚠️  Impossible pose frames: {issues['impossible_poses'][:5]}...")

    if not args.analyze_only and issues['all_problems']:
        print(f"\n🔧 Applying smart fixes...")
        df_fixed = smart_interpolation(df, issues['all_problems'])

        # Save fixed version
        df_fixed.to_csv(args.output, index=False)
        print(f"✅ Fixed data saved to: {args.output}")

        # Verify improvement
        issues_after = detect_rotation_issues(df_fixed)
        print(f"\n📊 After fixing:")
        print(f"  Remaining problems: {len(issues_after['all_problems'])} frames")
        print(f"  Improvement: {len(issues['all_problems']) - len(issues_after['all_problems'])} frames fixed")

if __name__ == "__main__":
    main()