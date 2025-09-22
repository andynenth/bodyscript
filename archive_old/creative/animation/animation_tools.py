"""
Animation Tools Module - Smoothing, interpolation, and loop generation
Advanced animation processing for creative applications
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from scipy import signal, interpolate
from dataclasses import dataclass
import warnings


@dataclass
class AnimationCurve:
    """Represents an animation curve for a single parameter."""
    frames: np.ndarray
    values: np.ndarray
    tangents_in: Optional[np.ndarray] = None
    tangents_out: Optional[np.ndarray] = None
    interpolation: str = 'linear'  # linear, bezier, step


class AnimationProcessor:
    """
    Process and enhance animation data for creative output.
    """

    INTERPOLATION_TYPES = ['linear', 'bezier', 'cubic', 'quadratic', 'step', 'elastic']

    def __init__(self, fps: float = 30.0):
        """
        Initialize animation processor.

        Args:
            fps: Frames per second
        """
        self.fps = fps

    def smooth_animation(self,
                        pose_data: pd.DataFrame,
                        smoothing_type: str = 'gaussian',
                        strength: float = 0.5,
                        preserve_extremes: bool = True) -> pd.DataFrame:
        """
        Apply advanced smoothing to animation data.

        Args:
            pose_data: DataFrame with pose landmarks
            smoothing_type: Type of smoothing (gaussian, savitzky, exponential, bilateral)
            strength: Smoothing strength (0-1)
            preserve_extremes: Whether to preserve extreme poses

        Returns:
            Smoothed pose data
        """
        smoothed_data = pose_data.copy()

        # Calculate window size based on strength
        window_size = max(3, int(strength * 15))
        if window_size % 2 == 0:
            window_size += 1

        # Store extremes if needed
        extremes = None
        if preserve_extremes:
            extremes = self._detect_extremes(pose_data)

        # Apply smoothing by landmark
        for landmark_id in pose_data['landmark_id'].unique():
            mask = pose_data['landmark_id'] == landmark_id

            for coord in ['x', 'y', 'z']:
                if coord not in pose_data.columns:
                    continue

                values = pose_data.loc[mask, coord].values

                # Skip if not enough data
                if len(values) < window_size:
                    continue

                # Apply selected smoothing method
                if smoothing_type == 'gaussian':
                    smoothed_values = self._gaussian_smooth(values, window_size, strength)
                elif smoothing_type == 'savitzky':
                    smoothed_values = self._savitzky_smooth(values, window_size)
                elif smoothing_type == 'exponential':
                    smoothed_values = self._exponential_smooth(values, strength)
                elif smoothing_type == 'bilateral':
                    smoothed_values = self._bilateral_smooth(values, window_size, strength)
                else:
                    smoothed_values = values

                # Restore extremes if needed
                if preserve_extremes and extremes is not None:
                    smoothed_values = self._restore_extremes(
                        smoothed_values, values, extremes, landmark_id, coord
                    )

                smoothed_data.loc[mask, coord] = smoothed_values

        return smoothed_data

    def interpolate_frames(self,
                          pose_data: pd.DataFrame,
                          target_fps: float = 60.0,
                          method: str = 'cubic') -> pd.DataFrame:
        """
        Interpolate between frames to change frame rate.

        Args:
            pose_data: Original pose data
            target_fps: Target frames per second
            method: Interpolation method

        Returns:
            Interpolated pose data
        """
        if target_fps == self.fps:
            return pose_data

        # Calculate interpolation factor
        factor = target_fps / self.fps
        original_frames = pose_data['frame_id'].unique()
        new_frame_count = int(len(original_frames) * factor)

        # Create new frame indices
        new_frames = np.linspace(
            original_frames.min(),
            original_frames.max(),
            new_frame_count
        )

        interpolated_data = []

        # Interpolate each landmark
        for landmark_id in pose_data['landmark_id'].unique():
            landmark_data = pose_data[pose_data['landmark_id'] == landmark_id].sort_values('frame_id')

            for coord in ['x', 'y', 'z', 'visibility']:
                if coord not in landmark_data.columns:
                    continue

                # Create interpolation function
                if method == 'cubic' and len(landmark_data) > 3:
                    f = interpolate.interp1d(
                        landmark_data['frame_id'].values,
                        landmark_data[coord].values,
                        kind='cubic',
                        fill_value='extrapolate'
                    )
                elif method == 'quadratic' and len(landmark_data) > 2:
                    f = interpolate.interp1d(
                        landmark_data['frame_id'].values,
                        landmark_data[coord].values,
                        kind='quadratic',
                        fill_value='extrapolate'
                    )
                else:  # Linear fallback
                    f = interpolate.interp1d(
                        landmark_data['frame_id'].values,
                        landmark_data[coord].values,
                        kind='linear',
                        fill_value='extrapolate'
                    )

                # Interpolate values
                new_values = f(new_frames)

                # Add to result
                for i, frame in enumerate(new_frames):
                    if coord == 'x':  # First coordinate, create row
                        interpolated_data.append({
                            'frame_id': int(frame) if factor > 1 else frame,
                            'timestamp': frame / target_fps,
                            'landmark_id': landmark_id,
                            coord: new_values[i]
                        })
                    else:  # Add to existing row
                        row_idx = len(interpolated_data) - len(new_frames) + i
                        interpolated_data[row_idx][coord] = new_values[i]

        return pd.DataFrame(interpolated_data)

    def create_loop(self,
                   pose_data: pd.DataFrame,
                   blend_frames: int = 10,
                   loop_type: str = 'seamless') -> pd.DataFrame:
        """
        Create a looping animation from pose data.

        Args:
            pose_data: Original pose data
            blend_frames: Number of frames to blend at loop point
            loop_type: Type of loop (seamless, pingpong, offset)

        Returns:
            Looped pose data
        """
        if loop_type == 'seamless':
            return self._create_seamless_loop(pose_data, blend_frames)
        elif loop_type == 'pingpong':
            return self._create_pingpong_loop(pose_data)
        elif loop_type == 'offset':
            return self._create_offset_loop(pose_data, blend_frames)
        else:
            return pose_data

    def add_animation_curves(self,
                           pose_data: pd.DataFrame,
                           curve_type: str = 'ease_in_out',
                           affected_frames: Optional[Tuple[int, int]] = None) -> pd.DataFrame:
        """
        Apply animation curves for more natural motion.

        Args:
            pose_data: Original pose data
            curve_type: Type of animation curve
            affected_frames: Range of frames to apply curve to

        Returns:
            Pose data with animation curves applied
        """
        curved_data = pose_data.copy()

        # Determine frame range
        if affected_frames is None:
            start_frame = pose_data['frame_id'].min()
            end_frame = pose_data['frame_id'].max()
        else:
            start_frame, end_frame = affected_frames

        frame_range = end_frame - start_frame

        # Generate curve
        curve_values = self._generate_curve(curve_type, frame_range)

        # Apply curve to motion
        for landmark_id in pose_data['landmark_id'].unique():
            mask = (pose_data['landmark_id'] == landmark_id) & \
                   (pose_data['frame_id'] >= start_frame) & \
                   (pose_data['frame_id'] <= end_frame)

            if not mask.any():
                continue

            # Get motion delta
            landmark_frames = pose_data.loc[mask].sort_values('frame_id')
            start_pos = landmark_frames.iloc[0]
            end_pos = landmark_frames.iloc[-1]

            for coord in ['x', 'y']:
                if coord not in pose_data.columns:
                    continue

                # Calculate motion path
                motion_delta = end_pos[coord] - start_pos[coord]

                # Apply curve
                for i, (idx, row) in enumerate(landmark_frames.iterrows()):
                    if i < len(curve_values):
                        new_value = start_pos[coord] + motion_delta * curve_values[i]
                        curved_data.loc[idx, coord] = new_value

        return curved_data

    def add_secondary_motion(self,
                           pose_data: pd.DataFrame,
                           motion_type: str = 'follow_through',
                           strength: float = 0.3) -> pd.DataFrame:
        """
        Add secondary animation effects.

        Args:
            pose_data: Original pose data
            motion_type: Type of secondary motion
            strength: Effect strength

        Returns:
            Enhanced pose data
        """
        enhanced_data = pose_data.copy()

        if motion_type == 'follow_through':
            enhanced_data = self._add_follow_through(enhanced_data, strength)
        elif motion_type == 'overlap':
            enhanced_data = self._add_overlap(enhanced_data, strength)
        elif motion_type == 'anticipation':
            enhanced_data = self._add_anticipation(enhanced_data, strength)

        return enhanced_data

    def _gaussian_smooth(self, values: np.ndarray, window: int, strength: float) -> np.ndarray:
        """Apply Gaussian smoothing."""
        sigma = window / 6.0 * strength
        return signal.gaussian_filter1d(values, sigma=sigma, mode='nearest')

    def _savitzky_smooth(self, values: np.ndarray, window: int) -> np.ndarray:
        """Apply Savitzky-Golay smoothing."""
        poly_order = min(3, window - 2)
        return signal.savgol_filter(values, window, poly_order, mode='nearest')

    def _exponential_smooth(self, values: np.ndarray, alpha: float) -> np.ndarray:
        """Apply exponential smoothing."""
        smoothed = np.zeros_like(values)
        smoothed[0] = values[0]

        for i in range(1, len(values)):
            smoothed[i] = alpha * values[i] + (1 - alpha) * smoothed[i - 1]

        return smoothed

    def _bilateral_smooth(self, values: np.ndarray, window: int, strength: float) -> np.ndarray:
        """Apply bilateral filtering (preserves edges)."""
        smoothed = np.zeros_like(values)
        half_window = window // 2

        for i in range(len(values)):
            start = max(0, i - half_window)
            end = min(len(values), i + half_window + 1)

            # Calculate weights based on value similarity
            local_values = values[start:end]
            center_value = values[i]

            # Spatial weights
            spatial_weights = np.exp(-np.arange(len(local_values))**2 / (2 * (window/4)**2))

            # Range weights (value similarity)
            range_weights = np.exp(-(local_values - center_value)**2 / (2 * (strength * 0.1)**2))

            # Combined weights
            weights = spatial_weights * range_weights
            weights /= weights.sum()

            smoothed[i] = np.sum(local_values * weights)

        return smoothed

    def _detect_extremes(self, pose_data: pd.DataFrame) -> Dict:
        """Detect extreme poses in animation."""
        extremes = {}

        for landmark_id in pose_data['landmark_id'].unique():
            landmark_data = pose_data[pose_data['landmark_id'] == landmark_id]
            extremes[landmark_id] = {}

            for coord in ['x', 'y', 'z']:
                if coord not in landmark_data.columns:
                    continue

                values = landmark_data[coord].values

                # Find local maxima and minima
                peaks, _ = signal.find_peaks(values, prominence=0.05)
                valleys, _ = signal.find_peaks(-values, prominence=0.05)

                extremes[landmark_id][coord] = {
                    'peaks': peaks,
                    'valleys': valleys
                }

        return extremes

    def _restore_extremes(self,
                         smoothed: np.ndarray,
                         original: np.ndarray,
                         extremes: Dict,
                         landmark_id: int,
                         coord: str) -> np.ndarray:
        """Restore extreme poses after smoothing."""
        if landmark_id not in extremes or coord not in extremes[landmark_id]:
            return smoothed

        extreme_data = extremes[landmark_id][coord]

        # Restore peaks
        for peak_idx in extreme_data['peaks']:
            if peak_idx < len(smoothed):
                # Blend original extreme with smoothed
                smoothed[peak_idx] = 0.7 * original[peak_idx] + 0.3 * smoothed[peak_idx]

        # Restore valleys
        for valley_idx in extreme_data['valleys']:
            if valley_idx < len(smoothed):
                smoothed[valley_idx] = 0.7 * original[valley_idx] + 0.3 * smoothed[valley_idx]

        return smoothed

    def _create_seamless_loop(self, pose_data: pd.DataFrame, blend_frames: int) -> pd.DataFrame:
        """Create a seamless loop by blending start and end."""
        looped_data = pose_data.copy()

        max_frame = pose_data['frame_id'].max()
        min_frame = pose_data['frame_id'].min()

        # For each landmark, blend the transition
        for landmark_id in pose_data['landmark_id'].unique():
            landmark_data = pose_data[pose_data['landmark_id'] == landmark_id].sort_values('frame_id')

            for coord in ['x', 'y', 'z']:
                if coord not in landmark_data.columns:
                    continue

                # Get start and end positions
                start_frames = landmark_data[landmark_data['frame_id'] < min_frame + blend_frames]
                end_frames = landmark_data[landmark_data['frame_id'] > max_frame - blend_frames]

                if len(start_frames) == 0 or len(end_frames) == 0:
                    continue

                # Calculate blend weights
                for i in range(min(blend_frames, len(start_frames), len(end_frames))):
                    weight = i / blend_frames

                    # Blend start frame toward end position
                    start_idx = start_frames.index[i]
                    end_value = end_frames.iloc[-(i+1)][coord]
                    start_value = start_frames.iloc[i][coord]

                    blended = start_value * (1 - weight) + end_value * weight
                    looped_data.loc[start_idx, coord] = blended

                    # Blend end frame toward start position
                    end_idx = end_frames.index[-(i+1)]
                    start_value = start_frames.iloc[i][coord]
                    end_value = end_frames.iloc[-(i+1)][coord]

                    blended = end_value * (1 - weight) + start_value * weight
                    looped_data.loc[end_idx, coord] = blended

        return looped_data

    def _create_pingpong_loop(self, pose_data: pd.DataFrame) -> pd.DataFrame:
        """Create a ping-pong loop (forward then reverse)."""
        # Get forward animation
        forward = pose_data.copy()

        # Create reverse animation
        reverse = pose_data.copy()
        max_frame = pose_data['frame_id'].max()
        reverse['frame_id'] = max_frame * 2 - reverse['frame_id'] + 1
        reverse['timestamp'] = reverse['frame_id'] / self.fps

        # Combine forward and reverse
        looped = pd.concat([forward, reverse], ignore_index=True)

        return looped.sort_values(['frame_id', 'landmark_id']).reset_index(drop=True)

    def _create_offset_loop(self, pose_data: pd.DataFrame, blend_frames: int) -> pd.DataFrame:
        """Create an offset loop with position adjustment."""
        looped_data = pose_data.copy()

        # Calculate position offset between start and end
        first_frame = pose_data[pose_data['frame_id'] == pose_data['frame_id'].min()]
        last_frame = pose_data[pose_data['frame_id'] == pose_data['frame_id'].max()]

        # Calculate average offset
        x_offset = 0
        y_offset = 0

        for landmark_id in pose_data['landmark_id'].unique()[:5]:  # Use first 5 landmarks
            first = first_frame[first_frame['landmark_id'] == landmark_id]
            last = last_frame[last_frame['landmark_id'] == landmark_id]

            if not first.empty and not last.empty:
                x_offset += last['x'].iloc[0] - first['x'].iloc[0]
                y_offset += last['y'].iloc[0] - first['y'].iloc[0]

        x_offset /= 5
        y_offset /= 5

        # Apply gradual offset correction
        max_frame = pose_data['frame_id'].max()

        for frame_id in pose_data['frame_id'].unique():
            frame_progress = frame_id / max_frame
            frame_mask = looped_data['frame_id'] == frame_id

            # Gradually remove offset
            looped_data.loc[frame_mask, 'x'] -= x_offset * frame_progress
            looped_data.loc[frame_mask, 'y'] -= y_offset * frame_progress

        return looped_data

    def _generate_curve(self, curve_type: str, num_frames: int) -> np.ndarray:
        """Generate animation curve values."""
        t = np.linspace(0, 1, num_frames)

        if curve_type == 'linear':
            return t
        elif curve_type == 'ease_in':
            return t ** 2
        elif curve_type == 'ease_out':
            return 1 - (1 - t) ** 2
        elif curve_type == 'ease_in_out':
            return np.where(t < 0.5, 2 * t ** 2, 1 - 2 * (1 - t) ** 2)
        elif curve_type == 'cubic':
            return t ** 3
        elif curve_type == 'bounce':
            return np.abs(np.sin(t * np.pi * 2))
        elif curve_type == 'elastic':
            return np.sin(t * np.pi * 4) * np.exp(-t * 2) + t
        else:
            return t

    def _add_follow_through(self, pose_data: pd.DataFrame, strength: float) -> pd.DataFrame:
        """Add follow-through motion to extremities."""
        enhanced = pose_data.copy()

        # Define extremity landmarks (hands, feet)
        extremities = [15, 16, 27, 28]  # Wrists and ankles

        for landmark_id in extremities:
            landmark_data = enhanced[enhanced['landmark_id'] == landmark_id].sort_values('frame_id')

            if len(landmark_data) < 3:
                continue

            for coord in ['x', 'y']:
                if coord not in landmark_data.columns:
                    continue

                values = landmark_data[coord].values

                # Calculate velocity
                velocity = np.diff(values)
                velocity = np.append(velocity, velocity[-1])

                # Add delayed motion based on velocity
                for i in range(2, len(values)):
                    # Add a portion of previous frame's velocity
                    values[i] += velocity[i-2] * strength * 0.1

                # Update data
                enhanced.loc[landmark_data.index, coord] = values

        return enhanced

    def _add_overlap(self, pose_data: pd.DataFrame, strength: float) -> pd.DataFrame:
        """Add overlapping motion for connected parts."""
        enhanced = pose_data.copy()

        # Define parent-child relationships
        relationships = [
            (11, 13),  # Shoulder to elbow
            (13, 15),  # Elbow to wrist
            (12, 14),  # Right shoulder to elbow
            (14, 16),  # Right elbow to wrist
        ]

        for parent_id, child_id in relationships:
            parent_data = enhanced[enhanced['landmark_id'] == parent_id].sort_values('frame_id')
            child_data = enhanced[enhanced['landmark_id'] == child_id].sort_values('frame_id')

            if len(parent_data) < 2 or len(child_data) < 2:
                continue

            for coord in ['x', 'y']:
                if coord not in parent_data.columns:
                    continue

                parent_values = parent_data[coord].values
                child_values = child_data[coord].values

                # Calculate parent motion
                parent_motion = np.diff(parent_values)
                parent_motion = np.append([0], parent_motion)

                # Apply delayed motion to child
                for i in range(1, len(child_values)):
                    if i < len(parent_motion):
                        child_values[i] += parent_motion[i-1] * strength * 0.5

                # Update data
                enhanced.loc[child_data.index, coord] = child_values

        return enhanced

    def _add_anticipation(self, pose_data: pd.DataFrame, strength: float) -> pd.DataFrame:
        """Add anticipation before major movements."""
        enhanced = pose_data.copy()

        for landmark_id in pose_data['landmark_id'].unique():
            landmark_data = enhanced[enhanced['landmark_id'] == landmark_id].sort_values('frame_id')

            if len(landmark_data) < 5:
                continue

            for coord in ['x', 'y']:
                if coord not in landmark_data.columns:
                    continue

                values = landmark_data[coord].values

                # Detect large movements
                diffs = np.diff(values)
                large_movements = np.abs(diffs) > np.std(diffs) * 2

                # Add anticipation before large movements
                for i in range(2, len(values) - 1):
                    if i < len(large_movements) and large_movements[i]:
                        # Move slightly in opposite direction before movement
                        values[i-1] -= diffs[i] * strength * 0.2

                # Update data
                enhanced.loc[landmark_data.index, coord] = values

        return enhanced


def test_animation_tools():
    """Test the animation tools module."""
    print("\n=== Testing Animation Tools ===\n")

    # Create sample animation data
    np.random.seed(42)
    n_frames = 60
    data = []

    for frame_id in range(n_frames):
        for landmark_id in range(33):
            # Create bouncing motion
            phase = frame_id * 0.15
            x = 0.5 + 0.2 * np.sin(phase)
            y = 0.3 + 0.3 * np.abs(np.sin(phase * 2))
            z = 0.1

            # Add some noise
            x += np.random.normal(0, 0.01)
            y += np.random.normal(0, 0.01)

            data.append({
                'frame_id': frame_id,
                'timestamp': frame_id / 30.0,
                'landmark_id': landmark_id,
                'x': x,
                'y': y,
                'z': z,
                'visibility': 0.95
            })

    pose_df = pd.DataFrame(data)

    # Initialize processor
    processor = AnimationProcessor(fps=30)

    # Test smoothing
    print("Testing animation smoothing:")
    smoothed = processor.smooth_animation(pose_df, 'gaussian', strength=0.7)
    print(f"  ✓ Applied Gaussian smoothing")

    # Test frame interpolation
    print("\nTesting frame interpolation:")
    interpolated = processor.interpolate_frames(pose_df, target_fps=60, method='cubic')
    print(f"  ✓ Interpolated from 30fps to 60fps ({len(interpolated) // 33} frames)")

    # Test loop creation
    print("\nTesting loop generation:")
    looped = processor.create_loop(pose_df, blend_frames=10, loop_type='seamless')
    print(f"  ✓ Created seamless loop")

    pingpong = processor.create_loop(pose_df, loop_type='pingpong')
    print(f"  ✓ Created ping-pong loop ({len(pingpong) // 33} frames)")

    # Test animation curves
    print("\nTesting animation curves:")
    curved = processor.add_animation_curves(pose_df, curve_type='ease_in_out')
    print(f"  ✓ Applied ease-in-out curve")

    # Test secondary motion
    print("\nTesting secondary motion:")
    enhanced = processor.add_secondary_motion(pose_df, 'follow_through', strength=0.3)
    print(f"  ✓ Added follow-through motion")

    enhanced = processor.add_secondary_motion(enhanced, 'anticipation', strength=0.2)
    print(f"  ✓ Added anticipation")

    # Save test results
    smoothed.head(100).to_csv('animation_test_smoothed.csv', index=False)
    looped.head(100).to_csv('animation_test_looped.csv', index=False)
    print("\n✓ Test results saved to CSV files")


if __name__ == "__main__":
    test_animation_tools()