"""Visualization utilities for pose data.

Provides functions for creating plots, trajectories, and visual analysis.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
import os
from datetime import datetime

from core.config import Config


class PoseVisualizer:
    """Create various visualizations for pose data."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize visualizer.
        
        Args:
            output_dir: Directory for saving visualizations
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def plot_confidence_over_time(self, 
                                 df: pd.DataFrame,
                                 save_path: Optional[str] = None) -> str:
        """Plot average confidence/visibility over time.
        
        Args:
            df: DataFrame with pose data
            save_path: Optional save path
            
        Returns:
            Path to saved plot
        """
        plt.figure(figsize=(12, 6))
        
        # Calculate average confidence per frame
        avg_conf = df.groupby('frame_id')['confidence'].mean()
        
        plt.subplot(2, 1, 1)
        plt.plot(avg_conf.index, avg_conf.values, 'b-', alpha=0.7)
        plt.fill_between(avg_conf.index, avg_conf.values, alpha=0.3)
        plt.title('Average Landmark Confidence Over Time')
        plt.xlabel('Frame')
        plt.ylabel('Confidence (0-1)')
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1)
        
        # Plot detection gaps
        plt.subplot(2, 1, 2)
        frames_with_data = df['frame_id'].unique()
        all_frames = np.arange(frames_with_data.min(), frames_with_data.max() + 1)
        detection_status = np.isin(all_frames, frames_with_data).astype(int)
        
        plt.plot(all_frames, detection_status, 'g-', linewidth=2)
        plt.fill_between(all_frames, detection_status, alpha=0.3, color='green')
        plt.title('Pose Detection Status')
        plt.xlabel('Frame')
        plt.ylabel('Detected (1) / Not Detected (0)')
        plt.ylim(-0.1, 1.1)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"confidence_plot_{timestamp}.png")
            
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return save_path
        
    def plot_landmark_trajectories(self,
                                 df: pd.DataFrame,
                                 landmark_ids: Optional[List[int]] = None,
                                 save_path: Optional[str] = None) -> str:
        """Plot trajectories of specific landmarks.
        
        Args:
            df: DataFrame with pose data
            landmark_ids: List of landmark IDs to plot (default: key landmarks)
            save_path: Optional save path
            
        Returns:
            Path to saved plot
        """
        if landmark_ids is None:
            # Default to key landmarks
            landmark_ids = [0, 11, 12, 15, 16, 23, 24]  # nose, shoulders, wrists, hips
            
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()
        
        for idx, landmark_id in enumerate(landmark_ids[:4]):
            ax = axes[idx]
            
            # Get data for this landmark
            landmark_data = df[df['landmark_id'] == landmark_id].sort_values('frame_id')
            
            if not landmark_data.empty:
                # Plot trajectory
                ax.plot(landmark_data['x'], landmark_data['y'], 'b-', alpha=0.5)
                ax.scatter(landmark_data['x'].iloc[0], landmark_data['y'].iloc[0],
                          color='green', s=100, label='Start', zorder=5)
                ax.scatter(landmark_data['x'].iloc[-1], landmark_data['y'].iloc[-1],
                          color='red', s=100, label='End', zorder=5)
                
                # Format plot
                ax.set_title(f"{Config.get_landmark_name(landmark_id)} Trajectory")
                ax.set_xlabel('X (normalized)')
                ax.set_ylabel('Y (normalized)')
                ax.invert_yaxis()  # Invert Y to match image coordinates
                ax.set_xlim(0, 1)
                ax.set_ylim(1, 0)
                ax.grid(True, alpha=0.3)
                ax.legend()
                ax.set_aspect('equal')
            else:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f"{Config.get_landmark_name(landmark_id)} - No Data")
                
        plt.suptitle('Landmark Trajectories', fontsize=16)
        plt.tight_layout()
        
        # Save plot
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"trajectories_{timestamp}.png")
            
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return save_path
        
    def plot_movement_heatmap(self,
                            df: pd.DataFrame,
                            landmark_id: int = 0,
                            bins: int = 50,
                            save_path: Optional[str] = None) -> str:
        """Create heatmap of landmark positions.
        
        Args:
            df: DataFrame with pose data
            landmark_id: Landmark ID to analyze (default: nose)
            bins: Number of bins for heatmap
            save_path: Optional save path
            
        Returns:
            Path to saved plot
        """
        plt.figure(figsize=(10, 8))
        
        # Get data for landmark
        landmark_data = df[df['landmark_id'] == landmark_id]
        
        if not landmark_data.empty:
            # Create 2D histogram
            h, xedges, yedges = np.histogram2d(
                landmark_data['x'],
                landmark_data['y'],
                bins=bins,
                range=[[0, 1], [0, 1]]
            )
            
            # Plot heatmap
            extent = [xedges[0], xedges[-1], yedges[-1], yedges[0]]
            plt.imshow(h.T, extent=extent, origin='upper', 
                      cmap='hot', interpolation='gaussian', aspect='equal')
            
            # Add trajectory overlay
            plt.plot(landmark_data['x'], landmark_data['y'], 'cyan', 
                    alpha=0.3, linewidth=1)
            
            plt.colorbar(label='Frequency')
            plt.title(f'Movement Heatmap - {Config.get_landmark_name(landmark_id)}')
            plt.xlabel('X (normalized)')
            plt.ylabel('Y (normalized)')
            
        else:
            plt.text(0.5, 0.5, 'No data available', ha='center', va='center')
            plt.xlim(0, 1)
            plt.ylim(0, 1)
            
        # Save plot
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"heatmap_{timestamp}.png")
            
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return save_path
        
    def plot_joint_angles(self,
                         angle_data: pd.DataFrame,
                         save_path: Optional[str] = None) -> str:
        """Plot joint angles over time.
        
        Args:
            angle_data: DataFrame with angle calculations
            save_path: Optional save path
            
        Returns:
            Path to saved plot
        """
        if angle_data.empty:
            print("No angle data to plot")
            return ""
            
        # Get unique angles
        angles = angle_data['angle_name'].unique()
        
        fig, axes = plt.subplots(len(angles), 1, figsize=(12, 4 * len(angles)))
        if len(angles) == 1:
            axes = [axes]
            
        for idx, angle_name in enumerate(angles):
            ax = axes[idx]
            
            # Get data for this angle
            angle_subset = angle_data[angle_data['angle_name'] == angle_name]
            
            # Plot angle over time
            ax.plot(angle_subset['frame_id'], angle_subset['angle_degrees'], 
                   'b-', linewidth=2)
            ax.fill_between(angle_subset['frame_id'], angle_subset['angle_degrees'],
                           alpha=0.3)
            
            ax.set_title(f'{angle_name.replace("_", " ").title()} Angle')
            ax.set_xlabel('Frame')
            ax.set_ylabel('Angle (degrees)')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 180)
            
        plt.suptitle('Joint Angles Over Time', fontsize=16)
        plt.tight_layout()
        
        # Save plot
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"joint_angles_{timestamp}.png")
            
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return save_path
        
    def create_summary_visualization(self,
                                   df: pd.DataFrame,
                                   statistics: Dict,
                                   save_path: Optional[str] = None) -> str:
        """Create comprehensive summary visualization.
        
        Args:
            df: DataFrame with pose data
            statistics: Calculated statistics dictionary
            save_path: Optional save path
            
        Returns:
            Path to saved plot
        """
        fig = plt.figure(figsize=(16, 10))
        
        # 1. Detection rate pie chart
        ax1 = plt.subplot(2, 3, 1)
        detection_rate = statistics.get('detection_rate', 0)
        sizes = [detection_rate, 1 - detection_rate]
        labels = ['Detected', 'Not Detected']
        colors = ['#90EE90', '#FFB6C1']
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                startangle=90)
        ax1.set_title('Overall Detection Rate')
        
        # 2. Confidence distribution histogram
        ax2 = plt.subplot(2, 3, 2)
        if 'confidence' in df.columns:
            ax2.hist(df['confidence'], bins=30, alpha=0.7, color='blue', edgecolor='black')
            ax2.axvline(statistics.get('average_confidence', 0), color='red',
                       linestyle='dashed', linewidth=2, label='Average')
            ax2.set_xlabel('Confidence')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Confidence Distribution')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
        # 3. Landmarks per frame
        ax3 = plt.subplot(2, 3, 3)
        landmarks_per_frame = df.groupby('frame_id')['landmark_id'].nunique()
        ax3.plot(landmarks_per_frame.index, landmarks_per_frame.values, 'g-', alpha=0.7)
        ax3.fill_between(landmarks_per_frame.index, landmarks_per_frame.values, alpha=0.3)
        ax3.axhline(33, color='red', linestyle='dashed', label='Max (33)')
        ax3.set_xlabel('Frame')
        ax3.set_ylabel('Number of Landmarks')
        ax3.set_title('Landmarks Detected per Frame')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Key statistics text
        ax4 = plt.subplot(2, 3, 4)
        ax4.axis('off')
        stats_text = [
            f"Total Frames: {statistics.get('total_frames', 0)}",
            f"Detected Frames: {statistics.get('detected_frames', 0)}",
            f"Detection Rate: {statistics.get('detection_rate', 0):.1%}",
            f"Avg Confidence: {statistics.get('average_confidence', 0):.3f}",
            f"Processing FPS: {statistics.get('processing_fps', 0):.1f}"
        ]
        for i, text in enumerate(stats_text):
            ax4.text(0.1, 0.8 - i*0.15, text, fontsize=12, 
                    transform=ax4.transAxes)
        ax4.set_title('Key Statistics')
        
        # 5. Sample trajectories
        ax5 = plt.subplot(2, 3, 5)
        # Plot nose trajectory as example
        nose_data = df[df['landmark_id'] == 0]
        if not nose_data.empty:
            ax5.plot(nose_data['x'], nose_data['y'], 'b-', alpha=0.5)
            ax5.scatter(nose_data['x'].iloc[0], nose_data['y'].iloc[0],
                       color='green', s=100, label='Start')
            ax5.scatter(nose_data['x'].iloc[-1], nose_data['y'].iloc[-1],
                       color='red', s=100, label='End')
            ax5.set_xlabel('X')
            ax5.set_ylabel('Y')
            ax5.set_title('Nose Trajectory (Sample)')
            ax5.invert_yaxis()
            ax5.set_xlim(0, 1)
            ax5.set_ylim(1, 0)
            ax5.legend()
            ax5.grid(True, alpha=0.3)
            
        # 6. Confidence over time
        ax6 = plt.subplot(2, 3, 6)
        avg_conf_time = df.groupby('frame_id')['confidence'].mean()
        ax6.plot(avg_conf_time.index, avg_conf_time.values, 'purple', alpha=0.7)
        ax6.fill_between(avg_conf_time.index, avg_conf_time.values, alpha=0.3)
        ax6.set_xlabel('Frame')
        ax6.set_ylabel('Average Confidence')
        ax6.set_title('Confidence Over Time')
        ax6.grid(True, alpha=0.3)
        ax6.set_ylim(0, 1)
        
        plt.suptitle('Pose Estimation Analysis Summary', fontsize=20)
        plt.tight_layout()
        
        # Save plot
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"summary_viz_{timestamp}.png")
            
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return save_path