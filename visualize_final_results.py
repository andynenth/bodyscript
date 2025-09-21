#!/usr/bin/env python
"""
Visualize Final MediaPipe Results
Compare original vs final optimized results
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
import matplotlib.pyplot as plt


def draw_skeleton_from_csv(frame, csv_data, frame_id, color=(0, 255, 0)):
    """Draw skeleton from CSV data onto frame"""
    h, w = frame.shape[:2]
    frame_data = csv_data[csv_data['frame_id'] == frame_id]

    if frame_data.empty:
        return frame

    # Draw connections
    mp_pose = mp.solutions.pose
    for connection in mp_pose.POSE_CONNECTIONS:
        start_idx, end_idx = connection

        start_point = frame_data[frame_data['landmark_id'] == start_idx]
        end_point = frame_data[frame_data['landmark_id'] == end_idx]

        if not start_point.empty and not end_point.empty:
            if start_point.iloc[0]['visibility'] > 0.5 and end_point.iloc[0]['visibility'] > 0.5:
                x1 = int(start_point.iloc[0]['x'] * w)
                y1 = int(start_point.iloc[0]['y'] * h)
                x2 = int(end_point.iloc[0]['x'] * w)
                y2 = int(end_point.iloc[0]['y'] * h)

                thickness = int(2 + 3 * min(start_point.iloc[0]['visibility'],
                                           end_point.iloc[0]['visibility']))
                cv2.line(frame, (x1, y1), (x2, y2), color, thickness)

    # Draw landmarks
    for _, landmark in frame_data.iterrows():
        if landmark['visibility'] > 0.5:
            x = int(landmark['x'] * w)
            y = int(landmark['y'] * h)
            radius = int(3 + 5 * landmark['visibility'])
            cv2.circle(frame, (x, y), radius, color, -1)
            cv2.circle(frame, (x, y), radius + 1, (0, 0, 0), 1)

    return frame


def create_comparison():
    """Create side-by-side comparison of results"""

    # Load CSVs
    original_csv = pd.read_csv('creative_output/true_every_frame_optimized.csv')
    final_csv = pd.read_csv('creative_output/mediapipe_final_sample.csv')

    # Test frames
    test_frames = [3, 50]

    for frame_id in test_frames:
        frame_path = Path('frames_complete_analysis') / f"frame_{frame_id:06d}.png"
        if not frame_path.exists():
            continue

        frame = cv2.imread(str(frame_path))
        h, w = frame.shape[:2]

        # Create figure with 3 columns
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # Original frame
        axes[0].imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        axes[0].set_title(f"Frame {frame_id}\nOriginal Image")
        axes[0].axis('off')

        # Original detection
        frame_orig = frame.copy()
        frame_orig = draw_skeleton_from_csv(frame_orig, original_csv, frame_id, (0, 255, 0))
        axes[1].imshow(cv2.cvtColor(frame_orig, cv2.COLOR_BGR2RGB))

        # Get strategy used
        orig_data = original_csv[original_csv['frame_id'] == frame_id]
        if not orig_data.empty and 'strategy' in orig_data.columns:
            strategy = orig_data.iloc[0]['strategy']
            avg_vis = orig_data['visibility'].mean()
            axes[1].set_title(f"Initial Best\n{strategy} (vis: {avg_vis:.2f})")
        else:
            axes[1].set_title("Initial Best\n(4 strategies)")
        axes[1].axis('off')

        # Final optimized
        frame_final = frame.copy()
        frame_final = draw_skeleton_from_csv(frame_final, final_csv, frame_id, (255, 200, 0))
        axes[2].imshow(cv2.cvtColor(frame_final, cv2.COLOR_BGR2RGB))

        # Get final strategy
        final_data = final_csv[final_csv['frame_id'] == frame_id]
        if not final_data.empty and 'strategy' in final_data.columns:
            strategy = final_data.iloc[0]['strategy'].replace('_', ' ')
            avg_vis = final_data['visibility'].mean()
            axes[2].set_title(f"Final Optimized\n{strategy} (vis: {avg_vis:.2f})")
        else:
            axes[2].set_title("Final Optimized\n(30 strategies)")
        axes[2].axis('off')

        plt.suptitle(f"MediaPipe Evolution - Frame {frame_id}", fontsize=14, fontweight='bold')
        plt.tight_layout()

        output_path = f"creative_output/final_comparison_frame_{frame_id}.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"Saved: {output_path}")

    # Create quality chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Calculate averages
    frames = final_csv['frame_id'].unique()
    orig_vis = []
    final_vis = []

    for fid in sorted(frames):
        orig_frame = original_csv[original_csv['frame_id'] == fid]
        final_frame = final_csv[final_csv['frame_id'] == fid]

        if not orig_frame.empty:
            orig_vis.append(orig_frame['visibility'].mean())
        else:
            orig_vis.append(0)

        if not final_frame.empty:
            final_vis.append(final_frame['visibility'].mean())
        else:
            final_vis.append(0)

    # Visibility comparison
    x = range(len(frames))
    ax1.bar([i - 0.2 for i in x], orig_vis, 0.4, label='Original', color='green', alpha=0.7)
    ax1.bar([i + 0.2 for i in x], final_vis, 0.4, label='Final', color='orange', alpha=0.7)
    ax1.set_xlabel('Frame Index')
    ax1.set_ylabel('Average Visibility')
    ax1.set_title('Detection Quality Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Strategy distribution for final
    strategy_counts = final_csv.groupby('strategy').size()
    strategies = [s.split('_')[0] for s in strategy_counts.index]
    strategy_summary = {}
    for s in strategies:
        strategy_summary[s] = strategy_summary.get(s, 0) + 1

    ax2.bar(strategy_summary.keys(), strategy_summary.values(), color='steelblue')
    ax2.set_xlabel('Strategy')
    ax2.set_ylabel('Frames')
    ax2.set_title('Final Strategy Distribution')
    ax2.tick_params(axis='x', rotation=45)

    plt.suptitle('MediaPipe Final Optimization Results', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('creative_output/final_quality_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("Saved: creative_output/final_quality_analysis.png")


if __name__ == "__main__":
    print("Creating final comparisons...")
    create_comparison()
    print("\n✅ Visualizations complete!")