#!/usr/bin/env python
"""
Quick consistency test on a few key frames.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
from unified_optimization import UnifiedOptimizer


def test_frame_consistency(frame_id, num_iterations=3):
    """Test if same frame produces consistent results."""
    frames_dir = Path('frames_complete_analysis')
    frame_path = frames_dir / f"frame_{frame_id:04d}.png"

    if not frame_path.exists():
        print(f"Frame {frame_id} not found")
        return None

    frame = cv2.imread(str(frame_path))
    optimizer = UnifiedOptimizer()

    results = []

    for i in range(num_iterations):
        result = optimizer.optimize_frame(frame, frame_id)

        if result is not None:
            strategy = result.iloc[0]['strategy'] if 'strategy' in result.columns else 'unknown'
            score = result.iloc[0]['score'] if 'score' in result.columns else 0

            # Calculate leg visibility
            leg_data = result[result['landmark_id'].isin(optimizer.leg_landmarks)]
            leg_vis = leg_data['visibility'].mean() if not leg_data.empty else 0

            # Get specific landmarks for detailed comparison
            left_knee = result[result['landmark_id'] == 25]['visibility'].values[0] if 25 in result['landmark_id'].values else 0
            right_knee = result[result['landmark_id'] == 26]['visibility'].values[0] if 26 in result['landmark_id'].values else 0

            results.append({
                'iteration': i + 1,
                'strategy': strategy,
                'score': score,
                'leg_visibility': leg_vis,
                'left_knee': left_knee,
                'right_knee': right_knee
            })

    return results


def main():
    """Quick consistency test."""
    print("🚀 QUICK CONSISTENCY TEST")
    print("="*60)
    print("Testing if unified optimization produces same results on repeated runs...")
    print()

    # Test a few key frames from each category
    test_frames = {
        'early_difficult': [5, 7],      # Frames with leg issues
        'rotation': [50, 51],            # Rotation frames
        'standard': [100, 200]           # Regular frames
    }

    all_results = {}

    for category, frame_ids in test_frames.items():
        print(f"\n📍 Testing {category} frames:")
        print("-"*40)

        for frame_id in frame_ids:
            print(f"\nFrame {frame_id} (3 iterations):")

            results = test_frame_consistency(frame_id, num_iterations=3)

            if results:
                all_results[frame_id] = results

                # Check consistency
                strategies = [r['strategy'] for r in results]
                leg_scores = [r['leg_visibility'] for r in results]
                scores = [r['score'] for r in results]
                left_knees = [r['left_knee'] for r in results]
                right_knees = [r['right_knee'] for r in results]

                # Display results
                for r in results:
                    print(f"  Iter {r['iteration']}: {r['strategy']:20s} | Leg: {r['leg_visibility']:.3f} | Score: {r['score']:.3f}")

                # Check variation
                leg_std = np.std(leg_scores)
                score_std = np.std(scores)

                if leg_std < 0.001 and score_std < 0.001:
                    print(f"  ✅ IDENTICAL across all iterations")
                else:
                    print(f"  ⚠️  VARIATION detected:")
                    print(f"      Leg visibility: {leg_scores}")
                    print(f"      Std deviation: {leg_std:.6f}")

    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY:")
    print("-"*40)

    total_frames = len(all_results)
    consistent_frames = 0

    for frame_id, results in all_results.items():
        leg_scores = [r['leg_visibility'] for r in results]
        if np.std(leg_scores) < 0.001:
            consistent_frames += 1

    print(f"Frames tested: {total_frames}")
    print(f"Perfectly consistent: {consistent_frames}/{total_frames}")

    if consistent_frames == total_frames:
        print("\n✅ CONCLUSION: Unified optimization is DETERMINISTIC")
        print("   Same input → Same output every time")
        print("   Results do NOT get better or worse with iterations")
    else:
        varying_frames = [fid for fid, results in all_results.items()
                         if np.std([r['leg_visibility'] for r in results]) >= 0.001]
        print(f"\n⚠️  CONCLUSION: Some variation in frames {varying_frames}")

        # Check if there's a trend
        first_iter_avg = np.mean([results[0]['leg_visibility'] for results in all_results.values()])
        last_iter_avg = np.mean([results[-1]['leg_visibility'] for results in all_results.values()])

        diff = last_iter_avg - first_iter_avg
        if abs(diff) < 0.001:
            print("   No meaningful difference between first and last iteration")
        elif diff > 0:
            print(f"   Slight improvement: {diff:.4f} ({diff/first_iter_avg*100:.2f}%)")
        else:
            print(f"   Slight degradation: {diff:.4f} ({diff/first_iter_avg*100:.2f}%)")


if __name__ == "__main__":
    main()