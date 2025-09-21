#!/usr/bin/env python
"""
Visualize all 4 detection strategies for specific frames.
Shows side-by-side comparison of original, blurred, enhanced, and mirrored approaches.
"""

import cv2
import pandas as pd
import numpy as np
import mediapipe as mp
from pathlib import Path
import argparse


def draw_pose_on_image(image, landmarks, label, color=(0, 255, 0)):
    """Draw pose landmarks on image with label."""
    h, w = image.shape[:2]

    # MediaPipe connections for skeleton
    mp_pose = mp.solutions.pose
    connections = mp_pose.POSE_CONNECTIONS

    if landmarks:
        # Draw connections
        for connection in connections:
            start_idx, end_idx = connection
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start = landmarks[start_idx]
                end = landmarks[end_idx]

                if start.visibility > 0.5 and end.visibility > 0.5:
                    x1, y1 = int(start.x * w), int(start.y * h)
                    x2, y2 = int(end.x * w), int(end.y * h)
                    cv2.line(image, (x1, y1), (x2, y2), color, 2)

        # Draw landmarks
        for landmark in landmarks:
            if landmark.visibility > 0.5:
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(image, (x, y), 4, color, -1)
                cv2.circle(image, (x, y), 5, (0, 0, 0), 1)

    # Add label
    cv2.rectangle(image, (0, 0), (w, 40), (0, 0, 0), -1)
    cv2.putText(image, label, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    return image


def analyze_frame_all_strategies(frame_path, save_comparison=True, output_dir="strategy_comparisons"):
    """
    Analyze a single frame with all 4 strategies and create comparison image.
    """
    frame = cv2.imread(str(frame_path))
    if frame is None:
        print(f"Error: Could not load {frame_path}")
        return None

    h, w = frame.shape[:2]

    # Initialize pose detector
    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        min_detection_confidence=0.2,
        min_tracking_confidence=0.2
    )

    results = {}
    scores = {}
    processed_images = {}

    # Strategy 1: Original
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result_orig = pose.process(rgb)
    if result_orig and result_orig.pose_landmarks:
        score = sum(lm.visibility for lm in result_orig.pose_landmarks.landmark) / 33
        results['Original'] = result_orig
        scores['Original'] = score
        img_orig = frame.copy()
        draw_pose_on_image(img_orig, result_orig.pose_landmarks.landmark if result_orig else None,
                          f"Original (Score: {score:.3f})", (0, 255, 0))
        processed_images['Original'] = img_orig

    # Strategy 2: Blurred
    blurred = cv2.GaussianBlur(frame, (7, 7), 0)
    rgb_blur = cv2.cvtColor(blurred, cv2.COLOR_BGR2RGB)
    result_blur = pose.process(rgb_blur)
    if result_blur and result_blur.pose_landmarks:
        score = sum(lm.visibility for lm in result_blur.pose_landmarks.landmark) / 33
        results['Blurred'] = result_blur
        scores['Blurred'] = score
        img_blur = blurred.copy()
        draw_pose_on_image(img_blur, result_blur.pose_landmarks.landmark if result_blur else None,
                          f"Blurred (Score: {score:.3f})", (0, 200, 255))
        processed_images['Blurred'] = img_blur

    # Strategy 3: Enhanced
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    rgb_enh = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
    result_enh = pose.process(rgb_enh)
    if result_enh and result_enh.pose_landmarks:
        score = sum(lm.visibility for lm in result_enh.pose_landmarks.landmark) / 33
        results['Enhanced'] = result_enh
        scores['Enhanced'] = score
        img_enh = enhanced.copy()
        draw_pose_on_image(img_enh, result_enh.pose_landmarks.landmark if result_enh else None,
                          f"Enhanced (Score: {score:.3f})", (255, 0, 255))
        processed_images['Enhanced'] = img_enh

    # Strategy 4: Mirrored
    mirrored = cv2.flip(frame, 1)
    rgb_mir = cv2.cvtColor(mirrored, cv2.COLOR_BGR2RGB)
    result_mir = pose.process(rgb_mir)
    if result_mir and result_mir.pose_landmarks:
        # Flip landmarks back for display
        if result_mir.pose_landmarks:
            for lm in result_mir.pose_landmarks.landmark:
                lm.x = 1.0 - lm.x
        score = sum(lm.visibility for lm in result_mir.pose_landmarks.landmark) / 33
        results['Mirrored'] = result_mir
        scores['Mirrored'] = score
        img_mir = frame.copy()  # Use original frame, not mirrored
        draw_pose_on_image(img_mir, result_mir.pose_landmarks.landmark if result_mir else None,
                          f"Mirrored (Score: {score:.3f})", (255, 200, 0))
        processed_images['Mirrored'] = img_mir

    pose.close()

    # Find best strategy
    if scores:
        best_strategy = max(scores, key=scores.get)
        best_score = scores[best_strategy]

        print(f"\nFrame: {frame_path.name}")
        print("-" * 40)
        for strategy, score in sorted(scores.items(), key=lambda x: -x[1]):
            marker = " ← BEST" if strategy == best_strategy else ""
            print(f"  {strategy:10s}: {score:.3f}{marker}")

    # Create comparison image
    if save_comparison and processed_images:
        # Create 2x2 grid
        row1 = np.hstack([
            processed_images.get('Original', np.zeros((h, w, 3), dtype=np.uint8)),
            processed_images.get('Blurred', np.zeros((h, w, 3), dtype=np.uint8))
        ])
        row2 = np.hstack([
            processed_images.get('Enhanced', np.zeros((h, w, 3), dtype=np.uint8)),
            processed_images.get('Mirrored', np.zeros((h, w, 3), dtype=np.uint8))
        ])
        comparison = np.vstack([row1, row2])

        # Add title
        title_height = 60
        title_img = np.zeros((title_height, comparison.shape[1], 3), dtype=np.uint8)
        cv2.putText(title_img, f"Frame: {frame_path.stem} | Best: {best_strategy} ({best_score:.3f})",
                   (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        comparison = np.vstack([title_img, comparison])

        # Save comparison
        Path(output_dir).mkdir(exist_ok=True)
        output_path = Path(output_dir) / f"comparison_{frame_path.stem}.jpg"
        cv2.imwrite(str(output_path), comparison, [cv2.IMWRITE_JPEG_QUALITY, 95])
        print(f"  Saved comparison: {output_path}")

        return comparison, results, scores

    return None, results, scores


def main():
    """Main function to analyze specific frames."""
    parser = argparse.ArgumentParser(description='Visualize all 4 pose detection strategies')
    parser.add_argument('--frames', type=str, default='3,50,100,200,300',
                       help='Comma-separated frame numbers to analyze (default: 3,50,100,200,300)')
    parser.add_argument('--input-dir', type=str, default='frames_complete_analysis',
                       help='Directory containing frame PNGs (default: frames_complete_analysis)')
    parser.add_argument('--output-dir', type=str, default='strategy_comparisons',
                       help='Output directory for comparison images (default: strategy_comparisons)')
    args = parser.parse_args()

    print("🔍 POSE DETECTION STRATEGY COMPARISON")
    print("=" * 60)

    # Parse frame numbers
    frame_numbers = [int(f.strip()) for f in args.frames.split(',')]

    # Create output directory
    Path(args.output_dir).mkdir(exist_ok=True)

    # Process each frame
    for frame_num in frame_numbers:
        frame_path = Path(args.input_dir) / f"frame_{frame_num:06d}.png"

        if not frame_path.exists():
            print(f"\n⚠️  Frame {frame_num} not found: {frame_path}")
            continue

        print(f"\n📸 Analyzing frame {frame_num}...")
        comparison, results, scores = analyze_frame_all_strategies(
            frame_path,
            save_comparison=True,
            output_dir=args.output_dir
        )

    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print(f"📁 Comparison images saved to: {args.output_dir}/")
    print("\n💡 Tips:")
    print("  • Green = Original strategy")
    print("  • Orange = Blurred strategy")
    print("  • Purple = Enhanced strategy")
    print("  • Yellow = Mirrored strategy")
    print("  • Higher scores = better detection")
    print("=" * 60)


if __name__ == "__main__":
    main()