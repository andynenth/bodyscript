"""
Analytics Module - Joint angles, movement patterns, and biomechanical analysis
Provides comprehensive movement analysis for research applications
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy import signal, stats
from collections import defaultdict
import warnings


class BiomechanicalAnalyzer:
    """
    Analyzes biomechanical properties from pose landmarks.
    Calculates joint angles, movement patterns, and symmetry metrics.
    """

    # Key joint definitions for angle calculations
    JOINT_DEFINITIONS = {
        # Joint name: (point1, vertex, point2)
        'left_elbow': (11, 13, 15),  # shoulder-elbow-wrist
        'right_elbow': (12, 14, 16),
        'left_shoulder': (13, 11, 23),  # elbow-shoulder-hip
        'right_shoulder': (14, 12, 24),
        'left_hip': (11, 23, 25),  # shoulder-hip-knee
        'right_hip': (12, 24, 26),
        'left_knee': (23, 25, 27),  # hip-knee-ankle
        'right_knee': (24, 26, 28),
        'left_ankle': (25, 27, 31),  # knee-ankle-foot
        'right_ankle': (26, 28, 32),
        # Spine angles
        'neck_flexion': (0, 11, 12),  # nose-left_shoulder-right_shoulder (approximation)
        'trunk_flexion': (11, 23, 25),  # shoulder-hip-knee
        # Additional angles for detailed analysis
        'left_wrist': (13, 15, 19),  # elbow-wrist-index
        'right_wrist': (14, 16, 20),
    }

    # Movement pattern definitions
    MOVEMENT_PATTERNS = {
        'walking': {
            'landmarks': [23, 24, 25, 26, 27, 28],  # hips, knees, ankles
            'frequency_range': (0.5, 2.0),  # Hz
            'symmetry_threshold': 0.7
        },
        'arm_swing': {
            'landmarks': [11, 12, 13, 14, 15, 16],  # shoulders, elbows, wrists
            'frequency_range': (0.3, 3.0),  # Hz
            'symmetry_threshold': 0.6
        },
        'squat': {
            'landmarks': [23, 24, 25, 26],  # hips and knees
            'angle_range': (70, 120),  # degrees
            'duration_range': (1.0, 5.0)  # seconds
        },
        'reach': {
            'landmarks': [15, 16],  # wrists
            'velocity_threshold': 0.3,  # normalized units/second
            'distance_threshold': 0.2  # normalized units
        }
    }

    def __init__(self, fps: float = 30.0):
        """
        Initialize the biomechanical analyzer.

        Args:
            fps: Frames per second of the video
        """
        self.fps = fps
        self.angles_history = defaultdict(list)
        self.patterns_detected = []

    def calculate_angle(self, point1: np.ndarray, vertex: np.ndarray,
                       point2: np.ndarray) -> float:
        """
        Calculate angle at vertex between two vectors.

        Args:
            point1: First point coordinates (x, y, z)
            vertex: Vertex point coordinates
            point2: Second point coordinates

        Returns:
            Angle in degrees (0-180)
        """
        # Create vectors
        v1 = point1 - vertex
        v2 = point2 - vertex

        # Calculate angle using dot product
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

        # Clamp to avoid numerical errors
        cos_angle = np.clip(cos_angle, -1.0, 1.0)

        # Convert to degrees
        angle = np.degrees(np.arccos(cos_angle))

        return angle

    def calculate_joint_angles(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all defined joint angles from pose data.

        Args:
            df: DataFrame with pose landmarks

        Returns:
            DataFrame with joint angles
        """
        angles_data = []

        # Group by frame
        for frame_id in df['frame_id'].unique():
            frame_data = df[df['frame_id'] == frame_id]
            timestamp = frame_data['timestamp'].iloc[0] if 'timestamp' in frame_data.columns else frame_id / self.fps

            angles_row = {
                'frame_id': frame_id,
                'timestamp': timestamp
            }

            # Calculate each defined joint angle
            for joint_name, (p1_idx, vertex_idx, p2_idx) in self.JOINT_DEFINITIONS.items():
                # Get landmark positions
                p1 = self._get_landmark_position(frame_data, p1_idx)
                vertex = self._get_landmark_position(frame_data, vertex_idx)
                p2 = self._get_landmark_position(frame_data, p2_idx)

                if p1 is not None and vertex is not None and p2 is not None:
                    angle = self.calculate_angle(p1, vertex, p2)
                    angles_row[joint_name] = angle
                    self.angles_history[joint_name].append(angle)
                else:
                    angles_row[joint_name] = np.nan

            angles_data.append(angles_row)

        return pd.DataFrame(angles_data)

    def _get_landmark_position(self, frame_data: pd.DataFrame,
                              landmark_idx: int) -> Optional[np.ndarray]:
        """Extract 3D position of a landmark."""
        landmark_data = frame_data[frame_data['landmark_id'] == landmark_idx]

        if landmark_data.empty:
            return None

        x = landmark_data['x'].iloc[0]
        y = landmark_data['y'].iloc[0]
        z = landmark_data['z'].iloc[0] if 'z' in landmark_data.columns else 0

        if pd.isna(x) or pd.isna(y):
            return None

        return np.array([x, y, z])

    def detect_movement_patterns(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Detect predefined movement patterns in the pose data.

        Args:
            df: DataFrame with pose landmarks

        Returns:
            Dictionary of detected patterns with details
        """
        patterns = {}

        # Detect walking pattern
        walking_info = self._detect_walking(df)
        if walking_info['detected']:
            patterns['walking'] = walking_info

        # Detect arm swing
        arm_swing_info = self._detect_arm_swing(df)
        if arm_swing_info['detected']:
            patterns['arm_swing'] = arm_swing_info

        # Detect squats
        squat_info = self._detect_squats(df)
        if squat_info['detected']:
            patterns['squats'] = squat_info

        # Detect reaching movements
        reach_info = self._detect_reaching(df)
        if reach_info['detected']:
            patterns['reaching'] = reach_info

        # Detect repetitive patterns
        repetitive_info = self._detect_repetitive_movements(df)
        if repetitive_info['patterns']:
            patterns['repetitive'] = repetitive_info

        return patterns

    def _detect_walking(self, df: pd.DataFrame) -> Dict:
        """Detect walking pattern based on leg movement periodicity."""
        pattern_info = {
            'detected': False,
            'frequency': 0.0,
            'step_count': 0,
            'cadence': 0.0,
            'symmetry': 0.0
        }

        # Get hip and knee landmarks
        hip_knee_landmarks = [23, 24, 25, 26]  # Left/right hip and knee

        # Extract y-coordinates (vertical movement)
        movement_signals = []
        for landmark_id in hip_knee_landmarks:
            landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')
            if not landmark_data.empty:
                y_values = landmark_data['y'].values
                if not np.all(np.isnan(y_values)):
                    movement_signals.append(y_values)

        if len(movement_signals) < 2:
            return pattern_info

        # Analyze periodicity using FFT
        for signal in movement_signals:
            valid_mask = ~np.isnan(signal)
            if valid_mask.sum() < 30:  # Need at least 1 second of data
                continue

            valid_signal = signal[valid_mask]

            # Apply FFT
            fft = np.fft.fft(valid_signal)
            frequencies = np.fft.fftfreq(len(valid_signal), 1/self.fps)

            # Find dominant frequency in walking range
            walking_range = (0.5, 2.0)  # 0.5-2.0 Hz typical walking
            freq_mask = (frequencies > walking_range[0]) & (frequencies < walking_range[1])

            if freq_mask.any():
                power = np.abs(fft[freq_mask])**2
                peak_idx = np.argmax(power)
                peak_freq = frequencies[freq_mask][peak_idx]

                # Check if peak is significant
                if power[peak_idx] > np.mean(power) * 2:
                    pattern_info['detected'] = True
                    pattern_info['frequency'] = peak_freq
                    pattern_info['step_count'] = int(peak_freq * len(valid_signal) / self.fps)
                    pattern_info['cadence'] = peak_freq * 60  # steps per minute
                    break

        # Calculate symmetry if walking detected
        if pattern_info['detected'] and len(movement_signals) >= 4:
            left_signal = np.nanmean([movement_signals[0], movement_signals[2]], axis=0)  # Left hip/knee
            right_signal = np.nanmean([movement_signals[1], movement_signals[3]], axis=0)  # Right hip/knee

            valid_mask = ~(np.isnan(left_signal) | np.isnan(right_signal))
            if valid_mask.sum() > 0:
                correlation = np.corrcoef(left_signal[valid_mask], right_signal[valid_mask])[0, 1]
                pattern_info['symmetry'] = max(0, correlation)

        return pattern_info

    def _detect_arm_swing(self, df: pd.DataFrame) -> Dict:
        """Detect arm swinging patterns."""
        pattern_info = {
            'detected': False,
            'frequency': 0.0,
            'amplitude': 0.0,
            'symmetry': 0.0
        }

        # Get wrist landmarks for arm swing detection
        left_wrist = df[df['landmark_id'] == 15].sort_values('frame_id')
        right_wrist = df[df['landmark_id'] == 16].sort_values('frame_id')

        if left_wrist.empty or right_wrist.empty:
            return pattern_info

        # Calculate wrist displacement
        for wrist_data in [left_wrist, right_wrist]:
            x_values = wrist_data['x'].values
            valid_mask = ~np.isnan(x_values)

            if valid_mask.sum() < 30:  # Need sufficient data
                continue

            valid_signal = x_values[valid_mask]

            # Detect oscillation
            velocity = np.diff(valid_signal)
            zero_crossings = np.where(np.diff(np.sign(velocity)))[0]

            if len(zero_crossings) > 2:
                # Calculate period from zero crossings
                periods = np.diff(zero_crossings)
                avg_period = np.mean(periods)
                frequency = self.fps / (2 * avg_period)  # Two zero crossings per cycle

                if 0.3 <= frequency <= 3.0:  # Reasonable arm swing frequency
                    pattern_info['detected'] = True
                    pattern_info['frequency'] = frequency
                    pattern_info['amplitude'] = np.std(valid_signal)
                    break

        # Calculate symmetry between arms
        if pattern_info['detected']:
            left_x = left_wrist['x'].values
            right_x = right_wrist['x'].values
            valid_mask = ~(np.isnan(left_x) | np.isnan(right_x))

            if valid_mask.sum() > 0:
                correlation = np.corrcoef(left_x[valid_mask], right_x[valid_mask])[0, 1]
                pattern_info['symmetry'] = abs(correlation)  # Anti-phase for walking

        return pattern_info

    def _detect_squats(self, df: pd.DataFrame) -> Dict:
        """Detect squat movements based on hip and knee angles."""
        pattern_info = {
            'detected': False,
            'count': 0,
            'depths': [],
            'durations': []
        }

        # Calculate hip and knee angles first
        angles_df = self.calculate_joint_angles(df)

        # Focus on knee angles
        knee_angles = []
        for knee in ['left_knee', 'right_knee']:
            if knee in angles_df.columns:
                angles = angles_df[knee].values
                valid_mask = ~np.isnan(angles)
                if valid_mask.sum() > 0:
                    knee_angles.append(angles)

        if not knee_angles:
            return pattern_info

        # Average knee angles
        avg_knee_angle = np.nanmean(knee_angles, axis=0)

        # Detect squats as significant knee flexion events
        squat_threshold = 120  # degrees - typical squat knee angle
        in_squat = avg_knee_angle < squat_threshold

        # Find squat events
        squat_starts = []
        squat_ends = []

        for i in range(1, len(in_squat)):
            if in_squat[i] and not in_squat[i-1]:
                squat_starts.append(i)
            elif not in_squat[i] and in_squat[i-1]:
                squat_ends.append(i)

        # Pair starts and ends
        squats = []
        for start in squat_starts:
            end = next((e for e in squat_ends if e > start), None)
            if end:
                duration = (end - start) / self.fps
                if 0.5 <= duration <= 10.0:  # Reasonable squat duration
                    depth = np.nanmin(avg_knee_angle[start:end])
                    squats.append({
                        'start_frame': start,
                        'end_frame': end,
                        'duration': duration,
                        'depth': depth
                    })

        if squats:
            pattern_info['detected'] = True
            pattern_info['count'] = len(squats)
            pattern_info['depths'] = [s['depth'] for s in squats]
            pattern_info['durations'] = [s['duration'] for s in squats]

        return pattern_info

    def _detect_reaching(self, df: pd.DataFrame) -> Dict:
        """Detect reaching movements."""
        pattern_info = {
            'detected': False,
            'count': 0,
            'directions': [],
            'distances': []
        }

        # Track wrist movements for reaching
        for wrist_id in [15, 16]:  # Left and right wrist
            wrist_data = df[df['landmark_id'] == wrist_id].sort_values('frame_id')

            if wrist_data.empty:
                continue

            x_values = wrist_data['x'].values
            y_values = wrist_data['y'].values

            valid_mask = ~(np.isnan(x_values) | np.isnan(y_values))

            if valid_mask.sum() < 10:
                continue

            valid_x = x_values[valid_mask]
            valid_y = y_values[valid_mask]

            # Calculate velocity
            vx = np.diff(valid_x) * self.fps
            vy = np.diff(valid_y) * self.fps
            speed = np.sqrt(vx**2 + vy**2)

            # Detect reach events (high velocity movements)
            reach_threshold = 0.3  # normalized units/second
            reach_events = speed > reach_threshold

            # Find reach segments
            reach_starts = []
            reach_ends = []

            for i in range(1, len(reach_events)):
                if reach_events[i] and not reach_events[i-1]:
                    reach_starts.append(i)
                elif not reach_events[i] and reach_events[i-1]:
                    reach_ends.append(i)

            # Analyze each reach
            for start in reach_starts:
                end = next((e for e in reach_ends if e > start), None)
                if end and (end - start) > 3:  # Minimum 3 frames
                    # Calculate reach properties
                    dx = valid_x[end] - valid_x[start]
                    dy = valid_y[end] - valid_y[start]
                    distance = np.sqrt(dx**2 + dy**2)
                    direction = np.degrees(np.arctan2(dy, dx))

                    if distance > 0.1:  # Minimum reach distance
                        pattern_info['detected'] = True
                        pattern_info['count'] += 1
                        pattern_info['directions'].append(direction)
                        pattern_info['distances'].append(distance)

        return pattern_info

    def _detect_repetitive_movements(self, df: pd.DataFrame) -> Dict:
        """Detect any repetitive movement patterns."""
        pattern_info = {
            'patterns': [],
            'frequencies': [],
            'landmarks': []
        }

        # Analyze each landmark for repetitive patterns
        for landmark_id in df['landmark_id'].unique():
            landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')

            if landmark_data.empty:
                continue

            # Combine x and y for pattern detection
            x_values = landmark_data['x'].values
            y_values = landmark_data['y'].values

            valid_mask = ~(np.isnan(x_values) | np.isnan(y_values))

            if valid_mask.sum() < 60:  # Need at least 2 seconds
                continue

            valid_x = x_values[valid_mask]
            valid_y = y_values[valid_mask]

            # Calculate movement magnitude
            movement = np.sqrt(valid_x**2 + valid_y**2)

            # Detrend to focus on oscillations
            detrended = signal.detrend(movement)

            # Autocorrelation to find periodicity
            autocorr = np.correlate(detrended, detrended, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            autocorr = autocorr / autocorr[0]  # Normalize

            # Find peaks in autocorrelation
            peaks, properties = signal.find_peaks(autocorr, height=0.3, distance=self.fps//2)

            if len(peaks) > 0:
                # Get the first significant peak (period)
                period_frames = peaks[0]
                frequency = self.fps / period_frames

                if 0.1 <= frequency <= 5.0:  # Reasonable frequency range
                    pattern_info['patterns'].append(f"landmark_{landmark_id}")
                    pattern_info['frequencies'].append(frequency)
                    pattern_info['landmarks'].append(landmark_id)

        return pattern_info

    def calculate_symmetry(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate movement symmetry between left and right sides.

        Args:
            df: DataFrame with pose landmarks

        Returns:
            Dictionary of symmetry scores for different body parts
        """
        symmetry_scores = {}

        # Define paired landmarks (left, right)
        landmark_pairs = {
            'shoulders': (11, 12),
            'elbows': (13, 14),
            'wrists': (15, 16),
            'hips': (23, 24),
            'knees': (25, 26),
            'ankles': (27, 28)
        }

        for body_part, (left_id, right_id) in landmark_pairs.items():
            left_data = df[df['landmark_id'] == left_id].sort_values('frame_id')
            right_data = df[df['landmark_id'] == right_id].sort_values('frame_id')

            if left_data.empty or right_data.empty:
                continue

            # Merge on frame_id
            merged = pd.merge(left_data[['frame_id', 'x', 'y']],
                            right_data[['frame_id', 'x', 'y']],
                            on='frame_id', suffixes=('_left', '_right'))

            if len(merged) < 10:
                continue

            # Calculate correlation for x and y movements
            x_corr = merged['x_left'].corr(merged['x_right'])
            y_corr = merged['y_left'].corr(merged['y_right'])

            # Average correlation as symmetry score
            symmetry = (abs(x_corr) + abs(y_corr)) / 2
            symmetry_scores[body_part] = min(max(symmetry, 0), 1)

        # Calculate overall symmetry
        if symmetry_scores:
            symmetry_scores['overall'] = np.mean(list(symmetry_scores.values()))

        return symmetry_scores

    def generate_movement_report(self, df: pd.DataFrame) -> Dict:
        """
        Generate comprehensive movement analysis report.

        Args:
            df: DataFrame with pose landmarks

        Returns:
            Dictionary containing full analysis results
        """
        report = {
            'joint_angles': {},
            'movement_patterns': {},
            'symmetry': {},
            'statistics': {}
        }

        # Calculate joint angles
        print("Calculating joint angles...")
        angles_df = self.calculate_joint_angles(df)
        report['joint_angles'] = {
            'data': angles_df,
            'ranges': {},
            'means': {}
        }

        for joint in self.JOINT_DEFINITIONS.keys():
            if joint in angles_df.columns:
                angles = angles_df[joint].dropna()
                if len(angles) > 0:
                    report['joint_angles']['ranges'][joint] = (angles.min(), angles.max())
                    report['joint_angles']['means'][joint] = angles.mean()

        # Detect movement patterns
        print("Detecting movement patterns...")
        report['movement_patterns'] = self.detect_movement_patterns(df)

        # Calculate symmetry
        print("Calculating symmetry...")
        report['symmetry'] = self.calculate_symmetry(df)

        # Generate statistics
        print("Generating statistics...")
        report['statistics'] = {
            'total_frames': df['frame_id'].nunique(),
            'duration_seconds': df['frame_id'].nunique() / self.fps,
            'detected_patterns': list(report['movement_patterns'].keys()),
            'avg_symmetry': report['symmetry'].get('overall', 0)
        }

        # Add angle statistics
        if self.angles_history:
            for joint_name, angles in self.angles_history.items():
                if angles:
                    report['statistics'][f'{joint_name}_range'] = (min(angles), max(angles))
                    report['statistics'][f'{joint_name}_mean'] = np.mean(angles)
                    report['statistics'][f'{joint_name}_std'] = np.std(angles)

        return report


def test_analytics():
    """Test the analytics module with synthetic data."""
    print("\n=== Testing Analytics Module ===\n")

    # Create synthetic walking data
    np.random.seed(42)
    n_frames = 300  # 10 seconds at 30 fps
    fps = 30

    data = []

    for frame_id in range(n_frames):
        timestamp = frame_id / fps

        # Simulate walking pattern
        walking_phase = frame_id * 0.1  # Phase for walking cycle

        # Generate pose landmarks with walking motion
        for landmark_id in range(33):
            # Add walking motion to leg landmarks
            if landmark_id in [23, 24, 25, 26, 27, 28]:  # Leg landmarks
                # Oscillating motion for walking
                x = 0.5 + 0.1 * np.sin(walking_phase + landmark_id * 0.5)
                y = 0.5 + 0.05 * np.cos(walking_phase * 2 + landmark_id * 0.5)
            else:
                # Relatively stable upper body
                x = 0.5 + np.random.normal(0, 0.01)
                y = 0.3 + np.random.normal(0, 0.01)

            z = 0.5 + np.random.normal(0, 0.01)
            visibility = 0.9 + np.random.normal(0, 0.05)

            data.append({
                'frame_id': frame_id,
                'timestamp': timestamp,
                'landmark_id': landmark_id,
                'x': x, 'y': y, 'z': z,
                'visibility': min(max(visibility, 0), 1)
            })

    df = pd.DataFrame(data)

    # Initialize analyzer
    analyzer = BiomechanicalAnalyzer(fps=fps)

    # Generate full report
    print("Generating movement analysis report...")
    report = analyzer.generate_movement_report(df)

    # Print results
    print("\n=== Movement Analysis Results ===")

    print("\n1. Joint Angles:")
    for joint, mean_angle in report['joint_angles']['means'].items():
        range_min, range_max = report['joint_angles']['ranges'][joint]
        print(f"  {joint}: mean={mean_angle:.1f}°, range=({range_min:.1f}°-{range_max:.1f}°)")

    print("\n2. Detected Movement Patterns:")
    for pattern_name, pattern_info in report['movement_patterns'].items():
        print(f"  {pattern_name}:")
        for key, value in pattern_info.items():
            if isinstance(value, float):
                print(f"    - {key}: {value:.3f}")
            else:
                print(f"    - {key}: {value}")

    print("\n3. Movement Symmetry:")
    for body_part, score in report['symmetry'].items():
        print(f"  {body_part}: {score:.3f}")

    print("\n4. Overall Statistics:")
    print(f"  Duration: {report['statistics']['duration_seconds']:.1f} seconds")
    print(f"  Total frames: {report['statistics']['total_frames']}")
    print(f"  Detected patterns: {', '.join(report['statistics']['detected_patterns'])}")
    print(f"  Average symmetry: {report['statistics']['avg_symmetry']:.3f}")

    # Save angle data
    angles_df = report['joint_angles']['data']
    angles_df.to_csv('joint_angles_test.csv', index=False)
    print("\n✓ Joint angles saved to joint_angles_test.csv")


if __name__ == "__main__":
    test_analytics()