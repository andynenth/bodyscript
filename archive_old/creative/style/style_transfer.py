"""
Style Transfer Module - Transform poses between different artistic styles
Supports realistic to anime, cartoon, minimalist, and custom styles
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class StyleProfile:
    """Defines characteristics of an artistic style."""
    name: str
    proportions: Dict[str, float]  # Body part scaling
    joint_constraints: Dict[str, Tuple[float, float]]  # Min/max angles
    simplification_level: float  # 0-1, how much to simplify
    exaggeration_factors: Dict[str, float]  # Part-specific exaggeration
    smoothing_strength: float  # Temporal smoothing
    characteristic_poses: List[Dict]  # Signature poses for the style


class PoseStyleTransfer:
    """
    Transform pose data between different artistic styles.
    """

    # Predefined style profiles
    STYLES = {
        'realistic': StyleProfile(
            name='realistic',
            proportions={
                'head': 1.0, 'torso': 1.0, 'arms': 1.0, 'legs': 1.0
            },
            joint_constraints={
                'elbow': (0, 180), 'knee': (0, 180),
                'shoulder': (0, 180), 'hip': (0, 180)
            },
            simplification_level=0.0,
            exaggeration_factors={
                'expression': 1.0, 'gesture': 1.0, 'posture': 1.0
            },
            smoothing_strength=0.3,
            characteristic_poses=[]
        ),

        'anime': StyleProfile(
            name='anime',
            proportions={
                'head': 1.2,  # Larger head
                'torso': 0.9,  # Slimmer torso
                'arms': 1.1,  # Slightly longer arms
                'legs': 1.15  # Longer legs
            },
            joint_constraints={
                'elbow': (10, 170),  # More restricted for cleaner lines
                'knee': (10, 170),
                'shoulder': (0, 180),
                'hip': (0, 160)
            },
            simplification_level=0.4,  # Simplify complex movements
            exaggeration_factors={
                'expression': 1.5,  # Exaggerated expressions
                'gesture': 1.3,  # Dramatic gestures
                'posture': 1.2  # Enhanced posture
            },
            smoothing_strength=0.5,  # Smoother movements
            characteristic_poses=[
                {'name': 'power_stance', 'weight': 1.2},
                {'name': 'dynamic_action', 'weight': 1.3}
            ]
        ),

        'cartoon': StyleProfile(
            name='cartoon',
            proportions={
                'head': 1.4,  # Very large head
                'torso': 1.0,
                'arms': 0.9,  # Shorter arms
                'legs': 0.8  # Shorter legs
            },
            joint_constraints={
                'elbow': (20, 160),
                'knee': (20, 160),
                'shoulder': (0, 170),
                'hip': (0, 150)
            },
            simplification_level=0.6,  # High simplification
            exaggeration_factors={
                'expression': 2.0,  # Very exaggerated
                'gesture': 1.8,
                'posture': 1.5
            },
            smoothing_strength=0.7,
            characteristic_poses=[
                {'name': 'bounce', 'weight': 1.5},
                {'name': 'squash_stretch', 'weight': 1.4}
            ]
        ),

        'minimalist': StyleProfile(
            name='minimalist',
            proportions={
                'head': 1.0, 'torso': 1.0, 'arms': 1.0, 'legs': 1.0
            },
            joint_constraints={
                'elbow': (30, 150),
                'knee': (30, 150),
                'shoulder': (20, 160),
                'hip': (20, 140)
            },
            simplification_level=0.8,  # Maximum simplification
            exaggeration_factors={
                'expression': 0.7,  # Reduced movement
                'gesture': 0.8,
                'posture': 0.9
            },
            smoothing_strength=0.9,  # Very smooth
            characteristic_poses=[]
        ),

        'athletic': StyleProfile(
            name='athletic',
            proportions={
                'head': 0.95,
                'torso': 1.1,  # Broader torso
                'arms': 1.05,  # Muscular arms
                'legs': 1.1  # Powerful legs
            },
            joint_constraints={
                'elbow': (0, 180),
                'knee': (0, 180),
                'shoulder': (0, 190),  # Extended range
                'hip': (0, 190)
            },
            simplification_level=0.1,
            exaggeration_factors={
                'expression': 1.0,
                'gesture': 1.4,  # Dynamic movements
                'posture': 1.3  # Athletic posture
            },
            smoothing_strength=0.2,
            characteristic_poses=[
                {'name': 'athletic_ready', 'weight': 1.3},
                {'name': 'power_movement', 'weight': 1.4}
            ]
        )
    }

    # Body part groupings for proportion scaling
    BODY_PARTS = {
        'head': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # Face and head landmarks
        'torso': [11, 12, 23, 24],  # Shoulders and hips
        'arms': [11, 12, 13, 14, 15, 16],  # Shoulders to hands
        'legs': [23, 24, 25, 26, 27, 28, 29, 30, 31, 32]  # Hips to feet
    }

    def __init__(self):
        """Initialize the style transfer system."""
        self.current_style = self.STYLES['realistic']
        self.custom_styles = {}

    def transform_pose(self,
                       pose_data: pd.DataFrame,
                       target_style: str,
                       strength: float = 1.0) -> pd.DataFrame:
        """
        Transform pose data to a target artistic style.

        Args:
            pose_data: DataFrame with pose landmarks
            target_style: Name of target style
            strength: Transformation strength (0-1)

        Returns:
            Transformed pose DataFrame
        """
        if target_style not in self.STYLES and target_style not in self.custom_styles:
            raise ValueError(f"Unknown style: {target_style}")

        style = self.STYLES.get(target_style, self.custom_styles.get(target_style))

        # Create a copy for transformation
        transformed_data = pose_data.copy()

        # Apply transformations
        transformed_data = self._apply_proportions(transformed_data, style, strength)
        transformed_data = self._apply_constraints(transformed_data, style)
        transformed_data = self._apply_simplification(transformed_data, style.simplification_level * strength)
        transformed_data = self._apply_exaggeration(transformed_data, style, strength)
        transformed_data = self._apply_smoothing(transformed_data, style.smoothing_strength * strength)

        # Add style metadata
        transformed_data['style'] = target_style
        transformed_data['style_strength'] = strength

        return transformed_data

    def _apply_proportions(self,
                          data: pd.DataFrame,
                          style: StyleProfile,
                          strength: float) -> pd.DataFrame:
        """Apply proportion changes based on style."""
        for body_part, landmarks in self.BODY_PARTS.items():
            if body_part not in style.proportions:
                continue

            scale_factor = 1.0 + (style.proportions[body_part] - 1.0) * strength

            # Apply scaling to relevant landmarks
            mask = data['landmark_id'].isin(landmarks)

            if body_part == 'head':
                # Scale head relative to neck
                neck_point = self._get_neck_center(data)
                if neck_point is not None:
                    data.loc[mask, 'y'] = neck_point[1] + (data.loc[mask, 'y'] - neck_point[1]) * scale_factor
                    data.loc[mask, 'x'] = neck_point[0] + (data.loc[mask, 'x'] - neck_point[0]) * scale_factor

            elif body_part == 'torso':
                # Scale torso width and height
                center = self._get_torso_center(data)
                if center is not None:
                    data.loc[mask, 'x'] = center[0] + (data.loc[mask, 'x'] - center[0]) * scale_factor
                    data.loc[mask, 'y'] = center[1] + (data.loc[mask, 'y'] - center[1]) * (scale_factor * 0.8)

            elif body_part == 'arms':
                # Scale arm length from shoulders
                for side_landmarks in [[11, 13, 15], [12, 14, 16]]:  # Left and right arms
                    self._scale_limb(data, side_landmarks, scale_factor)

            elif body_part == 'legs':
                # Scale leg length from hips
                for side_landmarks in [[23, 25, 27], [24, 26, 28]]:  # Left and right legs
                    self._scale_limb(data, side_landmarks, scale_factor)

        return data

    def _apply_constraints(self,
                          data: pd.DataFrame,
                          style: StyleProfile) -> pd.DataFrame:
        """Apply joint angle constraints based on style."""
        # This would integrate with the analytics module to constrain angles
        # For now, we'll implement basic position constraints

        for joint_name, (min_angle, max_angle) in style.joint_constraints.items():
            # Apply constraints to maintain style-appropriate poses
            # This is simplified - full implementation would calculate actual angles
            pass

        return data

    def _apply_simplification(self,
                             data: pd.DataFrame,
                             level: float) -> pd.DataFrame:
        """Simplify pose by reducing detail and noise."""
        if level <= 0:
            return data

        # Reduce precision based on simplification level
        decimal_places = max(1, int(4 * (1 - level)))

        for coord in ['x', 'y', 'z']:
            if coord in data.columns:
                data[coord] = data[coord].round(decimal_places)

        # Remove small movements
        threshold = 0.01 * level
        for coord in ['x', 'y']:
            if coord in data.columns:
                # Group by landmark and frame
                for landmark_id in data['landmark_id'].unique():
                    mask = data['landmark_id'] == landmark_id
                    values = data.loc[mask, coord].values

                    if len(values) > 1:
                        diffs = np.abs(np.diff(values))
                        small_movements = diffs < threshold

                        # Propagate previous value for small movements
                        for i, is_small in enumerate(small_movements):
                            if is_small:
                                values[i + 1] = values[i]

                        data.loc[mask, coord] = values

        return data

    def _apply_exaggeration(self,
                           data: pd.DataFrame,
                           style: StyleProfile,
                           strength: float) -> pd.DataFrame:
        """Apply style-specific exaggerations."""
        # Exaggerate gestures (arm movements)
        if 'gesture' in style.exaggeration_factors:
            gesture_factor = 1.0 + (style.exaggeration_factors['gesture'] - 1.0) * strength

            # Find center of mass
            center_x = data.groupby('frame_id')['x'].mean()
            center_y = data.groupby('frame_id')['y'].mean()

            # Exaggerate arm movements from center
            arm_landmarks = [13, 14, 15, 16]  # Elbows and wrists
            for landmark_id in arm_landmarks:
                mask = data['landmark_id'] == landmark_id

                for frame_id in data.loc[mask, 'frame_id'].unique():
                    frame_mask = mask & (data['frame_id'] == frame_id)

                    if frame_id in center_x.index:
                        cx = center_x[frame_id]
                        cy = center_y[frame_id]

                        # Exaggerate distance from center
                        data.loc[frame_mask, 'x'] = cx + (data.loc[frame_mask, 'x'] - cx) * gesture_factor
                        data.loc[frame_mask, 'y'] = cy + (data.loc[frame_mask, 'y'] - cy) * gesture_factor

        # Exaggerate posture (spine alignment)
        if 'posture' in style.exaggeration_factors:
            posture_factor = 1.0 + (style.exaggeration_factors['posture'] - 1.0) * strength

            # Enhance vertical alignment for spine
            spine_landmarks = [11, 12, 23, 24]  # Shoulders and hips
            for frame_id in data['frame_id'].unique():
                frame_mask = data['frame_id'] == frame_id
                spine_mask = frame_mask & data['landmark_id'].isin(spine_landmarks)

                if spine_mask.any():
                    # Make spine more vertical
                    spine_data = data.loc[spine_mask]
                    mean_x = spine_data['x'].mean()

                    # Pull spine landmarks toward vertical line
                    data.loc[spine_mask, 'x'] = mean_x + (data.loc[spine_mask, 'x'] - mean_x) * (2.0 - posture_factor)

        return data

    def _apply_smoothing(self,
                        data: pd.DataFrame,
                        strength: float) -> pd.DataFrame:
        """Apply temporal smoothing for fluid animation."""
        if strength <= 0:
            return data

        window_size = max(3, int(strength * 10))
        if window_size % 2 == 0:
            window_size += 1  # Ensure odd window

        for landmark_id in data['landmark_id'].unique():
            mask = data['landmark_id'] == landmark_id

            for coord in ['x', 'y', 'z']:
                if coord not in data.columns:
                    continue

                values = data.loc[mask, coord].values

                if len(values) > window_size:
                    # Apply moving average
                    from scipy.ndimage import uniform_filter1d
                    smoothed = uniform_filter1d(values, size=window_size, mode='nearest')

                    # Blend based on strength
                    data.loc[mask, coord] = values * (1 - strength) + smoothed * strength

        return data

    def _get_neck_center(self, data: pd.DataFrame) -> Optional[Tuple[float, float]]:
        """Get the neck center point."""
        shoulder_landmarks = [11, 12]
        frame0_mask = (data['frame_id'] == data['frame_id'].min())
        shoulders = data[frame0_mask & data['landmark_id'].isin(shoulder_landmarks)]

        if len(shoulders) >= 2:
            return (shoulders['x'].mean(), shoulders['y'].mean())
        return None

    def _get_torso_center(self, data: pd.DataFrame) -> Optional[Tuple[float, float]]:
        """Get the torso center point."""
        torso_landmarks = [11, 12, 23, 24]
        frame0_mask = (data['frame_id'] == data['frame_id'].min())
        torso = data[frame0_mask & data['landmark_id'].isin(torso_landmarks)]

        if len(torso) >= 4:
            return (torso['x'].mean(), torso['y'].mean())
        return None

    def _scale_limb(self, data: pd.DataFrame, landmarks: List[int], scale_factor: float):
        """Scale a limb (arm or leg) from its root joint."""
        if len(landmarks) < 2:
            return

        root_landmark = landmarks[0]

        for frame_id in data['frame_id'].unique():
            frame_mask = data['frame_id'] == frame_id

            # Get root position
            root_mask = frame_mask & (data['landmark_id'] == root_landmark)
            if not root_mask.any():
                continue

            root_x = data.loc[root_mask, 'x'].iloc[0]
            root_y = data.loc[root_mask, 'y'].iloc[0]

            # Scale other joints from root
            for landmark_id in landmarks[1:]:
                joint_mask = frame_mask & (data['landmark_id'] == landmark_id)
                if joint_mask.any():
                    data.loc[joint_mask, 'x'] = root_x + (data.loc[joint_mask, 'x'] - root_x) * scale_factor
                    data.loc[joint_mask, 'y'] = root_y + (data.loc[joint_mask, 'y'] - root_y) * scale_factor

    def create_custom_style(self,
                           name: str,
                           base_style: str = 'realistic',
                           **modifications) -> StyleProfile:
        """
        Create a custom style based on an existing style.

        Args:
            name: Name for the custom style
            base_style: Base style to modify
            **modifications: Style parameters to modify

        Returns:
            Custom StyleProfile
        """
        if base_style not in self.STYLES:
            raise ValueError(f"Unknown base style: {base_style}")

        base = self.STYLES[base_style]

        # Create custom style with modifications
        custom = StyleProfile(
            name=name,
            proportions=modifications.get('proportions', base.proportions.copy()),
            joint_constraints=modifications.get('joint_constraints', base.joint_constraints.copy()),
            simplification_level=modifications.get('simplification_level', base.simplification_level),
            exaggeration_factors=modifications.get('exaggeration_factors', base.exaggeration_factors.copy()),
            smoothing_strength=modifications.get('smoothing_strength', base.smoothing_strength),
            characteristic_poses=modifications.get('characteristic_poses', base.characteristic_poses.copy())
        )

        self.custom_styles[name] = custom
        return custom

    def blend_styles(self,
                    pose_data: pd.DataFrame,
                    styles: List[Tuple[str, float]]) -> pd.DataFrame:
        """
        Blend multiple styles with weighted contributions.

        Args:
            pose_data: Original pose data
            styles: List of (style_name, weight) tuples

        Returns:
            Blended pose data
        """
        if not styles:
            return pose_data

        # Normalize weights
        total_weight = sum(weight for _, weight in styles)
        normalized_styles = [(name, weight / total_weight) for name, weight in styles]

        # Start with zero transformation
        blended = pose_data.copy()
        blended[['x', 'y', 'z']] = 0

        # Add weighted contributions from each style
        for style_name, weight in normalized_styles:
            transformed = self.transform_pose(pose_data, style_name, strength=1.0)

            for coord in ['x', 'y', 'z']:
                if coord in blended.columns:
                    blended[coord] += transformed[coord] * weight

        return blended

    def get_style_preview(self, style_name: str) -> Dict:
        """
        Get preview information about a style.

        Args:
            style_name: Name of the style

        Returns:
            Dictionary with style characteristics
        """
        if style_name not in self.STYLES and style_name not in self.custom_styles:
            return {'error': f"Unknown style: {style_name}"}

        style = self.STYLES.get(style_name, self.custom_styles.get(style_name))

        return {
            'name': style.name,
            'proportions': style.proportions,
            'simplification': f"{style.simplification_level * 100:.0f}%",
            'smoothing': f"{style.smoothing_strength * 100:.0f}%",
            'exaggeration': style.exaggeration_factors,
            'characteristics': [pose['name'] for pose in style.characteristic_poses]
        }


def test_style_transfer():
    """Test the style transfer module."""
    print("\n=== Testing Style Transfer Module ===\n")

    # Create sample pose data
    np.random.seed(42)
    n_frames = 30
    data = []

    for frame_id in range(n_frames):
        for landmark_id in range(33):
            # Create walking motion
            phase = frame_id * 0.2
            x = 0.5 + 0.1 * np.sin(phase + landmark_id * 0.1)
            y = 0.5 + 0.1 * np.cos(phase + landmark_id * 0.1)
            z = 0.1

            data.append({
                'frame_id': frame_id,
                'landmark_id': landmark_id,
                'x': x,
                'y': y,
                'z': z
            })

    pose_df = pd.DataFrame(data)

    # Initialize style transfer
    transfer = PoseStyleTransfer()

    # Test different styles
    styles_to_test = ['anime', 'cartoon', 'minimalist', 'athletic']

    for style_name in styles_to_test:
        print(f"\nTesting {style_name} style:")

        # Get style preview
        preview = transfer.get_style_preview(style_name)
        print(f"  Proportions: {preview['proportions']}")
        print(f"  Simplification: {preview['simplification']}")
        print(f"  Smoothing: {preview['smoothing']}")

        # Transform pose
        transformed = transfer.transform_pose(pose_df, style_name, strength=0.8)

        # Check transformation
        print(f"  ✓ Transformed {len(transformed)} pose points")

        # Calculate change metrics
        x_change = (transformed['x'] - pose_df['x']).abs().mean()
        y_change = (transformed['y'] - pose_df['y']).abs().mean()

        print(f"  Average position change: X={x_change:.3f}, Y={y_change:.3f}")

    # Test style blending
    print("\n\nTesting style blending:")
    blended = transfer.blend_styles(pose_df, [
        ('anime', 0.5),
        ('athletic', 0.5)
    ])
    print("  ✓ Blended anime (50%) + athletic (50%) styles")

    # Create custom style
    print("\n\nCreating custom style:")
    custom = transfer.create_custom_style(
        'superhero',
        base_style='athletic',
        proportions={'torso': 1.3, 'arms': 1.2, 'legs': 1.1},
        exaggeration_factors={'gesture': 1.8, 'posture': 1.5}
    )
    print(f"  ✓ Created custom 'superhero' style based on athletic")

    # Save test results
    transformed_anime = transfer.transform_pose(pose_df, 'anime', strength=1.0)
    transformed_anime.head(100).to_csv('style_transfer_test.csv', index=False)
    print("\n✓ Test results saved to style_transfer_test.csv")


if __name__ == "__main__":
    test_style_transfer()