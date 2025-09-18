#!/usr/bin/env python
"""
Improved Temporal Prediction System with fixes for:
1. Cold start problem (frame 0)
2. Wild predictions when visibility is very low
3. Anatomical bounds checking
"""

import numpy as np
import pandas as pd
from collections import deque
from typing import Dict, Tuple, Optional


class ImprovedKalmanFilter2D:
    """
    Improved Kalman filter with bounds checking and initialization.
    """

    def __init__(self, process_noise=0.01, measurement_noise=0.1):
        self.state = np.zeros(4)  # [x, y, vx, vy]
        self.P = np.eye(4) * 1000  # Initial uncertainty
        self.Q = np.eye(4) * process_noise
        self.Q[2:, 2:] *= 0.1
        self.R = np.eye(2) * measurement_noise
        self.F = np.array([[1, 0, 1, 0],
                          [0, 1, 0, 1],
                          [0, 0, 1, 0],
                          [0, 0, 0, 1]])
        self.H = np.array([[1, 0, 0, 0],
                          [0, 1, 0, 0]])

        self.initialized = False
        self.update_count = 0  # Track how many updates we've had

    def predict(self):
        """Predict next state."""
        # Don't predict if not initialized
        if not self.initialized or self.update_count < 2:
            return None

        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q

        # Limit velocity to prevent wild predictions
        max_velocity = 0.1  # Max movement per frame
        self.state[2] = np.clip(self.state[2], -max_velocity, max_velocity)
        self.state[3] = np.clip(self.state[3], -max_velocity, max_velocity)

        return self.state[:2]

    def update(self, measurement, confidence=1.0):
        """Update with bounds checking."""
        if not self.initialized:
            self.state[:2] = measurement
            self.initialized = True
            self.update_count = 1
            return self.state[:2]

        # Don't trust very low confidence measurements for updates
        if confidence < 0.15:
            return self.state[:2]  # Return current state without update

        R_adjusted = self.R / (confidence + 0.01)
        S = self.H @ self.P @ self.H.T + R_adjusted
        K = self.P @ self.H.T @ np.linalg.inv(S)

        y = measurement - self.H @ self.state

        # Limit innovation to prevent jumps
        max_innovation = 0.2
        y = np.clip(y, -max_innovation, max_innovation)

        self.state = self.state + K @ y
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P

        self.update_count += 1

        return self.state[:2]


class ImprovedTemporalPrediction:
    """
    Improved temporal prediction with safeguards.
    """

    def __init__(self,
                 num_landmarks=33,
                 cold_start_frames=3,
                 min_prediction_confidence=0.2,
                 max_position_change=0.15):
        """
        Args:
            cold_start_frames: Number of frames to skip prediction at start
            min_prediction_confidence: Minimum confidence to attempt prediction
            max_position_change: Maximum allowed position change between frames
        """
        self.filters = {}
        for i in range(num_landmarks):
            self.filters[i] = ImprovedKalmanFilter2D()

        self.history = deque(maxlen=5)
        self.frame_count = 0
        self.cold_start_frames = cold_start_frames
        self.min_prediction_confidence = min_prediction_confidence
        self.max_position_change = max_position_change

        # Anatomical bounds for landmarks
        self.landmark_bounds = self._initialize_landmark_bounds()

    def _initialize_landmark_bounds(self):
        """Define reasonable bounds for each landmark."""
        bounds = {}

        # Head landmarks - should stay in upper portion
        for i in range(11):  # Nose, eyes, ears, etc.
            bounds[i] = {'x': (0.2, 0.8), 'y': (0.0, 0.4)}

        # Shoulders and upper body
        for i in [11, 12, 13, 14, 15, 16]:  # Shoulders, elbows, wrists
            bounds[i] = {'x': (0.0, 1.0), 'y': (0.15, 0.65)}

        # Hips
        for i in [23, 24]:
            bounds[i] = {'x': (0.2, 0.8), 'y': (0.4, 0.6)}

        # Legs - should be in lower portion
        for i in [25, 26]:  # Knees
            bounds[i] = {'x': (0.1, 0.9), 'y': (0.5, 0.75)}

        for i in [27, 28, 29, 30, 31, 32]:  # Ankles, heels, feet
            bounds[i] = {'x': (0.1, 0.9), 'y': (0.65, 0.95)}

        # Default for any missing
        for i in range(33):
            if i not in bounds:
                bounds[i] = {'x': (0.0, 1.0), 'y': (0.0, 1.0)}

        return bounds

    def _apply_bounds(self, landmark_id, x, y):
        """Constrain position to anatomical bounds."""
        bounds = self.landmark_bounds[landmark_id]
        x = np.clip(x, bounds['x'][0], bounds['x'][1])
        y = np.clip(y, bounds['y'][0], bounds['y'][1])
        return x, y

    def process_frame(self, frame_data: pd.DataFrame) -> pd.DataFrame:
        """
        Process frame with improved safeguards.
        """
        enhanced_data = frame_data.copy()
        self.frame_count += 1

        # Skip prediction for first few frames (cold start)
        if self.frame_count <= self.cold_start_frames:
            print(f"  Frame {self.frame_count}: Skipping prediction (cold start)")
            self.history.append(enhanced_data)
            return enhanced_data

        # Get previous frame for comparison
        prev_frame = self.history[-1] if self.history else None

        for landmark_id in range(33):
            landmark = frame_data[frame_data['landmark_id'] == landmark_id]

            if landmark.empty:
                continue

            landmark = landmark.iloc[0]
            position = np.array([landmark['x'], landmark['y']])
            visibility = landmark['visibility']

            # Get previous position for bounds checking
            prev_position = None
            if prev_frame is not None:
                prev_lm = prev_frame[prev_frame['landmark_id'] == landmark_id]
                if not prev_lm.empty:
                    prev_position = np.array([prev_lm.iloc[0]['x'], prev_lm.iloc[0]['y']])

            kf = self.filters[landmark_id]

            # Decision logic based on visibility
            if visibility > 0.5:
                # Good detection - trust it
                filtered_pos = kf.update(position, visibility)
                final_pos = position  # Use original

            elif visibility > self.min_prediction_confidence:
                # Medium confidence - blend
                filtered_pos = kf.update(position, visibility)

                if filtered_pos is not None:
                    # Blend based on confidence
                    alpha = visibility
                    final_pos = alpha * position + (1 - alpha) * filtered_pos
                else:
                    final_pos = position

                # Boost confidence slightly
                idx = enhanced_data[enhanced_data['landmark_id'] == landmark_id].index[0]
                enhanced_data.loc[idx, 'visibility'] = min(visibility + 0.15, 0.5)

            else:
                # Very low confidence - be careful

                # Don't predict if we don't have enough history
                if kf.update_count < 3:
                    final_pos = position  # Use original, don't predict

                else:
                    # Try prediction but validate it
                    predicted_pos = kf.predict()

                    if predicted_pos is not None and prev_position is not None:
                        # Check if prediction is reasonable
                        movement = np.linalg.norm(predicted_pos - prev_position)

                        if movement < self.max_position_change:
                            # Reasonable prediction
                            final_pos = predicted_pos

                            # Mark as predicted
                            idx = enhanced_data[enhanced_data['landmark_id'] == landmark_id].index[0]
                            enhanced_data.loc[idx, 'visibility'] = 0.4
                            enhanced_data.loc[idx, 'predicted'] = True
                        else:
                            # Prediction too wild, use original
                            final_pos = position
                    else:
                        # Can't predict, use original
                        final_pos = position

            # Apply anatomical bounds
            final_x, final_y = self._apply_bounds(landmark_id, final_pos[0], final_pos[1])

            # Check movement from previous frame
            if prev_position is not None:
                movement = np.sqrt((final_x - prev_position[0])**2 +
                                 (final_y - prev_position[1])**2)

                if movement > self.max_position_change:
                    # Too much movement, blend with previous
                    alpha = 0.3  # Take 30% of new position
                    final_x = alpha * final_x + (1 - alpha) * prev_position[0]
                    final_y = alpha * final_y + (1 - alpha) * prev_position[1]

            # Update dataframe
            idx = enhanced_data[enhanced_data['landmark_id'] == landmark_id].index[0]
            enhanced_data.loc[idx, 'x'] = final_x
            enhanced_data.loc[idx, 'y'] = final_y

        # Store in history
        self.history.append(enhanced_data)

        return enhanced_data

    def apply_bone_length_constraints(self, frame_data: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure bone lengths stay consistent.
        """
        if len(self.history) < 2:
            return frame_data

        enhanced = frame_data.copy()

        bone_pairs = [
            (23, 25),  # Left hip to knee
            (25, 27),  # Left knee to ankle
            (24, 26),  # Right hip to knee
            (26, 28),  # Right knee to ankle
            (11, 13),  # Left shoulder to elbow
            (13, 15),  # Left elbow to wrist
            (12, 14),  # Right shoulder to elbow
            (14, 16),  # Right elbow to wrist
        ]

        # Get average bone lengths from history
        avg_lengths = {}
        for p1_id, p2_id in bone_pairs:
            lengths = []
            for hist_frame in self.history:
                p1 = hist_frame[hist_frame['landmark_id'] == p1_id]
                p2 = hist_frame[hist_frame['landmark_id'] == p2_id]

                if not p1.empty and not p2.empty:
                    if p1.iloc[0]['visibility'] > 0.5 and p2.iloc[0]['visibility'] > 0.5:
                        length = np.sqrt(
                            (p1.iloc[0]['x'] - p2.iloc[0]['x'])**2 +
                            (p1.iloc[0]['y'] - p2.iloc[0]['y'])**2
                        )
                        lengths.append(length)

            if lengths:
                avg_lengths[(p1_id, p2_id)] = np.median(lengths)

        # Apply constraints
        for (p1_id, p2_id), target_length in avg_lengths.items():
            p1 = enhanced[enhanced['landmark_id'] == p1_id]
            p2 = enhanced[enhanced['landmark_id'] == p2_id]

            if p1.empty or p2.empty:
                continue

            current_length = np.sqrt(
                (p1.iloc[0]['x'] - p2.iloc[0]['x'])**2 +
                (p1.iloc[0]['y'] - p2.iloc[0]['y'])**2
            )

            # If length is way off, adjust
            length_ratio = current_length / (target_length + 0.001)

            if length_ratio > 1.5 or length_ratio < 0.5:
                # Bone length is wrong
                # Move the lower confidence point
                if p1.iloc[0]['visibility'] < p2.iloc[0]['visibility']:
                    # Adjust p1 to maintain bone length
                    direction = np.array([
                        p1.iloc[0]['x'] - p2.iloc[0]['x'],
                        p1.iloc[0]['y'] - p2.iloc[0]['y']
                    ])
                    direction = direction / (np.linalg.norm(direction) + 0.001)

                    new_p1_x = p2.iloc[0]['x'] + direction[0] * target_length
                    new_p1_y = p2.iloc[0]['y'] + direction[1] * target_length

                    # Apply bounds
                    new_p1_x, new_p1_y = self._apply_bounds(p1_id, new_p1_x, new_p1_y)

                    idx = enhanced[enhanced['landmark_id'] == p1_id].index[0]
                    enhanced.loc[idx, 'x'] = new_p1_x
                    enhanced.loc[idx, 'y'] = new_p1_y
                else:
                    # Adjust p2
                    direction = np.array([
                        p2.iloc[0]['x'] - p1.iloc[0]['x'],
                        p2.iloc[0]['y'] - p1.iloc[0]['y']
                    ])
                    direction = direction / (np.linalg.norm(direction) + 0.001)

                    new_p2_x = p1.iloc[0]['x'] + direction[0] * target_length
                    new_p2_y = p1.iloc[0]['y'] + direction[1] * target_length

                    # Apply bounds
                    new_p2_x, new_p2_y = self._apply_bounds(p2_id, new_p2_x, new_p2_y)

                    idx = enhanced[enhanced['landmark_id'] == p2_id].index[0]
                    enhanced.loc[idx, 'x'] = new_p2_x
                    enhanced.loc[idx, 'y'] = new_p2_y

        return enhanced


def apply_improved_temporal_smoothing(csv_path: str,
                                     output_path: str) -> pd.DataFrame:
    """
    Apply improved temporal smoothing with all safeguards.
    """
    print("🔮 Applying Improved Temporal Prediction")
    print("="*50)

    df = pd.read_csv(csv_path)

    predictor = ImprovedTemporalPrediction(
        cold_start_frames=3,  # Skip first 3 frames
        min_prediction_confidence=0.2,  # Don't predict below 20%
        max_position_change=0.15  # Max 15% screen movement per frame
    )

    smoothed_frames = []

    for frame_id in sorted(df['frame_id'].unique()):
        frame_data = df[df['frame_id'] == frame_id]

        # Apply prediction with safeguards
        enhanced = predictor.process_frame(frame_data)

        # Apply bone length constraints
        enhanced = predictor.apply_bone_length_constraints(enhanced)

        smoothed_frames.append(enhanced)

        if frame_id % 50 == 0:
            print(f"  Processed frame {frame_id}")

    result = pd.concat(smoothed_frames, ignore_index=True)

    # Add predicted column if it doesn't exist
    if 'predicted' not in result.columns:
        result['predicted'] = False

    result.to_csv(output_path, index=False)

    # Report
    print("\n📊 Improvement Report:")

    problem_frames = [0, 1, 17, 18, 51, 70, 100, 128]
    for frame_id in problem_frames:
        orig_frame = df[df['frame_id'] == frame_id]
        smooth_frame = result[result['frame_id'] == frame_id]

        if not orig_frame.empty and not smooth_frame.empty:
            # Check specific issues
            if frame_id == 0:
                # Check heel positions
                orig_heel = orig_frame[orig_frame['landmark_id'] == 29]  # Left heel
                smooth_heel = smooth_frame[smooth_frame['landmark_id'] == 29]
                if not orig_heel.empty and not smooth_heel.empty:
                    print(f"  Frame {frame_id} (L Heel Y): {orig_heel.iloc[0]['y']:.3f} → "
                          f"{smooth_heel.iloc[0]['y']:.3f}")

            elif frame_id in [51, 70, 100]:
                # Check left wrist
                orig_wrist = orig_frame[orig_frame['landmark_id'] == 15]
                smooth_wrist = smooth_frame[smooth_frame['landmark_id'] == 15]
                if not orig_wrist.empty and not smooth_wrist.empty:
                    print(f"  Frame {frame_id} (L Wrist): "
                          f"vis={orig_wrist.iloc[0]['visibility']:.2f}→"
                          f"{smooth_wrist.iloc[0]['visibility']:.2f}, "
                          f"x={orig_wrist.iloc[0]['x']:.3f}→"
                          f"{smooth_wrist.iloc[0]['x']:.3f}")

    print(f"\n✅ Saved to: {output_path}")

    return result


if __name__ == "__main__":
    apply_improved_temporal_smoothing(
        'creative_output/dance_poses_optimized_full.csv',
        'creative_output/dance_poses_temporal_improved.csv'
    )