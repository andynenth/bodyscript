#!/usr/bin/env python
"""
Test if varying optimization parameters makes results better or worse.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
from unified_optimization import UnifiedOptimizer


class OptimizationVariationTester:
    """Test different variations of optimization parameters."""

    def __init__(self):
        self.leg_landmarks = [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        self.critical_leg = [25, 26, 27, 28]

    def test_confidence_variations(self, frame, frame_id):
        """Test different confidence thresholds."""
        results = {}

        confidence_levels = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5]

        for conf in confidence_levels:
            pose = mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                min_detection_confidence=conf,
                min_tracking_confidence=conf
            )

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result and result.pose_landmarks:
                leg_scores = []
                for idx in self.leg_landmarks:
                    if idx < len(result.pose_landmarks.landmark):
                        leg_scores.append(result.pose_landmarks.landmark[idx].visibility)

                avg_leg = np.mean(leg_scores) if leg_scores else 0
                results[conf] = avg_leg
            else:
                results[conf] = 0

            pose.close()

        return results

    def test_enhancement_variations(self, frame, frame_id):
        """Test different enhancement strengths."""
        results = {}

        # Different CLAHE clip limits
        clip_limits = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

        for clip in clip_limits:
            # Apply CLAHE with different strengths
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8,8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

            # Test detection
            pose = mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                min_detection_confidence=0.2,
                min_tracking_confidence=0.2
            )

            rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result and result.pose_landmarks:
                leg_scores = []
                for idx in self.leg_landmarks:
                    if idx < len(result.pose_landmarks.landmark):
                        leg_scores.append(result.pose_landmarks.landmark[idx].visibility)

                avg_leg = np.mean(leg_scores) if leg_scores else 0
                results[f'clahe_{clip}'] = avg_leg
            else:
                results[f'clahe_{clip}'] = 0

            pose.close()

        return results

    def test_blur_variations(self, frame, frame_id):
        """Test different blur kernel sizes."""
        results = {}

        kernel_sizes = [3, 5, 7, 9, 11, 13, 15]

        for kernel in kernel_sizes:
            # Apply blur
            blurred = cv2.GaussianBlur(frame, (kernel, kernel), 0)

            # Test detection
            pose = mp.solutions.pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                min_detection_confidence=0.2,
                min_tracking_confidence=0.2
            )

            rgb = cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result and result.pose_landmarks:
                leg_scores = []
                for idx in self.leg_landmarks:
                    if idx < len(result.pose_landmarks.landmark):
                        leg_scores.append(result.pose_landmarks.landmark[idx].visibility)

                avg_leg = np.mean(leg_scores) if leg_scores else 0
                results[f'blur_{kernel}'] = avg_leg
            else:
                results[f'blur_{kernel}'] = 0

            pose.close()

        return results


def main():
    """Test variations to see what makes results better or worse."""
    print("🔬 TESTING OPTIMIZATION VARIATIONS")
    print("="*60)
    print("Testing if changing parameters makes results better or worse...")
    print()

    tester = OptimizationVariationTester()
    optimizer = UnifiedOptimizer()
    frames_dir = Path('frames_complete_analysis')

    # Test on problematic frames
    test_frames = [5, 7, 50, 100]  # Mix of different types

    all_results = {}

    for frame_id in test_frames:
        frame_path = frames_dir / f"frame_{frame_id:04d}.png"
        if not frame_path.exists():
            continue

        frame = cv2.imread(str(frame_path))
        print(f"\n{'='*50}")
        print(f"📍 FRAME {frame_id}")
        print(f"{'='*50}")

        # Get baseline with unified optimizer
        baseline_result = optimizer.optimize_frame(frame, frame_id)
        baseline_leg = 0
        if baseline_result is not None:
            leg_data = baseline_result[baseline_result['landmark_id'].isin(tester.leg_landmarks)]
            baseline_leg = leg_data['visibility'].mean() if not leg_data.empty else 0
            baseline_strategy = baseline_result.iloc[0]['strategy'] if 'strategy' in baseline_result.columns else 'unknown'
            print(f"Baseline (unified): {baseline_leg:.3f} using {baseline_strategy}")

        # Test confidence variations
        print(f"\n📊 Confidence Variations:")
        print("-"*30)
        conf_results = tester.test_confidence_variations(frame, frame_id)

        best_conf = max(conf_results.items(), key=lambda x: x[1])
        worst_conf = min(conf_results.items(), key=lambda x: x[1])

        for conf, score in sorted(conf_results.items()):
            status = ""
            if score > baseline_leg:
                status = f" ✅ BETTER (+{(score-baseline_leg)*100:.1f}%)"
            elif score < baseline_leg:
                status = f" ❌ WORSE ({(score-baseline_leg)*100:.1f}%)"

            print(f"  Confidence {conf:.2f}: {score:.3f}{status}")

        # Test enhancement variations
        print(f"\n📊 Enhancement Variations:")
        print("-"*30)
        enh_results = tester.test_enhancement_variations(frame, frame_id)

        for enh, score in sorted(enh_results.items()):
            status = ""
            if score > baseline_leg:
                status = f" ✅ BETTER (+{(score-baseline_leg)*100:.1f}%)"
            elif score < baseline_leg:
                status = f" ❌ WORSE ({(score-baseline_leg)*100:.1f}%)"

            print(f"  {enh}: {score:.3f}{status}")

        # Test blur variations
        print(f"\n📊 Blur Variations:")
        print("-"*30)
        blur_results = tester.test_blur_variations(frame, frame_id)

        for blur, score in sorted(blur_results.items()):
            status = ""
            if score > baseline_leg:
                status = f" ✅ BETTER (+{(score-baseline_leg)*100:.1f}%)"
            elif score < baseline_leg:
                status = f" ❌ WORSE ({(score-baseline_leg)*100:.1f}%)"

            print(f"  {blur}: {score:.3f}{status}")

        # Find overall best
        all_variations = {**conf_results, **enh_results, **blur_results}
        best_overall = max(all_variations.items(), key=lambda x: x[1])

        print(f"\n🏆 BEST for frame {frame_id}: {best_overall[0]} with score {best_overall[1]:.3f}")
        if best_overall[1] > baseline_leg:
            improvement = (best_overall[1] - baseline_leg) / baseline_leg * 100
            print(f"   This is {improvement:.1f}% BETTER than unified optimization!")
        elif best_overall[1] < baseline_leg:
            degradation = (baseline_leg - best_overall[1]) / baseline_leg * 100
            print(f"   Unified optimization is still {degradation:.1f}% better")

        all_results[frame_id] = {
            'baseline': baseline_leg,
            'best': best_overall,
            'all': all_variations
        }

    # Overall summary
    print("\n" + "="*60)
    print("📊 OVERALL SUMMARY")
    print("="*60)

    improvements = 0
    degradations = 0

    for frame_id, results in all_results.items():
        if results['best'][1] > results['baseline']:
            improvements += 1
            print(f"Frame {frame_id}: Can be IMPROVED from {results['baseline']:.3f} to {results['best'][1]:.3f} using {results['best'][0]}")
        else:
            degradations += 1
            print(f"Frame {frame_id}: Unified is OPTIMAL at {results['baseline']:.3f}")

    print(f"\n🎯 CONCLUSION:")
    print(f"  Frames that can be improved: {improvements}/{len(all_results)}")
    print(f"  Frames where unified is optimal: {degradations}/{len(all_results)}")

    if improvements > 0:
        print(f"\n💡 INSIGHT: Results CAN get better with different parameters!")
        print("  Suggests room for further optimization in the unified approach")
    else:
        print(f"\n✅ INSIGHT: Unified optimization is already well-tuned")


if __name__ == "__main__":
    main()