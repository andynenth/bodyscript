#!/usr/bin/env python
"""
Test unified optimization on problem frames first.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
from unified_optimization import UnifiedOptimizer


def test_on_problem_frames():
    """Test unified approach on known problem frames."""
    print("🧪 TESTING UNIFIED OPTIMIZATION ON PROBLEM FRAMES")
    print("="*60)

    optimizer = UnifiedOptimizer()
    frames_dir = Path('frames_complete_analysis')

    # Test on different categories
    test_frames = {
        'early_difficult': [3, 5, 6, 7, 8, 9, 10],
        'rotation': [50, 51, 52, 53],
        'known_problem': [73, 100, 206],
        'early_moderate': [15, 20, 25, 30]
    }

    all_results = []
    category_performance = {}

    for category, frame_ids in test_frames.items():
        print(f"\n📍 Testing {category} frames...")
        print("-"*40)

        category_scores = []
        category_leg_scores = []

        for frame_id in frame_ids:
            frame_path = frames_dir / f"frame_{frame_id:04d}.png"
            if not frame_path.exists():
                print(f"Frame {frame_id}: File not found")
                continue

            frame = cv2.imread(str(frame_path))

            # Get result from unified optimizer
            result = optimizer.optimize_frame(frame, frame_id)

            if result is not None:
                strategy = result.iloc[0]['strategy'] if 'strategy' in result.columns else 'unknown'
                score = result.iloc[0]['score'] if 'score' in result.columns else 0

                # Calculate leg visibility
                leg_data = result[result['landmark_id'].isin(optimizer.leg_landmarks)]
                leg_vis = leg_data['visibility'].mean() if not leg_data.empty else 0

                # Calculate critical joints
                critical_data = result[result['landmark_id'].isin(optimizer.critical_leg)]
                critical_vis = critical_data['visibility'].mean() if not critical_data.empty else 0

                print(f"  Frame {frame_id:3d}: {strategy:20s} | Leg: {leg_vis:.3f} | Critical: {critical_vis:.3f} | Score: {score:.3f}")

                category_scores.append(score)
                category_leg_scores.append(leg_vis)

                # Store for CSV
                for _, row in result.iterrows():
                    all_results.append(row.to_dict())
            else:
                print(f"  Frame {frame_id:3d}: FAILED")

        # Category statistics
        if category_scores:
            avg_score = np.mean(category_scores)
            avg_leg = np.mean(category_leg_scores)
            category_performance[category] = {
                'avg_score': avg_score,
                'avg_leg_visibility': avg_leg,
                'success_rate': len(category_scores) / len(frame_ids) * 100
            }

    # Compare with original
    print("\n📊 COMPARISON WITH ORIGINAL")
    print("-"*50)

    # Load original if exists
    original_path = 'creative_output/true_every_frame_optimized.csv'
    if Path(original_path).exists():
        df_original = pd.read_csv(original_path)

        for category, frame_ids in test_frames.items():
            orig_frames = df_original[df_original['frame_id'].isin(frame_ids)]
            if not orig_frames.empty:
                orig_leg_data = orig_frames[orig_frames['landmark_id'].isin(optimizer.leg_landmarks)]
                orig_leg_vis = orig_leg_data['visibility'].mean()

                if category in category_performance:
                    unified_leg = category_performance[category]['avg_leg_visibility']
                    improvement = (unified_leg - orig_leg_vis) / orig_leg_vis * 100
                    print(f"{category:20s}: Original={orig_leg_vis:.3f}, Unified={unified_leg:.3f} ({improvement:+.1f}%)")

    # Summary
    print("\n🎯 UNIFIED OPTIMIZATION PERFORMANCE")
    print("-"*50)

    for category, perf in category_performance.items():
        print(f"{category:20s}:")
        print(f"  Average Score: {perf['avg_score']:.3f}")
        print(f"  Leg Visibility: {perf['avg_leg_visibility']:.3f}")
        print(f"  Success Rate: {perf['success_rate']:.1f}%")

    # Save test results
    if all_results:
        df_test = pd.DataFrame(all_results)
        output_path = 'creative_output/unified_test_results.csv'
        df_test.to_csv(output_path, index=False)
        print(f"\n📁 Test results saved to: {output_path}")

        # Overall metrics
        avg_vis = df_test['visibility'].mean()
        leg_data = df_test[df_test['landmark_id'].isin(optimizer.leg_landmarks)]
        avg_leg = leg_data['visibility'].mean()

        print(f"\n✨ OVERALL TEST METRICS:")
        print(f"  Average visibility: {avg_vis:.3f}")
        print(f"  Average leg visibility: {avg_leg:.3f}")
        print(f"  Frames tested: {df_test['frame_id'].nunique()}")

    return all_results


def compare_strategies_side_by_side():
    """Direct comparison on specific frames."""
    print("\n\n🔄 SIDE-BY-SIDE STRATEGY COMPARISON")
    print("="*60)

    frames_dir = Path('frames_complete_analysis')
    optimizer = UnifiedOptimizer()

    # Test frame 5 (early difficult) with different approaches
    test_frame_id = 5
    frame_path = frames_dir / f"frame_{test_frame_id:04d}.png"
    frame = cv2.imread(str(frame_path))

    print(f"\nFrame {test_frame_id} - Early Difficult Category:")
    print("-"*50)

    strategies_to_test = [
        ('standard', frame, 0.3),
        ('low_conf', frame, 0.1),
        ('clahe', optimizer.enhance_contrast(frame), 0.25),
        ('lower_enhance', optimizer.enhance_lower_body(frame), 0.2),
        ('lower_enhance_strong', optimizer.enhance_lower_body(frame, strength=1.5), 0.15),
        ('bright_lower', optimizer.brighten_lower_body(frame), 0.2),
        ('blur5', cv2.GaussianBlur(frame, (5, 5), 0), 0.2)
    ]

    for strategy_name, processed_frame, confidence in strategies_to_test:
        result = optimizer.detect_pose(processed_frame, confidence)

        if result is not None:
            leg_data = result[result['landmark_id'].isin(optimizer.leg_landmarks)]
            leg_vis = leg_data['visibility'].mean() if not leg_data.empty else 0

            critical_data = result[result['landmark_id'].isin(optimizer.critical_leg)]
            critical_vis = critical_data['visibility'].mean() if not critical_data.empty else 0

            overall = result['visibility'].mean()

            print(f"{strategy_name:20s}: Overall={overall:.3f}, Leg={leg_vis:.3f}, Critical={critical_vis:.3f}")
        else:
            print(f"{strategy_name:20s}: FAILED")

    # Test frame 50 (rotation)
    test_frame_id = 50
    frame_path = frames_dir / f"frame_{test_frame_id:04d}.png"
    frame = cv2.imread(str(frame_path))

    print(f"\nFrame {test_frame_id} - Rotation Category:")
    print("-"*50)

    strategies_to_test = [
        ('standard', frame, 0.3),
        ('mirror', cv2.flip(frame, 1), 0.2),
        ('mirror_enhanced', cv2.flip(optimizer.enhance_contrast(frame), 1), 0.2),
        ('blur7', cv2.GaussianBlur(frame, (7, 7), 0), 0.3)
    ]

    for strategy_name, processed_frame, confidence in strategies_to_test:
        result = optimizer.detect_pose(processed_frame, confidence,
                                     flip_back=strategy_name.startswith('mirror'))

        if result is not None:
            leg_data = result[result['landmark_id'].isin(optimizer.leg_landmarks)]
            leg_vis = leg_data['visibility'].mean() if not leg_data.empty else 0

            overall = result['visibility'].mean()

            print(f"{strategy_name:20s}: Overall={overall:.3f}, Leg={leg_vis:.3f}")
        else:
            print(f"{strategy_name:20s}: FAILED")


if __name__ == "__main__":
    # Test on problem frames
    test_on_problem_frames()

    # Compare strategies directly
    compare_strategies_side_by_side()