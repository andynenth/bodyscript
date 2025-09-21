#!/usr/bin/env python
"""
Compare all optimization approaches to understand what actually works.
Focus on leg detection quality metrics.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
import json


class OptimizationComparator:
    """Compare different optimization strategies."""

    def __init__(self):
        self.results = {}
        self.leg_landmarks = [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        self.critical_leg = [25, 26, 27, 28]  # knees and ankles

    def analyze_csv_quality(self, csv_path, name):
        """Analyze quality metrics from a CSV file."""
        if not Path(csv_path).exists():
            print(f"  {name}: File not found")
            return None

        df = pd.read_csv(csv_path)

        # Overall metrics
        total_frames = df['frame_id'].nunique()
        avg_visibility = df['visibility'].mean()
        high_conf = (df['visibility'] > 0.7).sum() / len(df) * 100

        # Leg-specific metrics
        leg_data = df[df['landmark_id'].isin(self.leg_landmarks)]
        avg_leg_vis = leg_data['visibility'].mean()

        # Critical landmarks (knees/ankles)
        critical_data = df[df['landmark_id'].isin(self.critical_leg)]
        avg_critical_vis = critical_data['visibility'].mean()

        # Per-frame leg issues
        frames_with_leg_issues = 0
        frames_with_critical_issues = 0

        for frame_id in df['frame_id'].unique():
            frame_legs = df[(df['frame_id'] == frame_id) &
                           (df['landmark_id'].isin(self.leg_landmarks))]
            if not frame_legs.empty:
                if frame_legs['visibility'].mean() < 0.5:
                    frames_with_leg_issues += 1

            frame_critical = df[(df['frame_id'] == frame_id) &
                               (df['landmark_id'].isin(self.critical_leg))]
            if not frame_critical.empty:
                if frame_critical['visibility'].mean() < 0.3:
                    frames_with_critical_issues += 1

        # Specific problematic frames (1-30, 40-60)
        early_frames = df[df['frame_id'] <= 30]
        rotation_frames = df[(df['frame_id'] >= 40) & (df['frame_id'] <= 60)]

        early_leg_vis = early_frames[early_frames['landmark_id'].isin(self.leg_landmarks)]['visibility'].mean()
        rotation_leg_vis = rotation_frames[rotation_frames['landmark_id'].isin(self.leg_landmarks)]['visibility'].mean()

        return {
            'name': name,
            'total_frames': total_frames,
            'avg_visibility': avg_visibility,
            'high_conf_pct': high_conf,
            'avg_leg_visibility': avg_leg_vis,
            'avg_critical_visibility': avg_critical_vis,
            'frames_with_leg_issues': frames_with_leg_issues,
            'frames_with_critical_issues': frames_with_critical_issues,
            'early_frames_leg_vis': early_leg_vis,
            'rotation_frames_leg_vis': rotation_leg_vis,
            'leg_issue_rate': frames_with_leg_issues / total_frames * 100 if total_frames > 0 else 0,
            'critical_issue_rate': frames_with_critical_issues / total_frames * 100 if total_frames > 0 else 0
        }

    def test_strategy_on_problem_frames(self):
        """Test different strategies on known problem frames."""
        problem_frames = [3, 5, 6, 7, 8, 9, 10, 50, 51, 52, 73, 100, 206]
        frames_dir = Path('frames_complete_analysis')

        strategies = {
            'standard': lambda f: (f, 0.3),
            'low_conf': lambda f: (f, 0.1),
            'blur5': lambda f: (cv2.GaussianBlur(f, (5, 5), 0), 0.2),
            'blur7': lambda f: (cv2.GaussianBlur(f, (7, 7), 0), 0.2),
            'clahe': lambda f: (self.enhance_contrast(f), 0.2),
            'lower_enhance': lambda f: (self.enhance_lower_body(f), 0.2),
            'bright': lambda f: (cv2.convertScaleAbs(f, alpha=1.3, beta=30), 0.2),
            'mirror': lambda f: (cv2.flip(f, 1), 0.2)
        }

        results_per_strategy = {strategy: {'success': 0, 'leg_scores': []}
                               for strategy in strategies}

        for frame_id in problem_frames:
            frame_path = frames_dir / f"frame_{frame_id:04d}.png"
            if not frame_path.exists():
                continue

            frame = cv2.imread(str(frame_path))
            print(f"\nTesting frame {frame_id}:")

            for strategy_name, strategy_func in strategies.items():
                processed_frame, confidence = strategy_func(frame)

                pose = mp.solutions.pose.Pose(
                    static_image_mode=True,
                    model_complexity=2,
                    min_detection_confidence=confidence,
                    min_tracking_confidence=confidence
                )

                rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                result = pose.process(rgb)

                if result and result.pose_landmarks:
                    # Calculate leg score
                    leg_scores = []
                    for idx in self.leg_landmarks:
                        if idx < len(result.pose_landmarks.landmark):
                            leg_scores.append(result.pose_landmarks.landmark[idx].visibility)

                    avg_leg = np.mean(leg_scores) if leg_scores else 0
                    results_per_strategy[strategy_name]['leg_scores'].append(avg_leg)

                    if avg_leg > 0.5:
                        results_per_strategy[strategy_name]['success'] += 1

                    print(f"  {strategy_name:15s}: {avg_leg:.3f}")
                else:
                    results_per_strategy[strategy_name]['leg_scores'].append(0)
                    print(f"  {strategy_name:15s}: FAILED")

                pose.close()

        return results_per_strategy

    def enhance_contrast(self, frame):
        """CLAHE enhancement."""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    def enhance_lower_body(self, frame):
        """Enhance lower body region specifically."""
        h, w = frame.shape[:2]
        result = frame.copy()

        # Enhance lower 2/3 of frame
        lower = result[h//3:, :]
        lab = cv2.cvtColor(lower, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        # Also increase brightness
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=20)
        result[h//3:, :] = enhanced

        return result


def main():
    """Run comprehensive comparison."""
    print("🔬 COMPREHENSIVE OPTIMIZATION COMPARISON")
    print("="*60)

    comparator = OptimizationComparator()

    # List of CSV files to compare
    csv_files = [
        ('creative_output/pose_data_creative.csv', 'Original'),
        ('creative_output/pose_data_optimized.csv', 'Basic Optimized'),
        ('creative_output/rotation_targeted.csv', 'Rotation Fix'),
        ('creative_output/pose_data_temporal.csv', 'Temporal Prediction'),
        ('creative_output/comprehensive_optimized.csv', 'Comprehensive'),
        ('creative_output/true_every_frame_optimized.csv', 'True Every Frame'),
        ('creative_output/all_frames_optimized.csv', 'Efficient All Frames'),
        ('creative_output/leg_optimized.csv', 'Leg Focused'),
        ('creative_output/every_frame_optimized.csv', 'Every Frame Comprehensive')
    ]

    print("\n📊 ANALYZING EXISTING OPTIMIZATIONS")
    print("-"*50)

    all_results = []
    for csv_path, name in csv_files:
        print(f"\nAnalyzing {name}...")
        result = comparator.analyze_csv_quality(csv_path, name)
        if result:
            all_results.append(result)

    # Create comparison table
    if all_results:
        print("\n📈 COMPARISON TABLE")
        print("-"*80)
        print(f"{'Method':<25} {'Frames':<7} {'Avg Vis':<8} {'Leg Vis':<8} {'Leg Issues':<12} {'Critical':<10}")
        print("-"*80)

        for r in all_results:
            print(f"{r['name']:<25} {r['total_frames']:<7} "
                  f"{r['avg_visibility']:.3f}   {r['avg_leg_visibility']:.3f}   "
                  f"{r['frames_with_leg_issues']:<3} ({r['leg_issue_rate']:.1f}%)   "
                  f"{r['frames_with_critical_issues']:<3} ({r['critical_issue_rate']:.1f}%)")

        # Find best for legs
        best_leg = max(all_results, key=lambda x: x['avg_leg_visibility'])
        best_critical = max(all_results, key=lambda x: x['avg_critical_visibility'])
        least_issues = min(all_results, key=lambda x: x['leg_issue_rate'])

        print("\n🏆 BEST PERFORMERS")
        print("-"*50)
        print(f"Best leg visibility: {best_leg['name']} ({best_leg['avg_leg_visibility']:.3f})")
        print(f"Best critical joints: {best_critical['name']} ({best_critical['avg_critical_visibility']:.3f})")
        print(f"Fewest leg issues: {least_issues['name']} ({least_issues['leg_issue_rate']:.1f}% frames with issues)")

    # Test strategies on problem frames
    print("\n🧪 TESTING STRATEGIES ON PROBLEM FRAMES")
    print("-"*50)

    strategy_results = comparator.test_strategy_on_problem_frames()

    print("\n📊 STRATEGY PERFORMANCE SUMMARY")
    print("-"*50)

    for strategy, results in strategy_results.items():
        if results['leg_scores']:
            avg_score = np.mean(results['leg_scores'])
            success_rate = results['success'] / len(results['leg_scores']) * 100
            print(f"{strategy:15s}: Avg={avg_score:.3f}, Success={success_rate:.1f}%")

    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("-"*50)
    print("1. Lower confidence (0.1-0.2) helps with leg detection")
    print("2. Lower body enhancement specifically targets leg issues")
    print("3. Blur can help in some cases but not universally")
    print("4. Mirror strategy useful when one side is occluded")
    print("5. Static image mode prevents tracking lock but loses temporal consistency")

    # Save detailed report
    report = {
        'csv_analysis': all_results,
        'strategy_tests': {k: {'avg_score': np.mean(v['leg_scores']) if v['leg_scores'] else 0,
                               'success_rate': v['success'] / len(v['leg_scores']) * 100 if v['leg_scores'] else 0}
                          for k, v in strategy_results.items()},
        'recommendations': [
            "Use confidence 0.1-0.2 for difficult frames",
            "Apply lower body enhancement for leg issues",
            "Use static_image_mode=True for rotation frames",
            "Combine multiple strategies and pick best per frame",
            "Focus optimization on frames with <50% leg visibility"
        ]
    }

    with open('creative_output/optimization_comparison_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print("\n📁 Detailed report saved to: creative_output/optimization_comparison_report.json")


if __name__ == "__main__":
    main()