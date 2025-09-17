"""Simple pose analyzer - main interface for pose estimation.

This is the primary class that users interact with for pose analysis.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core import VideoLoader, PoseDetector, DataExporter, Config
from utils.visualization import PoseVisualizer


class SimplePoseAnalyzer:
    """Simple pose detection and analysis tool."""
    
    def __init__(self, 
                 detection_confidence: float = Config.MIN_DETECTION_CONFIDENCE,
                 tracking_confidence: float = Config.MIN_TRACKING_CONFIDENCE,
                 output_dir: str = "output"):
        """Initialize the analyzer.
        
        Args:
            detection_confidence: Minimum confidence for detection
            tracking_confidence: Minimum confidence for tracking
            output_dir: Directory for output files
        """
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize components
        self.pose_detector = PoseDetector(
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )
        self.data_exporter = DataExporter(output_dir)
        self.visualizer = PoseVisualizer(output_dir)
        
        # Results storage
        self.results_data = []
        self.video_metadata = {}
        self.statistics = {}
        
    def process_video(self, 
                     video_path: str, 
                     show_progress: bool = True,
                     batch_size: int = Config.BATCH_SIZE) -> Dict:
        """Process a video and extract pose data.
        
        Args:
            video_path: Path to video file
            show_progress: Show progress bar
            batch_size: Number of frames to process in batch
            
        Returns:
            Dictionary with processing results
        """
        print(f"\n{'='*60}")
        print(f"Processing video: {os.path.basename(video_path)}")
        print(f"{'='*60}")
        
        # Reset data
        self.results_data = []
        self.video_metadata = {}
        self.statistics = {}
        
        try:
            # Initialize video loader
            video_loader = VideoLoader(video_path)
            video_loader.load_video()
            self.video_metadata = video_loader.get_metadata()
            
            # Display video info
            print(f"\n{video_loader.get_video_info()}")
            print(f"\nProcessing with confidence threshold: {self.detection_confidence}")
            print(f"Batch size: {batch_size} frames")
            
            # Process frames in batches
            total_frames = self.video_metadata['total_frames']
            detected_frames = 0
            
            # Progress bar
            pbar = tqdm(total=total_frames, desc="Processing frames") if show_progress else None
            
            # Process video in batches
            for start_idx, batch_frames in video_loader.extract_frames_batch(batch_size):
                # Detect poses in batch
                batch_results = self.pose_detector.detect_poses(batch_frames)
                
                # Filter by confidence
                batch_results = self.pose_detector.filter_confidence(
                    batch_results, 
                    self.detection_confidence
                )
                
                # Store results
                self.results_data.extend(batch_results)
                
                # Count detections
                detected_frames += sum(1 for r in batch_results if r.detected)
                
                # Update progress
                if pbar:
                    pbar.update(len(batch_frames))
                    
            if pbar:
                pbar.close()
                
            # Calculate statistics
            self.statistics = self.data_exporter.calculate_statistics(
                self.results_data,
                self.video_metadata
            )
            
            # Display summary
            print(f"\n{'='*60}")
            print("PROCESSING COMPLETE")
            print(f"{'='*60}")
            print(f"Total frames: {total_frames}")
            print(f"Frames with pose detected: {detected_frames}")
            print(f"Detection rate: {detected_frames/total_frames*100:.1f}%")
            print(f"Average confidence: {self.statistics.get('average_confidence', 0):.3f}")
            print(f"Processing speed: {self.statistics.get('processing_fps', 0):.1f} fps")
            
            # Clean up
            video_loader.release()
            
            return {
                'total_frames': total_frames,
                'detected_frames': detected_frames,
                'detection_rate': detected_frames / total_frames if total_frames > 0 else 0,
                'fps': self.video_metadata.get('fps', 0),
                'data_points': sum(len(r.landmarks) for r in self.results_data if r.detected),
                'statistics': self.statistics
            }
            
        except Exception as e:
            print(f"\nError processing video: {e}")
            import traceback
            traceback.print_exc()
            return {}
            
    def export_csv(self, output_path: Optional[str] = None) -> str:
        """Export results to CSV.
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to saved CSV file
        """
        if not self.results_data:
            print("No data to export!")
            return ""
            
        csv_path = self.data_exporter.export_to_csv(
            self.results_data,
            self.video_metadata,
            output_path
        )
        
        return csv_path
        
    def export_json(self, output_path: Optional[str] = None) -> str:
        """Export comprehensive results to JSON.
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to saved JSON file
        """
        if not self.results_data:
            print("No data to export!")
            return ""
            
        json_path = self.data_exporter.export_to_json(
            self.results_data,
            self.video_metadata,
            self.statistics,
            output_path
        )
        
        return json_path
        
    def create_overlay_video(self, 
                           video_path: str,
                           output_path: Optional[str] = None) -> str:
        """Create video with skeleton overlay.
        
        Args:
            video_path: Path to original video
            output_path: Optional output path
            
        Returns:
            Path to output video
        """
        if not self.results_data:
            print("No pose data available! Process video first.")
            return ""
            
        print("\nCreating overlay video...")
        overlay_path = self.data_exporter.create_overlay_video(
            video_path,
            self.results_data,
            output_path
        )
        
        return overlay_path
        
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """Generate summary report.
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to report file
        """
        if not self.statistics:
            print("No statistics available! Process video first.")
            return ""
            
        report_path = self.data_exporter.generate_summary_report(
            self.statistics,
            self.video_metadata,
            output_path
        )
        
        return report_path
        
    def create_visualizations(self, csv_path: Optional[str] = None) -> Dict[str, str]:
        """Create all visualizations.
        
        Args:
            csv_path: Optional path to CSV file (uses last export if None)
            
        Returns:
            Dictionary of visualization file paths
        """
        # Load data
        if csv_path:
            df = pd.read_csv(csv_path)
        else:
            # Convert results to DataFrame
            df = self.get_dataframe()
            
        if df.empty:
            print("No data available for visualization!")
            return {}
            
        print("\nGenerating visualizations...")
        
        viz_paths = {}
        
        # 1. Confidence over time
        viz_paths['confidence'] = self.visualizer.plot_confidence_over_time(df)
        
        # 2. Landmark trajectories
        viz_paths['trajectories'] = self.visualizer.plot_landmark_trajectories(df)
        
        # 3. Movement heatmap
        viz_paths['heatmap'] = self.visualizer.plot_movement_heatmap(df)
        
        # 4. Summary visualization
        if self.statistics:
            viz_paths['summary'] = self.visualizer.create_summary_visualization(
                df, self.statistics
            )
            
        print(f"Created {len(viz_paths)} visualizations")
        
        return viz_paths
        
    def get_dataframe(self) -> pd.DataFrame:
        """Get results as pandas DataFrame.
        
        Returns:
            DataFrame with pose data
        """
        if not self.results_data:
            return pd.DataFrame()
            
        # Convert results to rows
        data_rows = []
        fps = self.video_metadata.get('fps', 30.0)
        
        for result in self.results_data:
            if result.detected and result.landmarks:
                timestamp = result.frame_idx / fps
                
                for landmark_idx, landmark in enumerate(result.landmarks):
                    data_rows.append({
                        'frame_id': result.frame_idx,
                        'timestamp': timestamp,
                        'landmark_id': landmark_idx,
                        'landmark_name': Config.get_landmark_name(landmark_idx),
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility,
                        'confidence': landmark.visibility
                    })
                    
        return pd.DataFrame(data_rows)
        
    def get_statistics(self) -> Dict:
        """Get calculated statistics.
        
        Returns:
            Dictionary of statistics
        """
        return self.statistics.copy()
        
    def analyze_joint_angles(self) -> pd.DataFrame:
        """Calculate joint angles from pose data.
        
        Returns:
            DataFrame with angle calculations
        """
        if not self.results_data:
            return pd.DataFrame()
            
        angle_data = []
        
        for result in self.results_data:
            if result.detected and result.landmarks:
                # Calculate each defined angle
                for angle_name, (p1_idx, p2_idx, p3_idx) in Config.KEY_ANGLES.items():
                    if all(idx < len(result.landmarks) for idx in [p1_idx, p2_idx, p3_idx]):
                        p1 = result.landmarks[p1_idx]
                        p2 = result.landmarks[p2_idx]
                        p3 = result.landmarks[p3_idx]
                        
                        # Only calculate if all points are visible
                        if all(p.visibility > Config.MIN_CONFIDENCE_THRESHOLD 
                               for p in [p1, p2, p3]):
                            angle = self._calculate_angle(p1, p2, p3)
                            angle_data.append({
                                'frame_id': result.frame_idx,
                                'angle_name': angle_name,
                                'angle_degrees': angle,
                                'confidence': min(p1.visibility, p2.visibility, p3.visibility)
                            })
                            
        return pd.DataFrame(angle_data)
        
    def _calculate_angle(self, p1, p2, p3) -> float:
        """Calculate angle between three points.
        
        Args:
            p1, p2, p3: Landmark points (p2 is the vertex)
            
        Returns:
            Angle in degrees
        """
        # Create vectors
        v1 = np.array([p1.x - p2.x, p1.y - p2.y, p1.z - p2.z])
        v2 = np.array([p3.x - p2.x, p3.y - p2.y, p3.z - p2.z])
        
        # Calculate angle
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        
        return np.degrees(angle)


# Example usage
if __name__ == "__main__":
    print("SimplePoseAnalyzer - Example Usage")
    print("="*60)
    
    # Create analyzer
    analyzer = SimplePoseAnalyzer(detection_confidence=0.5)
    
    # Check if example video exists
    example_video = "data/test_videos/test1.mp4"
    
    if os.path.exists(example_video):
        # Process video
        results = analyzer.process_video(example_video)
        
        if results:
            # Export data
            csv_path = analyzer.export_csv()
            json_path = analyzer.export_json()
            
            # Generate report
            report_path = analyzer.generate_report()
            
            # Create visualizations
            viz_paths = analyzer.create_visualizations()
            
            # Create overlay video
            overlay_path = analyzer.create_overlay_video(example_video)
            
            # Display results
            print(f"\nAnalysis Complete!")
            print(f"CSV data: {csv_path}")
            print(f"JSON data: {json_path}")
            print(f"Report: {report_path}")
            print(f"Overlay video: {overlay_path}")
            print(f"Visualizations: {len(viz_paths)} files created")
    else:
        print(f"\nExample video not found: {example_video}")
        print("Please provide a video file to analyze.")
        print("\nUsage:")
        print("  analyzer = SimplePoseAnalyzer()")
        print("  results = analyzer.process_video('path/to/video.mp4')")
        print("  analyzer.export_csv('output.csv')")