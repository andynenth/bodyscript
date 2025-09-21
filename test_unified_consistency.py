#!/usr/bin/env python
"""
Test if unified optimization produces consistent results across multiple runs.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
from unified_optimization import UnifiedOptimizer
import json


def run_optimization_iteration(iteration_num):
    """Run one complete iteration of unified optimization on test frames."""
    print(f"\n{'='*60}")
    print(f"🔄 ITERATION {iteration_num}")
    print(f"{'='*60}")

    optimizer = UnifiedOptimizer()
    frames_dir = Path('frames_complete_analysis')

    # Test same frames as before
    test_frames = {
        'early_difficult': [3, 5, 6, 7, 8, 9, 10],
        'rotation': [50, 51, 52, 53],
        'known_problem': [73, 100, 206],
        'early_moderate': [15, 20, 25, 30]
    }

    results = {}

    for category, frame_ids in test_frames.items():
        category_results = []

        for frame_id in frame_ids:
            frame_path = frames_dir / f"frame_{frame_id:04d}.png"
            if not frame_path.exists():
                continue

            frame = cv2.imread(str(frame_path))

            # Run optimization
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

                category_results.append({
                    'frame_id': frame_id,
                    'strategy': strategy,
                    'score': score,
                    'leg_visibility': leg_vis,
                    'critical_visibility': critical_vis,
                    'overall_visibility': result['visibility'].mean()
                })

                print(f"  Frame {frame_id:3d}: {strategy:20s} | Leg: {leg_vis:.3f}")
            else:
                category_results.append({
                    'frame_id': frame_id,
                    'strategy': 'FAILED',
                    'score': 0,
                    'leg_visibility': 0,
                    'critical_visibility': 0,
                    'overall_visibility': 0
                })
                print(f"  Frame {frame_id:3d}: FAILED")

        results[category] = category_results

    return results


def analyze_consistency(all_iterations):
    """Analyze consistency across iterations."""
    print("\n" + "="*60)
    print("📊 CONSISTENCY ANALYSIS ACROSS ITERATIONS")
    print("="*60)

    # Organize by frame
    frame_results = {}

    for iter_num, iteration in all_iterations.items():
        for category, frames in iteration.items():
            for frame_data in frames:
                frame_id = frame_data['frame_id']
                if frame_id not in frame_results:
                    frame_results[frame_id] = []
                frame_results[frame_id].append(frame_data)

    # Analyze each frame
    consistency_report = []

    for frame_id in sorted(frame_results.keys()):
        iterations = frame_results[frame_id]

        # Extract metrics across iterations
        leg_scores = [it['leg_visibility'] for it in iterations]
        strategies = [it['strategy'] for it in iterations]
        scores = [it['score'] for it in iterations]

        # Calculate statistics
        leg_mean = np.mean(leg_scores)
        leg_std = np.std(leg_scores)
        leg_variation = (leg_std / leg_mean * 100) if leg_mean > 0 else 0

        score_mean = np.mean(scores)
        score_std = np.std(scores)

        # Check if strategy is consistent
        unique_strategies = list(set(strategies))
        strategy_consistent = len(unique_strategies) == 1

        consistency_report.append({
            'frame_id': frame_id,
            'leg_mean': leg_mean,
            'leg_std': leg_std,
            'leg_variation_pct': leg_variation,
            'score_mean': score_mean,
            'score_std': score_std,
            'strategies': unique_strategies,
            'strategy_consistent': strategy_consistent,
            'all_leg_values': leg_scores
        })

        # Print frames with variation
        if leg_std > 0.001:
            print(f"\nFrame {frame_id} VARIES:")
            print(f"  Leg visibility: {leg_scores}")
            print(f"  Mean: {leg_mean:.3f} ± {leg_std:.3f} (variation: {leg_variation:.2f}%)")
            print(f"  Strategies used: {unique_strategies}")

    # Overall consistency
    print("\n" + "-"*50)
    print("OVERALL CONSISTENCY:")

    total_frames = len(consistency_report)
    consistent_frames = sum(1 for r in consistency_report if r['leg_std'] < 0.001)
    strategy_consistent = sum(1 for r in consistency_report if r['strategy_consistent'])

    print(f"  Frames with identical results: {consistent_frames}/{total_frames} ({consistent_frames/total_frames*100:.1f}%)")
    print(f"  Frames with same strategy: {strategy_consistent}/{total_frames} ({strategy_consistent/total_frames*100:.1f}%)")

    # Average variation
    avg_variation = np.mean([r['leg_variation_pct'] for r in consistency_report])
    max_variation = max([r['leg_variation_pct'] for r in consistency_report])

    print(f"  Average leg visibility variation: {avg_variation:.3f}%")
    print(f"  Maximum variation: {max_variation:.3f}%")

    # Category analysis
    categories = {
        'early_difficult': [3, 5, 6, 7, 8, 9, 10],
        'rotation': [50, 51, 52, 53],
        'known_problem': [73, 100, 206],
        'early_moderate': [15, 20, 25, 30]
    }

    print("\n" + "-"*50)
    print("CONSISTENCY BY CATEGORY:")

    for cat_name, frame_ids in categories.items():
        cat_reports = [r for r in consistency_report if r['frame_id'] in frame_ids]
        if cat_reports:
            cat_consistent = sum(1 for r in cat_reports if r['leg_std'] < 0.001)
            cat_avg_var = np.mean([r['leg_variation_pct'] for r in cat_reports])
            print(f"  {cat_name:20s}: {cat_consistent}/{len(cat_reports)} consistent, avg variation: {cat_avg_var:.3f}%")

    return consistency_report


def compare_iteration_quality(all_iterations):
    """Compare overall quality between iterations."""
    print("\n" + "-"*50)
    print("QUALITY COMPARISON BETWEEN ITERATIONS:")

    for iter_num in sorted(all_iterations.keys()):
        iteration = all_iterations[iter_num]

        all_leg_scores = []
        all_scores = []

        for category, frames in iteration.items():
            for frame_data in frames:
                if frame_data['strategy'] != 'FAILED':
                    all_leg_scores.append(frame_data['leg_visibility'])
                    all_scores.append(frame_data['score'])

        if all_leg_scores:
            avg_leg = np.mean(all_leg_scores)
            avg_score = np.mean(all_scores)
            print(f"  Iteration {iter_num}: Avg leg visibility={avg_leg:.3f}, Avg score={avg_score:.3f}")


def main():
    """Run multiple iterations and analyze consistency."""
    print("🔬 TESTING UNIFIED OPTIMIZATION CONSISTENCY")
    print("="*60)
    print("Running same optimization 5 times to check for variation...")

    num_iterations = 5
    all_iterations = {}

    # Run multiple iterations
    for i in range(1, num_iterations + 1):
        iteration_results = run_optimization_iteration(i)
        all_iterations[i] = iteration_results

    # Analyze consistency
    consistency_report = analyze_consistency(all_iterations)

    # Compare quality
    compare_iteration_quality(all_iterations)

    # Final verdict
    print("\n" + "="*60)
    print("🎯 FINAL VERDICT:")
    print("="*60)

    # Check if completely deterministic
    all_consistent = all(r['leg_std'] < 0.001 for r in consistency_report)

    if all_consistent:
        print("✅ PERFECTLY CONSISTENT: Every frame produces IDENTICAL results across all iterations")
        print("   The unified optimization is DETERMINISTIC")
        print("   Results neither improve nor degrade - they are exactly the same")
    else:
        varying_frames = [r['frame_id'] for r in consistency_report if r['leg_std'] > 0.001]
        print(f"⚠️  SOME VARIATION DETECTED in frames: {varying_frames}")

        # Check if variation is meaningful
        max_var = max(r['leg_variation_pct'] for r in consistency_report)
        if max_var < 1.0:
            print(f"   However, variation is minimal (max {max_var:.3f}%)")
            print("   Results are PRACTICALLY CONSISTENT")
        else:
            print(f"   Variation is significant (up to {max_var:.3f}%)")

            # Check trend
            first_iter_leg = []
            last_iter_leg = []

            for frame_id, frame_data in consistency_report[0].items():
                if 'all_leg_values' in frame_data:
                    first_iter_leg.append(frame_data['all_leg_values'][0])
                    last_iter_leg.append(frame_data['all_leg_values'][-1])

            if first_iter_leg and last_iter_leg:
                first_avg = np.mean(first_iter_leg)
                last_avg = np.mean(last_iter_leg)

                if abs(first_avg - last_avg) < 0.001:
                    print("   No improvement or degradation between first and last iteration")
                elif last_avg > first_avg:
                    improvement = (last_avg - first_avg) / first_avg * 100
                    print(f"   📈 IMPROVEMENT: {improvement:.2f}% better on final iteration")
                else:
                    degradation = (first_avg - last_avg) / first_avg * 100
                    print(f"   📉 DEGRADATION: {degradation:.2f}% worse on final iteration")

    # Save detailed report
    report_data = {
        'num_iterations': num_iterations,
        'consistency_report': [
            {
                'frame_id': r['frame_id'],
                'leg_mean': float(r['leg_mean']),
                'leg_std': float(r['leg_std']),
                'leg_variation_pct': float(r['leg_variation_pct']),
                'strategy_consistent': r['strategy_consistent'],
                'strategies': r['strategies']
            }
            for r in consistency_report
        ],
        'all_consistent': all_consistent
    }

    with open('creative_output/unified_consistency_report.json', 'w') as f:
        json.dump(report_data, f, indent=2)

    print("\n📁 Detailed report saved to: creative_output/unified_consistency_report.json")


if __name__ == "__main__":
    main()