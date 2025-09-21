#!/usr/bin/env python
"""
Test if running the same optimization multiple times produces different results.
Focus on problematic frames with leg issues.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path


def analyze_frame_multiple_times(frame_path, frame_id, num_iterations=5):
    """
    Analyze the same frame multiple times to see if results vary.
    """
    frame = cv2.imread(str(frame_path))
    if frame is None:
        return None

    results_per_iteration = []

    for iteration in range(num_iterations):
        # Run exact same detection multiple times
        pose = mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.2,
            min_tracking_confidence=0.2
        )

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)

        if result and result.pose_landmarks:
            # Calculate leg visibility
            leg_landmarks = [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
            leg_scores = []

            for idx in leg_landmarks:
                if idx < len(result.pose_landmarks.landmark):
                    vis = result.pose_landmarks.landmark[idx].visibility
                    leg_scores.append(vis)

            avg_leg_score = np.mean(leg_scores)

            # Focus on critical landmarks
            left_knee_vis = result.pose_landmarks.landmark[25].visibility
            right_knee_vis = result.pose_landmarks.landmark[26].visibility

            results_per_iteration.append({
                'iteration': iteration,
                'avg_leg_visibility': avg_leg_score,
                'left_knee': left_knee_vis,
                'right_knee': right_knee_vis
            })

        pose.close()

    return results_per_iteration


def compare_optimization_runs():
    """
    Compare multiple runs of the same optimization to check consistency.
    """
    print("🔄 TESTING OPTIMIZATION CONSISTENCY")
    print("="*60)

    # Test on frames known to have leg issues
    problem_frames = [3, 5, 6, 7, 8, 9, 10, 73, 100, 206]
    frames_dir = Path('frames_complete_analysis')

    print("Testing if same frame produces different results across iterations...")
    print()

    all_variations = []

    for frame_id in problem_frames:
        frame_path = frames_dir / f"frame_{frame_id:04d}.png"

        if frame_path.exists():
            print(f"Frame {frame_id}:")

            # Run analysis multiple times
            results = analyze_frame_multiple_times(frame_path, frame_id, num_iterations=5)

            if results:
                # Calculate variation
                leg_scores = [r['avg_leg_visibility'] for r in results]
                left_knee_scores = [r['left_knee'] for r in results]
                right_knee_scores = [r['right_knee'] for r in results]

                mean_leg = np.mean(leg_scores)
                std_leg = np.std(leg_scores)
                variation = (std_leg / mean_leg * 100) if mean_leg > 0 else 0

                print(f"  Leg visibility: {mean_leg:.3f} ± {std_leg:.3f} (variation: {variation:.1f}%)")
                print(f"  Left knee:  {np.mean(left_knee_scores):.3f} ± {np.std(left_knee_scores):.3f}")
                print(f"  Right knee: {np.mean(right_knee_scores):.3f} ± {np.std(right_knee_scores):.3f}")

                # Check if results are identical
                if std_leg < 0.001:
                    print(f"  ✅ IDENTICAL results across iterations")
                else:
                    print(f"  ⚠️ VARYING results across iterations")

                all_variations.append(variation)

            print()

    # Summary
    print("="*60)
    print("SUMMARY:")
    avg_variation = np.mean(all_variations)
    print(f"Average variation across all frames: {avg_variation:.2f}%")

    if avg_variation < 1:
        print("✅ Results are DETERMINISTIC - same input produces same output")
    else:
        print("⚠️ Results are NON-DETERMINISTIC - same input produces different outputs")


def run_iterative_optimization():
    """
    Run optimization multiple times on ALL frames to see if it improves or degrades.
    """
    print("\n🔁 ITERATIVE OPTIMIZATION TEST")
    print("="*60)

    frames_dir = Path('frames_complete_analysis')
    frame_files = sorted(frames_dir.glob("frame_*.png"))[:50]  # Test first 50 frames

    print(f"Running 3 iterations on first 50 frames...")

    iteration_results = {}

    for iteration in range(3):
        print(f"\n📍 ITERATION {iteration + 1}")
        print("-"*40)

        all_results = []

        for frame_path in frame_files:
            frame_id = int(frame_path.stem.split('_')[1])
            frame = cv2.imread(str(frame_path))

            # Simple detection
            pose = mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                min_detection_confidence=0.2,
                min_tracking_confidence=0.2
            )

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result and result.pose_landmarks:
                # Calculate leg score
                leg_landmarks = [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
                leg_scores = []

                for idx in leg_landmarks:
                    if idx < len(result.pose_landmarks.landmark):
                        vis = result.pose_landmarks.landmark[idx].visibility
                        leg_scores.append(vis)

                avg_leg = np.mean(leg_scores)
                all_results.append({
                    'frame_id': frame_id,
                    'leg_visibility': avg_leg,
                    'left_knee': result.pose_landmarks.landmark[25].visibility,
                    'right_knee': result.pose_landmarks.landmark[26].visibility
                })

            pose.close()

        # Store iteration results
        iteration_results[f'iteration_{iteration}'] = pd.DataFrame(all_results)

        # Calculate statistics
        df_iter = pd.DataFrame(all_results)
        avg_leg_vis = df_iter['leg_visibility'].mean()
        frames_below_50 = len(df_iter[df_iter['leg_visibility'] < 0.5])

        print(f"  Average leg visibility: {avg_leg_vis:.3f}")
        print(f"  Frames with <50% leg visibility: {frames_below_50}/50")

    # Compare iterations
    print("\n📊 COMPARISON ACROSS ITERATIONS:")
    print("-"*40)

    for i in range(len(iteration_results) - 1):
        curr = iteration_results[f'iteration_{i}']
        next = iteration_results[f'iteration_{i+1}']

        # Merge on frame_id
        merged = curr.merge(next, on='frame_id', suffixes=('_curr', '_next'))

        # Calculate differences
        merged['leg_diff'] = merged['leg_visibility_next'] - merged['leg_visibility_curr']

        improved = len(merged[merged['leg_diff'] > 0.01])
        worsened = len(merged[merged['leg_diff'] < -0.01])
        unchanged = len(merged[abs(merged['leg_diff']) <= 0.01])

        print(f"\nIteration {i} → {i+1}:")
        print(f"  Improved: {improved} frames")
        print(f"  Worsened: {worsened} frames")
        print(f"  Unchanged: {unchanged} frames")
        print(f"  Average change: {merged['leg_diff'].mean():.4f}")

    # Final verdict
    print("\n" + "="*60)
    print("VERDICT:")

    first_iter = iteration_results['iteration_0']['leg_visibility'].mean()
    last_iter = iteration_results[f'iteration_{len(iteration_results)-1}']['leg_visibility'].mean()

    if abs(first_iter - last_iter) < 0.001:
        print("✅ Results are CONSISTENT - multiple iterations produce same results")
        print("   MediaPipe is DETERMINISTIC for the same input")
    else:
        change = (last_iter - first_iter) / first_iter * 100
        if change > 0:
            print(f"📈 Results IMPROVED by {change:.1f}% over iterations")
        else:
            print(f"📉 Results DEGRADED by {abs(change):.1f}% over iterations")


if __name__ == "__main__":
    # First test: Check if same frame gives same results
    compare_optimization_runs()

    # Second test: Check if multiple iterations improve or degrade
    run_iterative_optimization()