#!/usr/bin/env python
"""
Re-test the variations to confirm if improvements are consistent.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
from unified_optimization import UnifiedOptimizer


def test_specific_strategy(frame, strategy_name, params):
    """Test a specific strategy on a frame."""
    if strategy_name == 'blur':
        kernel = params['kernel']
        processed = cv2.GaussianBlur(frame, (kernel, kernel), 0)
        confidence = params.get('confidence', 0.2)
    elif strategy_name == 'clahe':
        clip = params['clip']
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        processed = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        confidence = params.get('confidence', 0.2)
    elif strategy_name == 'confidence':
        processed = frame
        confidence = params['confidence']
    else:
        processed = frame
        confidence = 0.3

    # Run detection
    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=confidence,
        min_tracking_confidence=confidence
    )

    rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb)

    leg_landmarks = [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]

    if result and result.pose_landmarks:
        leg_scores = []
        for idx in leg_landmarks:
            if idx < len(result.pose_landmarks.landmark):
                leg_scores.append(result.pose_landmarks.landmark[idx].visibility)
        avg_leg = np.mean(leg_scores) if leg_scores else 0
    else:
        avg_leg = 0

    pose.close()
    return avg_leg


def run_test_iteration(iteration_num):
    """Run one iteration of testing."""
    print(f"\n{'='*60}")
    print(f"🔄 ITERATION {iteration_num}")
    print(f"{'='*60}")

    optimizer = UnifiedOptimizer()
    frames_dir = Path('frames_complete_analysis')

    # Test the same frames with the strategies that showed improvement
    test_cases = [
        (5, 'blur', {'kernel': 3}),      # Frame 5 with blur_3
        (7, 'unified', {}),               # Frame 7 with unified
        (50, 'blur', {'kernel': 15}),     # Frame 50 with blur_15
        (100, 'blur', {'kernel': 7}),     # Frame 100 with blur_7
    ]

    results = {}

    for frame_id, strategy, params in test_cases:
        frame_path = frames_dir / f"frame_{frame_id:04d}.png"
        if not frame_path.exists():
            continue

        frame = cv2.imread(str(frame_path))

        # Get unified baseline
        baseline_result = optimizer.optimize_frame(frame, frame_id)
        baseline_leg = 0
        if baseline_result is not None:
            leg_data = baseline_result[baseline_result['landmark_id'].isin(optimizer.leg_landmarks)]
            baseline_leg = leg_data['visibility'].mean() if not leg_data.empty else 0

        # Test the specific strategy
        if strategy == 'unified':
            test_score = baseline_leg
            strategy_desc = 'unified'
        else:
            test_score = test_specific_strategy(frame, strategy, params)
            strategy_desc = f"{strategy}_{params}"

        results[frame_id] = {
            'baseline': baseline_leg,
            'test': test_score,
            'strategy': strategy_desc
        }

        status = ""
        if test_score > baseline_leg:
            improvement = (test_score - baseline_leg) / baseline_leg * 100
            status = f"✅ BETTER by {improvement:.1f}%"
        elif test_score < baseline_leg:
            degradation = (baseline_leg - test_score) / baseline_leg * 100
            status = f"❌ WORSE by {degradation:.1f}%"
        else:
            status = "= SAME"

        print(f"Frame {frame_id:3d}: Unified={baseline_leg:.3f}, Test={test_score:.3f} {status}")

    return results


def main():
    """Run multiple iterations to check consistency of improvements."""
    print("🔬 RE-TESTING VARIATION IMPROVEMENTS")
    print("="*60)
    print("Testing if the improvements are consistent...")
    print("\nPrevious findings:")
    print("  Frame 5: blur_3 was 30.5% better")
    print("  Frame 50: blur_15 was 1.7% better")
    print("  Frame 100: blur_7 was 7.4% better")
    print("\nLet's test 5 times to see if these hold true...")

    all_iterations = {}

    # Run 5 iterations
    for i in range(1, 6):
        iteration_results = run_test_iteration(i)
        all_iterations[i] = iteration_results

    # Analyze consistency
    print(f"\n{'='*60}")
    print("📊 CONSISTENCY ANALYSIS")
    print(f"{'='*60}")

    frame_consistency = {}

    for frame_id in [5, 7, 50, 100]:
        scores_baseline = []
        scores_test = []

        for iter_num, results in all_iterations.items():
            if frame_id in results:
                scores_baseline.append(results[frame_id]['baseline'])
                scores_test.append(results[frame_id]['test'])

        if scores_baseline and scores_test:
            baseline_std = np.std(scores_baseline)
            test_std = np.std(scores_test)

            baseline_mean = np.mean(scores_baseline)
            test_mean = np.mean(scores_test)

            frame_consistency[frame_id] = {
                'baseline_mean': baseline_mean,
                'baseline_std': baseline_std,
                'test_mean': test_mean,
                'test_std': test_std,
                'improvement': (test_mean - baseline_mean) / baseline_mean * 100 if baseline_mean > 0 else 0
            }

    # Display results
    for frame_id, stats in frame_consistency.items():
        print(f"\nFrame {frame_id}:")
        print(f"  Baseline: {stats['baseline_mean']:.3f} ± {stats['baseline_std']:.6f}")
        print(f"  Test:     {stats['test_mean']:.3f} ± {stats['test_std']:.6f}")

        if stats['baseline_std'] < 0.001 and stats['test_std'] < 0.001:
            print(f"  ✅ Both are PERFECTLY CONSISTENT")
        else:
            print(f"  ⚠️  Some variation detected")

        if stats['improvement'] > 0:
            print(f"  📈 Test is {stats['improvement']:.1f}% BETTER on average")
        elif stats['improvement'] < 0:
            print(f"  📉 Test is {abs(stats['improvement']):.1f}% WORSE on average")
        else:
            print(f"  = Test and baseline are EQUAL")

    # Final verdict
    print(f"\n{'='*60}")
    print("🎯 FINAL VERDICT")
    print(f"{'='*60}")

    improvements_consistent = []
    for frame_id, stats in frame_consistency.items():
        if stats['improvement'] > 0:
            improvements_consistent.append(frame_id)

    if improvements_consistent:
        print(f"✅ CONFIRMED: Improvements are REPRODUCIBLE for frames {improvements_consistent}")
        print("   The better strategies consistently outperform unified optimization")

        # Check if results get better or worse over iterations
        first_iter_avg = []
        last_iter_avg = []

        for frame_id in improvements_consistent:
            first_iter_avg.append(all_iterations[1][frame_id]['test'])
            last_iter_avg.append(all_iterations[5][frame_id]['test'])

        first_mean = np.mean(first_iter_avg)
        last_mean = np.mean(last_iter_avg)

        if abs(first_mean - last_mean) < 0.001:
            print("\n   Results are STABLE - neither better nor worse with repetition")
        elif last_mean > first_mean:
            print(f"\n   Results got {(last_mean-first_mean)/first_mean*100:.2f}% BETTER from iteration 1 to 5")
        else:
            print(f"\n   Results got {(first_mean-last_mean)/first_mean*100:.2f}% WORSE from iteration 1 to 5")
    else:
        print("❌ Previous improvements were NOT reproducible")

    # Test one more thing - try running same frame multiple times in a row
    print(f"\n{'='*60}")
    print("🔄 RAPID SUCCESSION TEST")
    print(f"{'='*60}")
    print("Testing frame 5 with blur_3 ten times in rapid succession...")

    frame_path = frames_dir / "frame_0005.png"
    frame = cv2.imread(str(frame_path))

    rapid_scores = []
    for i in range(10):
        score = test_specific_strategy(frame, 'blur', {'kernel': 3})
        rapid_scores.append(score)
        print(f"  Attempt {i+1:2d}: {score:.3f}")

    rapid_std = np.std(rapid_scores)
    rapid_mean = np.mean(rapid_scores)

    print(f"\nRapid test: {rapid_mean:.3f} ± {rapid_std:.6f}")
    if rapid_std < 0.001:
        print("✅ Perfectly consistent even in rapid succession")
    else:
        print(f"⚠️  Some variation detected: {rapid_std:.6f}")


if __name__ == "__main__":
    frames_dir = Path('frames_complete_analysis')
    main()