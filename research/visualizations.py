"""
Advanced Visualizations Module - Research-quality plots and visual analysis
Generates trajectory plots, heatmaps, angle graphs, and 3D visualizations
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from typing import List, Dict, Optional, Tuple
import cv2
from pathlib import Path


class ResearchVisualizer:
    """
    Creates publication-quality visualizations for movement analysis.
    """

    # MediaPipe pose connections for skeleton drawing
    POSE_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 7),  # Face
        (0, 4), (4, 5), (5, 6), (6, 8),
        (9, 10),  # Mouth
        (11, 12),  # Shoulders
        (11, 13), (13, 15),  # Left arm
        (12, 14), (14, 16),  # Right arm
        (11, 23), (12, 24),  # Torso
        (23, 24),  # Hips
        (23, 25), (25, 27),  # Left leg
        (24, 26), (26, 28),  # Right leg
        (27, 29), (29, 31),  # Left foot
        (28, 30), (30, 32),  # Right foot
    ]

    # Color scheme for different body parts
    BODY_PART_COLORS = {
        'face': '#FF6B6B',
        'torso': '#4ECDC4',
        'left_arm': '#45B7D1',
        'right_arm': '#96CEB4',
        'left_leg': '#FECA57',
        'right_leg': '#FF9FF3'
    }

    def __init__(self, output_dir: str = 'visualizations', dpi: int = 100):
        """
        Initialize the visualization system.

        Args:
            output_dir: Directory to save visualizations
            dpi: DPI for saved figures
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.dpi = dpi

        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")

    def plot_joint_trajectories(self, df: pd.DataFrame,
                              landmark_ids: Optional[List[int]] = None,
                              title: str = "Joint Trajectories") -> plt.Figure:
        """
        Plot 2D trajectories of selected joints over time.

        Args:
            df: DataFrame with pose data
            landmark_ids: List of landmark IDs to plot (default: major joints)
            title: Plot title

        Returns:
            Matplotlib figure
        """
        if landmark_ids is None:
            # Default to major joints
            landmark_ids = [0, 11, 12, 15, 16, 23, 24, 27, 28]  # Nose, shoulders, wrists, hips, ankles

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(title, fontsize=16, fontweight='bold')

        # Plot XY trajectory
        ax = axes[0, 0]
        for landmark_id in landmark_ids:
            landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')
            if not landmark_data.empty:
                x = landmark_data['x'].values
                y = landmark_data['y'].values
                label = self._get_landmark_name(landmark_id)

                # Plot with alpha for overlapping paths
                ax.plot(x, y, alpha=0.7, linewidth=1.5, label=label)

                # Mark start and end
                if not np.isnan(x[0]):
                    ax.scatter(x[0], y[0], s=50, marker='o', alpha=0.8)
                if not np.isnan(x[-1]):
                    ax.scatter(x[-1], y[-1], s=50, marker='s', alpha=0.8)

        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_title('XY Plane Trajectories')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        ax.set_aspect('equal')

        # Plot X over time
        ax = axes[0, 1]
        for landmark_id in landmark_ids:
            landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')
            if not landmark_data.empty:
                frames = landmark_data['frame_id'].values
                x = landmark_data['x'].values
                label = self._get_landmark_name(landmark_id)
                ax.plot(frames, x, alpha=0.7, linewidth=1.5, label=label)

        ax.set_xlabel('Frame')
        ax.set_ylabel('X Coordinate')
        ax.set_title('X Coordinate Over Time')
        ax.grid(True, alpha=0.3)

        # Plot Y over time
        ax = axes[1, 0]
        for landmark_id in landmark_ids:
            landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')
            if not landmark_data.empty:
                frames = landmark_data['frame_id'].values
                y = landmark_data['y'].values
                label = self._get_landmark_name(landmark_id)
                ax.plot(frames, y, alpha=0.7, linewidth=1.5, label=label)

        ax.set_xlabel('Frame')
        ax.set_ylabel('Y Coordinate')
        ax.set_title('Y Coordinate Over Time')
        ax.grid(True, alpha=0.3)

        # Plot velocity magnitude
        ax = axes[1, 1]
        for landmark_id in landmark_ids:
            landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')
            if not landmark_data.empty:
                x = landmark_data['x'].values
                y = landmark_data['y'].values

                # Calculate velocity
                vx = np.diff(x)
                vy = np.diff(y)
                velocity = np.sqrt(vx**2 + vy**2)

                frames = landmark_data['frame_id'].values[1:]
                label = self._get_landmark_name(landmark_id)
                ax.plot(frames, velocity, alpha=0.7, linewidth=1.5, label=label)

        ax.set_xlabel('Frame')
        ax.set_ylabel('Velocity')
        ax.set_title('Movement Velocity Over Time')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save figure
        output_path = self.output_dir / f"trajectories_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"✓ Trajectory plot saved to {output_path}")

        return fig

    def create_movement_heatmap(self, df: pd.DataFrame, bins: int = 50) -> plt.Figure:
        """
        Create a heatmap showing areas of most movement.

        Args:
            df: DataFrame with pose data
            bins: Number of bins for 2D histogram

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle("Movement Density Heatmaps", fontsize=16, fontweight='bold')

        # Collect all positions
        all_x = df['x'].dropna().values
        all_y = df['y'].dropna().values

        # Overall heatmap
        ax = axes[0]
        h, xedges, yedges, img = ax.hist2d(all_x, all_y, bins=bins, cmap='hot')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_title('Overall Movement Density')
        ax.set_aspect('equal')
        plt.colorbar(img, ax=ax, label='Frequency')

        # Upper body heatmap (shoulders, arms)
        ax = axes[1]
        upper_body_ids = [11, 12, 13, 14, 15, 16]  # Shoulders, elbows, wrists
        upper_df = df[df['landmark_id'].isin(upper_body_ids)]
        if not upper_df.empty:
            upper_x = upper_df['x'].dropna().values
            upper_y = upper_df['y'].dropna().values
            h, xedges, yedges, img = ax.hist2d(upper_x, upper_y, bins=bins, cmap='hot')
            ax.set_xlabel('X Coordinate')
            ax.set_ylabel('Y Coordinate')
            ax.set_title('Upper Body Movement')
            ax.set_aspect('equal')
            plt.colorbar(img, ax=ax, label='Frequency')

        # Lower body heatmap (hips, legs)
        ax = axes[2]
        lower_body_ids = [23, 24, 25, 26, 27, 28]  # Hips, knees, ankles
        lower_df = df[df['landmark_id'].isin(lower_body_ids)]
        if not lower_df.empty:
            lower_x = lower_df['x'].dropna().values
            lower_y = lower_df['y'].dropna().values
            h, xedges, yedges, img = ax.hist2d(lower_x, lower_y, bins=bins, cmap='hot')
            ax.set_xlabel('X Coordinate')
            ax.set_ylabel('Y Coordinate')
            ax.set_title('Lower Body Movement')
            ax.set_aspect('equal')
            plt.colorbar(img, ax=ax, label='Frequency')

        plt.tight_layout()

        # Save figure
        output_path = self.output_dir / f"heatmap_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"✓ Movement heatmap saved to {output_path}")

        return fig

    def plot_angle_evolution(self, angles_df: pd.DataFrame,
                           joint_names: Optional[List[str]] = None) -> plt.Figure:
        """
        Plot joint angles over time.

        Args:
            angles_df: DataFrame with joint angles from analytics module
            joint_names: List of joint names to plot

        Returns:
            Matplotlib figure
        """
        if joint_names is None:
            # Default to major joints
            joint_names = ['left_elbow', 'right_elbow', 'left_knee', 'right_knee',
                          'left_shoulder', 'right_shoulder']

        # Filter available joints
        available_joints = [j for j in joint_names if j in angles_df.columns]

        if not available_joints:
            print("No joint angle data available")
            return None

        n_joints = len(available_joints)
        fig, axes = plt.subplots(n_joints, 1, figsize=(12, 2.5 * n_joints), sharex=True)
        if n_joints == 1:
            axes = [axes]

        fig.suptitle("Joint Angle Evolution", fontsize=16, fontweight='bold')

        for idx, joint_name in enumerate(available_joints):
            ax = axes[idx]

            # Get angle data
            angles = angles_df[joint_name].values
            frames = angles_df['frame_id'].values if 'frame_id' in angles_df else np.arange(len(angles))

            # Plot raw angles
            ax.plot(frames, angles, alpha=0.5, color='gray', linewidth=0.5, label='Raw')

            # Plot smoothed angles
            valid_mask = ~np.isnan(angles)
            if valid_mask.sum() > 5:
                from scipy.ndimage import uniform_filter1d
                smoothed = uniform_filter1d(angles[valid_mask], size=5, mode='nearest')
                ax.plot(frames[valid_mask], smoothed, linewidth=2, label='Smoothed')

            # Add reference lines
            ax.axhline(y=90, color='r', linestyle='--', alpha=0.3, label='90°')
            ax.axhline(y=180, color='b', linestyle='--', alpha=0.3, label='180°')

            # Formatting
            ax.set_ylabel(f'{joint_name}\n(degrees)')
            ax.set_ylim(0, 200)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', fontsize=8)

            # Highlight specific ranges
            if 'knee' in joint_name:
                ax.axhspan(60, 120, alpha=0.1, color='green', label='Squat range')
            elif 'elbow' in joint_name:
                ax.axhspan(30, 160, alpha=0.1, color='blue', label='Normal range')

        axes[-1].set_xlabel('Frame')

        plt.tight_layout()

        # Save figure
        output_path = self.output_dir / f"angles_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"✓ Angle evolution plot saved to {output_path}")

        return fig

    def create_3d_pose_visualization(self, df: pd.DataFrame,
                                    frame_ids: Optional[List[int]] = None) -> plt.Figure:
        """
        Create 3D visualization of pose at specific frames.

        Args:
            df: DataFrame with pose data
            frame_ids: List of frame IDs to visualize (default: 5 evenly spaced)

        Returns:
            Matplotlib figure
        """
        if frame_ids is None:
            # Select 5 evenly spaced frames
            total_frames = df['frame_id'].nunique()
            frame_ids = np.linspace(0, total_frames-1, min(5, total_frames), dtype=int)

        n_frames = len(frame_ids)
        fig = plt.figure(figsize=(4 * n_frames, 6))
        fig.suptitle("3D Pose Visualization", fontsize=16, fontweight='bold')

        for idx, frame_id in enumerate(frame_ids):
            ax = fig.add_subplot(1, n_frames, idx + 1, projection='3d')

            # Get frame data
            frame_data = df[df['frame_id'] == frame_id]

            if frame_data.empty:
                continue

            # Plot landmarks
            x = frame_data['x'].values
            y = frame_data['y'].values
            z = frame_data['z'].values if 'z' in frame_data else np.zeros_like(x)

            # Plot points
            ax.scatter(x, y, z, c='red', s=30, alpha=0.8)

            # Plot connections
            for connection in self.POSE_CONNECTIONS:
                p1_data = frame_data[frame_data['landmark_id'] == connection[0]]
                p2_data = frame_data[frame_data['landmark_id'] == connection[1]]

                if not p1_data.empty and not p2_data.empty:
                    x_line = [p1_data['x'].iloc[0], p2_data['x'].iloc[0]]
                    y_line = [p1_data['y'].iloc[0], p2_data['y'].iloc[0]]
                    z_line = [p1_data['z'].iloc[0] if 'z' in p1_data else 0,
                             p2_data['z'].iloc[0] if 'z' in p2_data else 0]

                    ax.plot(x_line, y_line, z_line, 'b-', alpha=0.6, linewidth=2)

            # Set labels and limits
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title(f'Frame {frame_id}')

            # Set consistent limits
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_zlim(-0.5, 0.5)

            # Adjust viewing angle
            ax.view_init(elev=20, azim=45)

        plt.tight_layout()

        # Save figure
        output_path = self.output_dir / f"pose3d_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"✓ 3D pose visualization saved to {output_path}")

        return fig

    def create_symmetry_plot(self, symmetry_scores: Dict[str, float]) -> plt.Figure:
        """
        Create a radar plot showing movement symmetry.

        Args:
            symmetry_scores: Dictionary of symmetry scores from analytics

        Returns:
            Matplotlib figure
        """
        if not symmetry_scores:
            print("No symmetry data available")
            return None

        # Prepare data
        categories = list(symmetry_scores.keys())
        if 'overall' in categories:
            categories.remove('overall')  # Remove overall for individual plotting

        values = [symmetry_scores.get(cat, 0) for cat in categories]

        # Create radar plot
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='polar')

        # Compute angle for each axis
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values_plot = values + values[:1]  # Complete the circle
        angles += angles[:1]

        # Plot
        ax.plot(angles, values_plot, 'o-', linewidth=2, color='#FF6B6B')
        ax.fill(angles, values_plot, alpha=0.25, color='#FF6B6B')

        # Fix axis to go in the right order and start at 12 o'clock
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        # Set labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)

        # Set y limits and labels
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'])

        # Add grid
        ax.grid(True)

        # Add title
        overall_score = symmetry_scores.get('overall', np.mean(values))
        plt.title(f'Movement Symmetry Analysis\nOverall Score: {overall_score:.3f}',
                 fontsize=14, fontweight='bold', pad=20)

        # Save figure
        output_path = self.output_dir / f"symmetry_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"✓ Symmetry plot saved to {output_path}")

        return fig

    def create_quality_metrics_plot(self, metrics_dict: Dict[str, float]) -> plt.Figure:
        """
        Create bar plot of quality metrics.

        Args:
            metrics_dict: Dictionary of quality metrics

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Prepare data
        metrics = list(metrics_dict.keys())
        values = list(metrics_dict.values())

        # Create bar plot
        bars = ax.bar(metrics, values, color='skyblue', edgecolor='navy', linewidth=1.5)

        # Color bars based on value
        for bar, value in zip(bars, values):
            if value >= 0.8:
                bar.set_color('green')
            elif value >= 0.6:
                bar.set_color('yellow')
            else:
                bar.set_color('red')

        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{value:.2f}', ha='center', va='bottom')

        # Formatting
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title('Quality Metrics Assessment', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 1.1)
        ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.5, label='Good')
        ax.axhline(y=0.6, color='yellow', linestyle='--', alpha=0.5, label='Fair')
        ax.axhline(y=0.4, color='red', linestyle='--', alpha=0.5, label='Poor')

        # Rotate x labels if needed
        plt.xticks(rotation=45, ha='right')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        # Save figure
        output_path = self.output_dir / f"quality_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.png"
        fig.savefig(output_path, dpi=self.dpi, bbox_inches='tight')
        print(f"✓ Quality metrics plot saved to {output_path}")

        return fig

    def _get_landmark_name(self, landmark_id: int) -> str:
        """Get human-readable name for landmark ID."""
        landmark_names = {
            0: 'Nose', 11: 'L-Shoulder', 12: 'R-Shoulder',
            13: 'L-Elbow', 14: 'R-Elbow', 15: 'L-Wrist', 16: 'R-Wrist',
            23: 'L-Hip', 24: 'R-Hip', 25: 'L-Knee', 26: 'R-Knee',
            27: 'L-Ankle', 28: 'R-Ankle'
        }
        return landmark_names.get(landmark_id, f'Point-{landmark_id}')

    def generate_all_visualizations(self, df: pd.DataFrame,
                                  angles_df: Optional[pd.DataFrame] = None,
                                  symmetry_scores: Optional[Dict] = None,
                                  quality_metrics: Optional[Dict] = None) -> Dict[str, plt.Figure]:
        """
        Generate all available visualizations.

        Args:
            df: Pose data DataFrame
            angles_df: Joint angles DataFrame
            symmetry_scores: Symmetry analysis results
            quality_metrics: Quality assessment results

        Returns:
            Dictionary of figure objects
        """
        figures = {}

        print("\n=== Generating Research Visualizations ===")

        # Trajectory plots
        print("Creating trajectory plots...")
        figures['trajectories'] = self.plot_joint_trajectories(df)

        # Movement heatmap
        print("Creating movement heatmaps...")
        figures['heatmap'] = self.create_movement_heatmap(df)

        # 3D pose visualization
        print("Creating 3D pose visualization...")
        figures['pose3d'] = self.create_3d_pose_visualization(df)

        # Angle evolution (if available)
        if angles_df is not None:
            print("Creating angle evolution plots...")
            figures['angles'] = self.plot_angle_evolution(angles_df)

        # Symmetry plot (if available)
        if symmetry_scores:
            print("Creating symmetry analysis plot...")
            figures['symmetry'] = self.create_symmetry_plot(symmetry_scores)

        # Quality metrics (if available)
        if quality_metrics:
            print("Creating quality metrics plot...")
            figures['quality'] = self.create_quality_metrics_plot(quality_metrics)

        print(f"\n✓ Generated {len(figures)} visualizations")
        print(f"✓ All visualizations saved to {self.output_dir}/")

        return figures


def test_visualizations():
    """Test the visualization module with synthetic data."""
    print("\n=== Testing Visualizations Module ===\n")

    # Create synthetic data
    np.random.seed(42)
    n_frames = 100
    data = []

    for frame_id in range(n_frames):
        for landmark_id in range(33):
            # Create some movement pattern
            phase = frame_id * 0.1
            x = 0.5 + 0.2 * np.sin(phase + landmark_id * 0.2)
            y = 0.5 + 0.2 * np.cos(phase + landmark_id * 0.2)
            z = 0.1 * np.sin(phase * 2)

            data.append({
                'frame_id': frame_id,
                'landmark_id': landmark_id,
                'x': x + np.random.normal(0, 0.01),
                'y': y + np.random.normal(0, 0.01),
                'z': z + np.random.normal(0, 0.01)
            })

    df = pd.DataFrame(data)

    # Create sample angles data
    angles_data = []
    for frame_id in range(n_frames):
        angles_data.append({
            'frame_id': frame_id,
            'left_elbow': 90 + 30 * np.sin(frame_id * 0.1),
            'right_elbow': 90 + 30 * np.cos(frame_id * 0.1),
            'left_knee': 120 + 20 * np.sin(frame_id * 0.05),
            'right_knee': 120 + 20 * np.cos(frame_id * 0.05)
        })
    angles_df = pd.DataFrame(angles_data)

    # Sample symmetry scores
    symmetry_scores = {
        'shoulders': 0.85,
        'elbows': 0.78,
        'wrists': 0.72,
        'hips': 0.90,
        'knees': 0.88,
        'ankles': 0.75,
        'overall': 0.81
    }

    # Sample quality metrics
    quality_metrics = {
        'detection_rate': 0.92,
        'avg_confidence': 0.78,
        'temporal_consistency': 0.85,
        'completeness': 0.88,
        'smoothness': 0.73
    }

    # Initialize visualizer
    visualizer = ResearchVisualizer(output_dir='test_visualizations')

    # Generate all visualizations
    figures = visualizer.generate_all_visualizations(
        df=df,
        angles_df=angles_df,
        symmetry_scores=symmetry_scores,
        quality_metrics=quality_metrics
    )

    print(f"\n✓ Successfully generated {len(figures)} test visualizations")
    plt.show()


if __name__ == "__main__":
    test_visualizations()