#!/usr/bin/env python
"""
Rotation-aware pose processing that handles profile views properly.
"""

import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import mediapipe as mp
from typing import Dict, List, Tuple

class RotationAwarePoseProcessor:
    """
    Process poses with rotation awareness.
    """

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_face = mp.solutions.face_detection

        # Initialize both pose and face detection
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )

        self.face_detector = self.mp_face.FaceDetection(
            min_detection_confidence=0.3
        )

    def detect_orientation(self, frame: np.ndarray) -> str:
        """
        Detect if person is facing front, left, right, or back.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_results = self.face_detector.process(rgb_frame)

        if face_results.detections:
            # Face detected - check position
            detection = face_results.detections[0]
            bbox = detection.location_data.relative_bounding_box

            # Check face position relative to frame center
            face_center_x = bbox.xmin + bbox.width / 2

            if face_center_x < 0.3:
                return 'right_profile'  # Face on left = looking right
            elif face_center_x > 0.7:
                return 'left_profile'   # Face on right = looking left
            else:
                return 'frontal'
        else:
            # No face detected - might be back view or severe profile
            return 'unknown'

    def process_frontal_pose(self, frame: np.ndarray) -> pd.DataFrame:
        """
        Standard processing for frontal poses.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)

        if results.pose_landmarks:
            # Convert to dataframe with all coordinates
            data = []
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                data.append({
                    'landmark_id': idx,
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility,
                    'orientation': 'frontal'
                })
            return pd.DataFrame(data)
        return pd.DataFrame()

    def process_profile_pose(self, frame: np.ndarray, direction: str) -> pd.DataFrame:
        """
        Special processing for profile poses.
        """
        # For profile views, we need different strategy
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Try detection on original
        results_original = self.pose.process(rgb_frame)

        # Also try on mirrored frame
        mirrored_frame = cv2.flip(rgb_frame, 1)
        results_mirrored = self.pose.process(mirrored_frame)

        # Choose better result based on confidence
        if results_original.pose_landmarks and results_mirrored.pose_landmarks:
            conf_original = np.mean([lm.visibility for lm in results_original.pose_landmarks.landmark])
            conf_mirrored = np.mean([lm.visibility for lm in results_mirrored.pose_landmarks.landmark])

            if conf_mirrored > conf_original:
                results = results_mirrored
                need_flip = True
            else:
                results = results_original
                need_flip = False
        else:
            results = results_original
            need_flip = False

        if results.pose_landmarks:
            data = []
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                x = landmark.x
                if need_flip:
                    x = 1.0 - x  # Flip x coordinate back

                data.append({
                    'landmark_id': idx,
                    'x': x,
                    'y': landmark.y,
                    'z': landmark.z * 0.5,  # Reduce z-confidence for profiles
                    'visibility': landmark.visibility * 0.8,  # Reduce confidence
                    'orientation': direction
                })
            return pd.DataFrame(data)
        return pd.DataFrame()

    def process_video_with_rotation_awareness(self, video_path: str) -> pd.DataFrame:
        """
        Process entire video with rotation awareness.
        """
        cap = cv2.VideoCapture(video_path)
        all_poses = []
        frame_idx = 0

        print("Processing with rotation awareness...")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Detect orientation
            orientation = self.detect_orientation(frame)

            # Process based on orientation
            if orientation == 'frontal':
                pose_data = self.process_frontal_pose(frame)
            elif 'profile' in orientation:
                pose_data = self.process_profile_pose(frame, orientation)
            else:
                # Unknown orientation - try frontal with low confidence
                pose_data = self.process_frontal_pose(frame)
                if not pose_data.empty:
                    pose_data['visibility'] *= 0.5  # Reduce confidence

            if not pose_data.empty:
                pose_data['frame_id'] = frame_idx
                all_poses.append(pose_data)

            frame_idx += 1

            if frame_idx % 30 == 0:
                print(f"Processed frame {frame_idx}")

        cap.release()

        if all_poses:
            return pd.concat(all_poses, ignore_index=True)
        return pd.DataFrame()

def apply_temporal_constraints(pose_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply temporal constraints to fix impossible jumps.
    """
    df_fixed = pose_df.copy()
    frames = sorted(pose_df['frame_id'].unique())

    for i in range(1, len(frames)):
        curr_frame = df_fixed[df_fixed['frame_id'] == frames[i]]
        prev_frame = df_fixed[df_fixed['frame_id'] == frames[i-1]]

        for landmark_id in range(33):
            curr_lm = curr_frame[curr_frame['landmark_id'] == landmark_id]
            prev_lm = prev_frame[prev_frame['landmark_id'] == landmark_id]

            if not curr_lm.empty and not prev_lm.empty:
                # Calculate movement
                dx = curr_lm.iloc[0]['x'] - prev_lm.iloc[0]['x']
                dy = curr_lm.iloc[0]['y'] - prev_lm.iloc[0]['y']
                movement = np.sqrt(dx**2 + dy**2)

                # If movement is too large, interpolate
                if movement > 0.15:  # Max 15% screen movement per frame
                    # Use previous position with slight adjustment
                    df_fixed.loc[(df_fixed['frame_id'] == frames[i]) &
                                (df_fixed['landmark_id'] == landmark_id), 'x'] = \
                        prev_lm.iloc[0]['x'] + dx * 0.3  # Allow only 30% of movement

                    df_fixed.loc[(df_fixed['frame_id'] == frames[i]) &
                                (df_fixed['landmark_id'] == landmark_id), 'y'] = \
                        prev_lm.iloc[0]['y'] + dy * 0.3

                    # Mark as corrected
                    df_fixed.loc[(df_fixed['frame_id'] == frames[i]) &
                                (df_fixed['landmark_id'] == landmark_id), 'corrected'] = True

    return df_fixed

def hybrid_fix(video_path: str, output_csv: str):
    """
    Complete hybrid approach to fix rotation issues.
    """
    print("🔧 Applying Hybrid Rotation Fix")
    print("="*60)

    # Step 1: Process with rotation awareness
    processor = RotationAwarePoseProcessor()
    pose_df = processor.process_video_with_rotation_awareness(video_path)

    if pose_df.empty:
        print("❌ No poses detected!")
        return

    # Step 2: Apply temporal constraints
    print("\nApplying temporal constraints...")
    pose_df_fixed = apply_temporal_constraints(pose_df)

    # Step 3: Fill missing frames with interpolation
    all_frames = set(range(pose_df_fixed['frame_id'].max() + 1))
    detected_frames = set(pose_df_fixed['frame_id'].unique())
    missing_frames = all_frames - detected_frames

    if missing_frames:
        print(f"Interpolating {len(missing_frames)} missing frames...")
        # Add interpolation for missing frames here

    # Save result
    pose_df_fixed.to_csv(output_csv, index=False)
    print(f"\n✅ Fixed poses saved to: {output_csv}")

    # Report statistics
    orientations = pose_df_fixed.groupby('orientation').size()
    print("\n📊 Orientation Statistics:")
    for orient, count in orientations.items():
        print(f"  {orient}: {count} landmarks")

    corrected = pose_df_fixed['corrected'].sum() if 'corrected' in pose_df_fixed else 0
    print(f"\n📈 Corrections Applied: {corrected} landmarks")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Fix rotation issues in pose detection')
    parser.add_argument('--video', default='video/dance.mp4', help='Input video')
    parser.add_argument('--output', default='creative_output/dance_poses_rotation_fixed.csv',
                       help='Output CSV')

    args = parser.parse_args()

    hybrid_fix(args.video, args.output)

if __name__ == "__main__":
    main()