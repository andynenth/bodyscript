#!/usr/bin/env python
"""
Practical fix that works with existing data - filters and smooths bad frames.
"""

import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d

def practical_fix(csv_path: str, output_path: str = None):
    """
    Practical approach: Identify good frames and smooth between them.
    """
    print("🔧 Applying Practical Rotation Fix")
    print("="*60)

    # Load data
    df = pd.read_csv(csv_path)

    # Step 1: Identify "good" frames based on anatomical plausibility
    print("Step 1: Identifying reliable frames...")

    good_frames = []
    frame_scores = {}

    for frame_id in df['frame_id'].unique():
        frame_data = df[df['frame_id'] == frame_id]

        # Calculate plausibility score
        score = 0

        # Check shoulder width (should be reasonable)
        left_shoulder = frame_data[frame_data['landmark_id'] == 11]['x'].values[0]
        right_shoulder = frame_data[frame_data['landmark_id'] == 12]['x'].values[0]
        shoulder_width = abs(right_shoulder - left_shoulder)

        if 0.15 < shoulder_width < 0.35:  # Good shoulder width
            score += 1

        # Check vertical alignment (shoulders above hips)
        shoulder_y = frame_data[frame_data['landmark_id'] == 11]['y'].values[0]
        hip_y = frame_data[frame_data['landmark_id'] == 23]['y'].values[0]

        if shoulder_y < hip_y:  # Shoulders above hips
            score += 1

        # Check symmetry
        left_conf = frame_data[frame_data['landmark_id'].isin([11,13,15,23,25,27])]['visibility'].mean()
        right_conf = frame_data[frame_data['landmark_id'].isin([12,14,16,24,26,28])]['visibility'].mean()

        if abs(left_conf - right_conf) < 0.2:  # Good symmetry
            score += 1

        frame_scores[frame_id] = score

        if score >= 2:  # At least 2 out of 3 criteria met
            good_frames.append(frame_id)

    print(f"  Found {len(good_frames)}/{len(frame_scores)} reliable frames")

    # Step 2: Smooth trajectories using only good frames as anchors
    print("Step 2: Smoothing trajectories...")

    df_fixed = df.copy()

    for landmark_id in range(33):
        landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')

        # Get data from good frames only
        good_data = landmark_data[landmark_data['frame_id'].isin(good_frames)]

        if len(good_data) > 3:  # Need at least 4 points to interpolate
            # Create interpolation functions
            f_x = interp1d(good_data['frame_id'].values, good_data['x'].values,
                          kind='cubic', fill_value='extrapolate')
            f_y = interp1d(good_data['frame_id'].values, good_data['y'].values,
                          kind='cubic', fill_value='extrapolate')

            # Interpolate all frames
            all_frame_ids = landmark_data['frame_id'].values

            try:
                smoothed_x = f_x(all_frame_ids)
                smoothed_y = f_y(all_frame_ids)

                # Apply smoothing filter
                if len(smoothed_x) > 5:
                    window_length = min(11, len(smoothed_x) if len(smoothed_x) % 2 == 1 else len(smoothed_x) - 1)
                    if window_length >= 5:
                        smoothed_x = savgol_filter(smoothed_x, window_length, 3)
                        smoothed_y = savgol_filter(smoothed_y, window_length, 3)

                # Update dataframe
                for i, frame_id in enumerate(all_frame_ids):
                    df_fixed.loc[(df_fixed['frame_id'] == frame_id) &
                                (df_fixed['landmark_id'] == landmark_id), 'x'] = smoothed_x[i]
                    df_fixed.loc[(df_fixed['frame_id'] == frame_id) &
                                (df_fixed['landmark_id'] == landmark_id), 'y'] = smoothed_y[i]

            except:
                # If interpolation fails, keep original
                pass

    # Step 3: Fix z-coordinates (just flatten them since they're unreliable)
    print("Step 3: Fixing depth coordinates...")
    df_fixed['z'] = df_fixed['z'] * 0.1  # Reduce z-variation

    # Step 4: Boost confidence for interpolated frames
    bad_frames = [f for f in frame_scores.keys() if f not in good_frames]
    for frame_id in bad_frames:
        df_fixed.loc[df_fixed['frame_id'] == frame_id, 'visibility'] *= 0.7

    # Save
    if output_path is None:
        output_path = csv_path.replace('.csv', '_practical_fix.csv')

    df_fixed.to_csv(output_path, index=False)

    print(f"\n✅ Fixed data saved to: {output_path}")
    print(f"📊 Statistics:")
    print(f"  Reliable frames used as anchors: {len(good_frames)}")
    print(f"  Interpolated frames: {len(bad_frames)}")
    print(f"  Success rate: {len(good_frames)/len(frame_scores)*100:.1f}%")

    return df_fixed

if __name__ == "__main__":
    import sys

    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'creative_output/dance_poses.csv'
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    practical_fix(csv_path, output_path)