#!/usr/bin/env python
"""
Hybrid fix - Use aggressive reprocessing for rotation frames (40-60),
but preserve original for everything else.
"""

import pandas as pd
import numpy as np

def create_hybrid_fix():
    """
    Combine the best of both approaches:
    - Use fixed_clean data for frames 40-60 (better rotation handling)
    - Use original data for all other frames (preserve good detection)
    """
    print("🎯 Creating Hybrid Fix")
    print("="*60)

    # Load both datasets
    original = pd.read_csv('creative_output/dance_poses.csv')
    fixed_aggressive = pd.read_csv('creative_output/dance_poses_fixed_clean.csv')

    # Define frame ranges
    rotation_frames = list(range(40, 61))  # Frames with rotation issues

    print(f"📊 Hybrid Strategy:")
    print(f"  Frames 0-39: Use original (good detection)")
    print(f"  Frames 40-60: Use aggressive fix (rotation fix)")
    print(f"  Frames 61-404: Use original (good detection)")

    # Get original data for non-rotation frames
    original_keep = original[~original['frame_id'].isin(rotation_frames)]

    # Get fixed data for rotation frames
    fixed_rotation = fixed_aggressive[fixed_aggressive['frame_id'].isin(rotation_frames)]

    # Combine
    hybrid = pd.concat([original_keep, fixed_rotation], ignore_index=True)
    hybrid = hybrid.sort_values(['frame_id', 'landmark_id'])

    # Save
    output_path = 'creative_output/dance_poses_hybrid.csv'
    hybrid.to_csv(output_path, index=False)

    print(f"\n✅ Hybrid fix created!")
    print(f"📁 Saved to: {output_path}")

    # Verify the combination
    for test_frame in [0, 3, 10, 40, 50, 60, 100, 400]:
        frame_data = hybrid[hybrid['frame_id'] == test_frame]
        if not frame_data.empty:
            avg_vis = frame_data['visibility'].mean()
            source = "Fixed" if test_frame in rotation_frames else "Original"
            print(f"  Frame {test_frame}: {source} (visibility {avg_vis:.3f})")

    # Check quality metrics
    print(f"\n📈 Quality Metrics:")

    # Frame 3 (should have good legs from original)
    frame_3 = hybrid[hybrid['frame_id'] == 3]
    leg_ids = [25, 26, 27, 28, 29, 30, 31, 32]
    legs_3 = frame_3[frame_3['landmark_id'].isin(leg_ids)]
    print(f"  Frame 3 leg visibility: {legs_3['visibility'].mean():.3f}")

    # Frame 50 (should have rotation fix from aggressive)
    frame_50 = hybrid[hybrid['frame_id'] == 50]
    shoulders_50 = frame_50[frame_50['landmark_id'].isin([11, 12])]
    shoulder_width = abs(shoulders_50.iloc[0]['x'] - shoulders_50.iloc[1]['x'])
    print(f"  Frame 50 shoulder width: {shoulder_width:.3f} {'(profile)' if shoulder_width < 0.15 else '(frontal)'}")

    return output_path

if __name__ == "__main__":
    create_hybrid_fix()