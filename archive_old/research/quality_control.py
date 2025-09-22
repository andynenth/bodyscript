"""
Quality Control Module - Data filtering, smoothing, and interpolation
Ensures research-grade data quality through various processing techniques
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from scipy import signal, interpolate
from dataclasses import dataclass
import warnings


@dataclass
class QualityMetrics:
    """Metrics for assessing pose detection quality."""
    detection_rate: float
    avg_confidence: float
    temporal_consistency: float
    missing_landmarks_rate: float
    jitter_score: float
    frame_coverage: float

    def get_overall_score(self) -> float:
        """Calculate overall quality score (0-1)."""
        weights = {
            'detection': 0.3,
            'confidence': 0.2,
            'consistency': 0.2,
            'completeness': 0.15,
            'smoothness': 0.15
        }

        score = (
            weights['detection'] * self.detection_rate +
            weights['confidence'] * self.avg_confidence +
            weights['consistency'] * self.temporal_consistency +
            weights['completeness'] * (1 - self.missing_landmarks_rate) +
            weights['smoothness'] * (1 - min(self.jitter_score, 1.0))
        )

        return min(max(score, 0.0), 1.0)

    def is_research_quality(self) -> bool:
        """Check if data meets research quality standards."""
        return (
            self.detection_rate >= 0.8 and
            self.avg_confidence >= 0.6 and
            self.temporal_consistency >= 0.7 and
            self.missing_landmarks_rate <= 0.2
        )


class QualityControl:
    """
    Comprehensive quality control for pose detection data.
    Provides filtering, smoothing, interpolation, and quality assessment.
    """

    def __init__(self, confidence_threshold: float = 0.5,
                 smoothing_window: int = 5,
                 interpolation_method: str = 'linear'):
        """
        Initialize quality control system.

        Args:
            confidence_threshold: Minimum confidence for landmarks
            smoothing_window: Window size for temporal smoothing
            interpolation_method: Method for interpolating missing data
        """
        self.confidence_threshold = confidence_threshold
        self.smoothing_window = smoothing_window
        self.interpolation_method = interpolation_method

        # Savitzky-Golay filter parameters
        self.savgol_window = max(smoothing_window, 5)
        if self.savgol_window % 2 == 0:
            self.savgol_window += 1  # Ensure odd window
        self.savgol_poly = min(3, self.savgol_window - 2)

    def filter_by_confidence(self, df: pd.DataFrame,
                           confidence_column: str = 'visibility') -> pd.DataFrame:
        """
        Filter landmarks based on confidence threshold.

        Args:
            df: DataFrame with pose data
            confidence_column: Column name containing confidence scores

        Returns:
            Filtered DataFrame
        """
        if confidence_column not in df.columns:
            warnings.warn(f"Column '{confidence_column}' not found. Skipping confidence filtering.")
            return df

        # Mark low confidence landmarks as missing
        mask = df[confidence_column] >= self.confidence_threshold
        df_filtered = df.copy()

        # Set low confidence coordinates to NaN
        low_conf_mask = ~mask
        df_filtered.loc[low_conf_mask, ['x', 'y', 'z']] = np.nan

        # Track filtering statistics
        total_landmarks = len(df)
        filtered_count = low_conf_mask.sum()
        print(f"Filtered {filtered_count}/{total_landmarks} low-confidence landmarks "
              f"({filtered_count/total_landmarks*100:.1f}%)")

        return df_filtered

    def apply_temporal_smoothing(self, df: pd.DataFrame,
                                columns: List[str] = ['x', 'y', 'z']) -> pd.DataFrame:
        """
        Apply temporal smoothing to reduce jitter.

        Args:
            df: DataFrame with pose data
            columns: Columns to smooth

        Returns:
            Smoothed DataFrame
        """
        df_smoothed = df.copy()

        # Group by landmark for consistent smoothing
        if 'landmark_id' in df.columns:
            for landmark_id in df['landmark_id'].unique():
                landmark_mask = df['landmark_id'] == landmark_id

                for col in columns:
                    if col not in df.columns:
                        continue

                    values = df.loc[landmark_mask, col].values

                    # Skip if too few valid values
                    valid_mask = ~np.isnan(values)
                    if valid_mask.sum() < self.savgol_window:
                        continue

                    # Apply Savitzky-Golay filter for smooth derivatives
                    try:
                        smoothed = self._savgol_smooth(values)
                        df_smoothed.loc[landmark_mask, col] = smoothed
                    except Exception as e:
                        warnings.warn(f"Smoothing failed for landmark {landmark_id}, column {col}: {e}")

        else:
            # Apply smoothing to entire columns
            for col in columns:
                if col not in df.columns:
                    continue

                values = df[col].values
                smoothed = self._savgol_smooth(values)
                df_smoothed[col] = smoothed

        return df_smoothed

    def _savgol_smooth(self, values: np.ndarray) -> np.ndarray:
        """
        Apply Savitzky-Golay smoothing to a time series.

        Args:
            values: Input time series

        Returns:
            Smoothed values
        """
        # Handle NaN values
        valid_mask = ~np.isnan(values)

        if valid_mask.sum() < self.savgol_window:
            return values  # Not enough valid points

        # Create interpolated version for smoothing
        indices = np.arange(len(values))
        valid_indices = indices[valid_mask]
        valid_values = values[valid_mask]

        # Interpolate to fill gaps temporarily
        if len(valid_indices) > 1:
            f = interpolate.interp1d(valid_indices, valid_values,
                                    kind='linear', fill_value='extrapolate')
            interpolated = f(indices)

            # Apply Savitzky-Golay filter
            smoothed = signal.savgol_filter(interpolated, self.savgol_window,
                                          self.savgol_poly, mode='nearest')

            # Restore NaN values where originally missing
            smoothed[~valid_mask] = np.nan

            return smoothed

        return values

    def interpolate_missing_points(self, df: pd.DataFrame,
                                  max_gap: int = 10) -> pd.DataFrame:
        """
        Interpolate missing landmarks using surrounding frames.

        Args:
            df: DataFrame with pose data
            max_gap: Maximum frame gap to interpolate

        Returns:
            DataFrame with interpolated values
        """
        df_interpolated = df.copy()

        if 'landmark_id' not in df.columns:
            return df_interpolated

        # Process each landmark separately
        for landmark_id in df['landmark_id'].unique():
            landmark_mask = df['landmark_id'] == landmark_id
            landmark_data = df[landmark_mask].copy()

            # Sort by frame_id to ensure proper order
            if 'frame_id' in landmark_data.columns:
                landmark_data = landmark_data.sort_values('frame_id')

            for col in ['x', 'y', 'z']:
                if col not in landmark_data.columns:
                    continue

                values = landmark_data[col].values

                # Find gaps
                nan_mask = np.isnan(values)
                if not nan_mask.any():
                    continue  # No missing values

                # Identify gap sizes
                gap_groups = self._identify_gaps(nan_mask)

                for start_idx, end_idx in gap_groups:
                    gap_size = end_idx - start_idx

                    if gap_size <= max_gap:
                        # Interpolate this gap
                        interpolated = self._interpolate_gap(values, start_idx, end_idx)
                        values[start_idx:end_idx] = interpolated

                # Update the dataframe
                landmark_indices = landmark_data.index
                df_interpolated.loc[landmark_indices, col] = values

        # Report interpolation statistics
        original_missing = df[['x', 'y', 'z']].isna().sum().sum()
        final_missing = df_interpolated[['x', 'y', 'z']].isna().sum().sum()
        interpolated_count = original_missing - final_missing

        if original_missing > 0:
            print(f"Interpolated {interpolated_count}/{original_missing} missing values "
                  f"({interpolated_count/original_missing*100:.1f}%)")

        return df_interpolated

    def _identify_gaps(self, nan_mask: np.ndarray) -> List[Tuple[int, int]]:
        """Identify continuous gaps in the data."""
        gaps = []
        in_gap = False
        start_idx = 0

        for i, is_nan in enumerate(nan_mask):
            if is_nan and not in_gap:
                start_idx = i
                in_gap = True
            elif not is_nan and in_gap:
                gaps.append((start_idx, i))
                in_gap = False

        # Handle gap at the end
        if in_gap:
            gaps.append((start_idx, len(nan_mask)))

        return gaps

    def _interpolate_gap(self, values: np.ndarray, start: int, end: int) -> np.ndarray:
        """Interpolate values for a specific gap."""
        # Find valid anchors
        before_val = np.nan
        after_val = np.nan

        if start > 0:
            before_val = values[start - 1]
        if end < len(values):
            after_val = values[end] if end < len(values) else np.nan

        # Interpolate based on available anchors
        gap_size = end - start

        if not np.isnan(before_val) and not np.isnan(after_val):
            # Linear interpolation between two points
            return np.linspace(before_val, after_val, gap_size + 2)[1:-1]
        elif not np.isnan(before_val):
            # Forward fill
            return np.full(gap_size, before_val)
        elif not np.isnan(after_val):
            # Backward fill
            return np.full(gap_size, after_val)
        else:
            # No valid anchors
            return np.full(gap_size, np.nan)

    def assess_quality(self, df: pd.DataFrame) -> QualityMetrics:
        """
        Assess overall data quality.

        Args:
            df: DataFrame with pose data

        Returns:
            QualityMetrics object with assessment results
        """
        metrics = {}

        # Detection rate
        if 'frame_id' in df.columns:
            total_frames = df['frame_id'].nunique()
            frames_with_detection = df.dropna(subset=['x', 'y'])['frame_id'].nunique()
            metrics['detection_rate'] = frames_with_detection / max(total_frames, 1)
        else:
            metrics['detection_rate'] = 1.0

        # Average confidence
        if 'visibility' in df.columns:
            metrics['avg_confidence'] = df['visibility'].mean()
        else:
            metrics['avg_confidence'] = 1.0

        # Temporal consistency (based on coordinate changes)
        metrics['temporal_consistency'] = self._calculate_temporal_consistency(df)

        # Missing landmarks rate
        total_values = len(df) * 3  # x, y, z
        missing_values = df[['x', 'y', 'z']].isna().sum().sum()
        metrics['missing_landmarks_rate'] = missing_values / max(total_values, 1)

        # Jitter score (based on acceleration)
        metrics['jitter_score'] = self._calculate_jitter_score(df)

        # Frame coverage
        if 'frame_id' in df.columns:
            min_frame = df['frame_id'].min()
            max_frame = df['frame_id'].max()
            expected_frames = max_frame - min_frame + 1
            actual_frames = df['frame_id'].nunique()
            metrics['frame_coverage'] = actual_frames / max(expected_frames, 1)
        else:
            metrics['frame_coverage'] = 1.0

        return QualityMetrics(**metrics)

    def _calculate_temporal_consistency(self, df: pd.DataFrame) -> float:
        """Calculate temporal consistency based on smooth transitions."""
        if 'landmark_id' not in df.columns or 'frame_id' not in df.columns:
            return 1.0

        consistency_scores = []

        for landmark_id in df['landmark_id'].unique():
            landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')

            for col in ['x', 'y']:
                values = landmark_data[col].values
                valid_mask = ~np.isnan(values)

                if valid_mask.sum() < 3:
                    continue

                valid_values = values[valid_mask]

                # Calculate differences
                diffs = np.diff(valid_values)

                # Score based on smoothness (smaller changes = higher consistency)
                if len(diffs) > 0:
                    # Normalize by expected movement range
                    normalized_diffs = np.abs(diffs) / 0.1  # 0.1 = 10% of frame as max expected movement
                    consistency = 1.0 - np.tanh(np.mean(normalized_diffs))
                    consistency_scores.append(consistency)

        return np.mean(consistency_scores) if consistency_scores else 1.0

    def _calculate_jitter_score(self, df: pd.DataFrame) -> float:
        """Calculate jitter based on acceleration changes."""
        if 'landmark_id' not in df.columns or 'frame_id' not in df.columns:
            return 0.0

        jitter_scores = []

        for landmark_id in df['landmark_id'].unique():
            landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')

            for col in ['x', 'y']:
                values = landmark_data[col].values
                valid_mask = ~np.isnan(values)

                if valid_mask.sum() < 4:
                    continue

                valid_values = values[valid_mask]

                # Calculate acceleration (second derivative)
                velocity = np.diff(valid_values)
                acceleration = np.diff(velocity)

                if len(acceleration) > 0:
                    # Jitter is the variance in acceleration
                    jitter = np.var(acceleration)
                    jitter_scores.append(jitter)

        # Normalize jitter (lower is better)
        if jitter_scores:
            avg_jitter = np.mean(jitter_scores)
            return min(avg_jitter * 1000, 1.0)  # Scale and cap at 1.0
        return 0.0

    def process_dataframe(self, df: pd.DataFrame,
                         apply_all: bool = True) -> Tuple[pd.DataFrame, QualityMetrics]:
        """
        Apply all quality control measures to a dataframe.

        Args:
            df: Input pose data
            apply_all: Whether to apply all processing steps

        Returns:
            Tuple of processed DataFrame and quality metrics
        """
        # Assess initial quality
        initial_metrics = self.assess_quality(df)
        print(f"\n=== Initial Quality Metrics ===")
        print(f"Detection Rate: {initial_metrics.detection_rate:.2%}")
        print(f"Average Confidence: {initial_metrics.avg_confidence:.3f}")
        print(f"Temporal Consistency: {initial_metrics.temporal_consistency:.3f}")
        print(f"Missing Landmarks: {initial_metrics.missing_landmarks_rate:.2%}")
        print(f"Overall Score: {initial_metrics.get_overall_score():.3f}")
        print(f"Research Quality: {'Yes' if initial_metrics.is_research_quality() else 'No'}")

        if not apply_all:
            return df, initial_metrics

        # Apply quality control pipeline
        print("\n=== Applying Quality Control ===")

        # Step 1: Filter by confidence
        df_processed = self.filter_by_confidence(df)

        # Step 2: Interpolate missing points
        df_processed = self.interpolate_missing_points(df_processed)

        # Step 3: Apply temporal smoothing
        df_processed = self.apply_temporal_smoothing(df_processed)

        # Assess final quality
        final_metrics = self.assess_quality(df_processed)
        print(f"\n=== Final Quality Metrics ===")
        print(f"Detection Rate: {final_metrics.detection_rate:.2%}")
        print(f"Average Confidence: {final_metrics.avg_confidence:.3f}")
        print(f"Temporal Consistency: {final_metrics.temporal_consistency:.3f}")
        print(f"Missing Landmarks: {final_metrics.missing_landmarks_rate:.2%}")
        print(f"Overall Score: {final_metrics.get_overall_score():.3f}")
        print(f"Research Quality: {'Yes' if final_metrics.is_research_quality() else 'No'}")

        # Show improvement
        print(f"\n=== Quality Improvement ===")
        print(f"Overall Score: {initial_metrics.get_overall_score():.3f} → "
              f"{final_metrics.get_overall_score():.3f} "
              f"(+{(final_metrics.get_overall_score() - initial_metrics.get_overall_score()):.3f})")

        return df_processed, final_metrics


def test_quality_control():
    """Test quality control with synthetic data."""
    print("\n=== Testing Quality Control Module ===\n")

    # Create synthetic pose data with some issues
    np.random.seed(42)
    n_frames = 100
    n_landmarks = 33

    data = []
    for frame_id in range(n_frames):
        for landmark_id in range(n_landmarks):
            # Add some missing data
            if np.random.random() < 0.1:  # 10% missing
                x, y, z = np.nan, np.nan, np.nan
                visibility = 0.0
            else:
                # Add jitter
                base_x = 0.5 + 0.1 * np.sin(frame_id * 0.1)
                base_y = 0.5 + 0.1 * np.cos(frame_id * 0.1)
                x = base_x + np.random.normal(0, 0.02)  # Jitter
                y = base_y + np.random.normal(0, 0.02)
                z = 0.5 + np.random.normal(0, 0.01)
                visibility = np.random.uniform(0.3, 1.0)

            data.append({
                'frame_id': frame_id,
                'timestamp': frame_id / 30.0,
                'landmark_id': landmark_id,
                'x': x, 'y': y, 'z': z,
                'visibility': visibility
            })

    df = pd.DataFrame(data)

    # Initialize quality control
    qc = QualityControl(confidence_threshold=0.5, smoothing_window=5)

    # Process the data
    df_processed, metrics = qc.process_dataframe(df)

    # Save sample results
    print("\n=== Saving Sample Results ===")
    df_processed.head(100).to_csv('quality_control_test.csv', index=False)
    print("Sample results saved to quality_control_test.csv")


if __name__ == "__main__":
    test_quality_control()