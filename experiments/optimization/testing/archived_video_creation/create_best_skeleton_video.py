#!/usr/bin/env python
"""
Script to reproduce the best skeleton video (dance_skeleton_fixed_final.mp4).
This uses the comprehensive rotation fix that worked well.
"""

import os
import sys
import pandas as pd
import subprocess
from pathlib import Path

def create_best_skeleton_video(video_path='video/dance.mp4',
                               output_path='creative_output/dance_skeleton_best.mp4'):
    """
    Reproduce the dance_skeleton_fixed_final.mp4 approach.

    This approach:
    1. Runs initial pose detection
    2. Applies comprehensive rotation fix (reprocesses all frames with targeted strategies)
    3. Cleans the data (removes NaN, fixes column issues)
    4. Creates skeleton overlay video
    """

    print("🎥 Creating Best Skeleton Video")
    print("="*60)

    # Step 1: Check if initial pose detection exists
    poses_csv = 'creative_output/dance_poses.csv'

    if not Path(poses_csv).exists():
        print("📹 Running initial pose detection...")
        # Run the creative analyzer
        result = subprocess.run(['./run_creative.sh', video_path],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Pose detection failed")
            return False
    else:
        print("✓ Using existing pose data")

    # Step 2: Apply comprehensive rotation fix
    print("\n🔧 Applying comprehensive rotation fix...")

    # Run the targeted rotation fix
    result = subprocess.run(['python', 'targeted_rotation_fix.py'],
                          capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Rotation fix applied successfully")
        fixed_csv = 'creative_output/dance_poses_rotation_targeted.csv'
    else:
        print("⚠️ Rotation fix failed, using original data")
        fixed_csv = poses_csv

    # Step 3: Clean the data
    print("\n🧹 Cleaning data...")

    # Load and clean the data
    df = pd.read_csv(fixed_csv)

    # Remove NaN values
    df['x'] = df['x'].fillna(0.5)
    df['y'] = df['y'].fillna(0.5)
    df['z'] = df['z'].fillna(0.0)
    df['visibility'] = df['visibility'].fillna(0.5)

    # Remove _norm columns if they exist (they cause issues with drawing)
    if 'x_norm' in df.columns:
        df = df.drop(['x_norm', 'y_norm', 'z_norm'], axis=1, errors='ignore')

    # Save cleaned data
    clean_csv = 'creative_output/dance_poses_best_clean.csv'
    df.to_csv(clean_csv, index=False)
    print(f"✓ Data cleaned and saved to {clean_csv}")

    # Step 4: Create skeleton overlay video
    print("\n🎬 Creating skeleton overlay video...")

    result = subprocess.run([
        'python', 'create_skeleton_video.py',
        '--csv', clean_csv,
        '--output', output_path
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Video created successfully: {output_path}")
    else:
        print(f"❌ Video creation failed: {result.stderr}")
        return False

    # Step 5: Report statistics
    print("\n📊 Processing Statistics:")
    print(f"  Total frames: {df['frame_id'].nunique()}")
    print(f"  Total landmarks: {len(df)}")
    print(f"  Average visibility: {df['visibility'].mean():.2%}")

    # Check specific frames
    for frame_id in [3, 50, 100, 400]:
        frame_data = df[df['frame_id'] == frame_id]
        if not frame_data.empty:
            print(f"  Frame {frame_id}: {frame_data['visibility'].mean():.2%} visibility")

    print("\n✨ Best skeleton video created successfully!")
    print(f"📁 Output: {output_path}")

    return True

def create_best_with_optimization(video_path='video/dance.mp4'):
    """
    Create both regular and optimized versions.
    """
    print("🚀 Creating Best Skeleton Videos (Regular + Optimized)")
    print("="*60)

    # First create the regular version
    success = create_best_skeleton_video(
        video_path,
        'creative_output/dance_skeleton_best.mp4'
    )

    if not success:
        print("❌ Failed to create regular version")
        return

    # Then create optimized version with smoothing
    print("\n🎨 Creating optimized version with smoothing...")

    result = subprocess.run([
        'python', 'create_skeleton_video_optimized.py',
        '--csv', 'creative_output/dance_poses_best_clean.csv',
        '--output', 'creative_output/dance_skeleton_best_optimized.mp4',
        '--preset', 'smooth',
        '--smoothing', '10'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ Optimized version created")
    else:
        print("⚠️ Optimized version failed, but regular version is ready")

    print("\n" + "="*60)
    print("🏆 COMPLETE!")
    print("="*60)
    print("📁 Output files:")
    print("  • Regular: creative_output/dance_skeleton_best.mp4")
    print("  • Optimized: creative_output/dance_skeleton_best_optimized.mp4")
    print("\n💡 This approach handles:")
    print("  • Rotation/profile detection issues")
    print("  • Fast motion tracking problems")
    print("  • Comprehensive reprocessing with multiple strategies")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Create the best skeleton overlay video using proven approach'
    )

    parser.add_argument(
        '--video',
        default='video/dance.mp4',
        help='Input video path'
    )

    parser.add_argument(
        '--optimized',
        action='store_true',
        help='Also create optimized version with smoothing'
    )

    args = parser.parse_args()

    if args.optimized:
        create_best_with_optimization(args.video)
    else:
        create_best_skeleton_video(args.video)