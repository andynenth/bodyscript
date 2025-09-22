"""Data export module for pose estimation results.

Handles CSV generation, statistics calculation, and various export formats.
"""

import pandas as pd
import numpy as np
import cv2
import os
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import json

from .config import Config
from .pose_detector import PoseResult, Landmark


class DataExporter:
    """Handle data export and statistics generation."""
    
    def __init__(self, output_dir: str = "output"):
        """Initialize data exporter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_to_csv(self, 
                     pose_results: List[PoseResult], 
                     video_metadata: Dict,
                     output_path: Optional[str] = None) -> str:
        """Export pose data to CSV format.
        
        Args:
            pose_results: List of pose detection results
            video_metadata: Video metadata dictionary
            output_path: Optional output path. If None, auto-generates filename
            
        Returns:
            Path to saved CSV file
        """
        # Prepare data for DataFrame
        data_rows = []
        fps = video_metadata.get('fps', 30.0)
        
        for result in pose_results:
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
                        'confidence': landmark.visibility  # Using visibility as confidence
                    })
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"pose_data_{timestamp}.csv")
        
        # Save to CSV with proper formatting
        df.to_csv(output_path, index=False, float_format='%.6f')
        
        print(f"Exported {len(df)} pose measurements to {output_path}")
        print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")
        
        return output_path
        
    def export_to_json(self,
                      pose_results: List[PoseResult],
                      video_metadata: Dict,
                      statistics: Dict,
                      output_path: Optional[str] = None) -> str:
        """Export comprehensive data to JSON format.
        
        Args:
            pose_results: List of pose detection results
            video_metadata: Video metadata dictionary
            statistics: Calculated statistics
            output_path: Optional output path
            
        Returns:
            Path to saved JSON file
        """
        # Prepare JSON structure
        json_data = {
            "video_info": video_metadata,
            "processing_info": {
                "timestamp": datetime.now().isoformat(),
                "total_frames_processed": len(pose_results),
                "detection_settings": {
                    "model_complexity": Config.MODEL_COMPLEXITY,
                    "min_detection_confidence": Config.MIN_DETECTION_CONFIDENCE,
                    "min_tracking_confidence": Config.MIN_TRACKING_CONFIDENCE
                }
            },
            "statistics": statistics,
            "frame_data": []
        }
        
        # Add frame-by-frame data (limited to reduce file size)
        for result in pose_results[:100]:  # First 100 frames only
            if result.detected:
                frame_entry = {
                    "frame_id": result.frame_idx,
                    "timestamp": result.frame_idx / video_metadata.get('fps', 30.0),
                    "landmarks": [
                        {
                            "id": i,
                            "name": Config.get_landmark_name(i),
                            "x": lm.x,
                            "y": lm.y,
                            "z": lm.z,
                            "visibility": lm.visibility
                        }
                        for i, lm in enumerate(result.landmarks)
                    ]
                }
                json_data["frame_data"].append(frame_entry)
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"pose_analysis_{timestamp}.json")
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"Exported analysis to {output_path}")
        
        return output_path
        
    def calculate_statistics(self,
                           pose_results: List[PoseResult],
                           video_metadata: Dict) -> Dict:
        """Calculate comprehensive statistics from pose results.
        
        Args:
            pose_results: List of pose detection results
            video_metadata: Video metadata dictionary
            
        Returns:
            Dictionary of statistics
        """
        # Basic counts
        total_frames = len(pose_results)
        detected_frames = sum(1 for r in pose_results if r.detected)
        
        # Confidence statistics
        all_confidences = []
        landmark_counts = []
        
        for result in pose_results:
            if result.detected and result.landmarks:
                confidences = [lm.visibility for lm in result.landmarks]
                all_confidences.extend(confidences)
                landmark_counts.append(len([c for c in confidences if c > Config.MIN_CONFIDENCE_THRESHOLD]))
        
        # Calculate statistics
        stats = {
            'total_frames': total_frames,
            'detected_frames': detected_frames,
            'detection_rate': detected_frames / total_frames if total_frames > 0 else 0,
            'average_confidence': np.mean(all_confidences) if all_confidences else 0,
            'min_confidence': np.min(all_confidences) if all_confidences else 0,
            'max_confidence': np.max(all_confidences) if all_confidences else 0,
            'std_confidence': np.std(all_confidences) if all_confidences else 0,
            'average_landmarks_per_frame': np.mean(landmark_counts) if landmark_counts else 0,
            'processing_fps': total_frames / video_metadata.get('duration', 1.0)
        }
        
        # Add percentile statistics
        if all_confidences:
            stats['confidence_percentiles'] = {
                '25th': np.percentile(all_confidences, 25),
                '50th': np.percentile(all_confidences, 50),
                '75th': np.percentile(all_confidences, 75),
                '90th': np.percentile(all_confidences, 90)
            }
        
        return stats
        
    def create_overlay_video(self,
                           video_path: str,
                           pose_results: List[PoseResult],
                           output_path: Optional[str] = None) -> str:
        """Create video with pose skeleton overlay.
        
        Args:
            video_path: Path to original video
            pose_results: List of pose detection results
            output_path: Optional output path
            
        Returns:
            Path to output video
        """
        # Open video
        cap = cv2.VideoCapture(video_path)
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"skeleton_overlay_{timestamp}.mp4")
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_idx = 0
        while cap.isOpened() and frame_idx < len(pose_results):
            ret, frame = cap.read()
            if not ret:
                break
            
            # Draw skeleton if pose detected
            if frame_idx < len(pose_results):
                result = pose_results[frame_idx]
                if result.detected and result.landmarks:
                    frame = self._draw_skeleton(frame, result.landmarks)
                    
                    # Add status text
                    cv2.putText(frame, 
                              f"Frame: {frame_idx} | Detected: Yes",
                              (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX,
                              0.7,
                              (0, 255, 0),
                              2)
                else:
                    cv2.putText(frame,
                              f"Frame: {frame_idx} | Detected: No",
                              (10, 30),
                              cv2.FONT_HERSHEY_SIMPLEX,
                              0.7,
                              (0, 0, 255),
                              2)
            
            out.write(frame)
            frame_idx += 1
        
        # Cleanup
        cap.release()
        out.release()
        
        print(f"Created overlay video: {output_path}")
        
        return output_path
        
    def _draw_skeleton(self, 
                      image: np.ndarray, 
                      landmarks: List[Landmark]) -> np.ndarray:
        """Draw pose skeleton on image.
        
        Args:
            image: Input image
            landmarks: List of pose landmarks
            
        Returns:
            Image with skeleton drawn
        """
        h, w = image.shape[:2]
        
        # Draw connections
        for connection in Config.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                start_lm = landmarks[start_idx]
                end_lm = landmarks[end_idx]
                
                # Only draw if both landmarks are visible
                if (start_lm.visibility > Config.MIN_CONFIDENCE_THRESHOLD and
                    end_lm.visibility > Config.MIN_CONFIDENCE_THRESHOLD):
                    
                    start_point = (int(start_lm.x * w), int(start_lm.y * h))
                    end_point = (int(end_lm.x * w), int(end_lm.y * h))
                    
                    # Draw line with thickness based on confidence
                    thickness = int(Config.LINE_THICKNESS * min(start_lm.visibility, end_lm.visibility))
                    cv2.line(image, start_point, end_point, Config.OVERLAY_COLOR, thickness)
        
        # Draw landmarks
        for i, landmark in enumerate(landmarks):
            if landmark.visibility > Config.MIN_CONFIDENCE_THRESHOLD:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                
                # Draw circle with size based on confidence
                radius = int(Config.LANDMARK_RADIUS * landmark.visibility)
                cv2.circle(image, (x, y), radius, Config.LANDMARK_COLOR, -1)
                
                # Add landmark number for key points
                if i in [0, 11, 12, 15, 16, 23, 24]:  # Key landmarks
                    cv2.putText(image, str(i), (x + 5, y - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        
        return image
        
    def generate_summary_report(self,
                              statistics: Dict,
                              video_metadata: Dict,
                              output_path: Optional[str] = None) -> str:
        """Generate a text summary report.
        
        Args:
            statistics: Calculated statistics
            video_metadata: Video metadata
            output_path: Optional output path
            
        Returns:
            Path to summary report
        """
        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.output_dir, f"summary_report_{timestamp}.txt")
        
        # Create report content
        report = []
        report.append("=" * 60)
        report.append("POSE ESTIMATION ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Video information
        report.append("VIDEO INFORMATION:")
        report.append("-" * 30)
        report.append(f"Resolution: {video_metadata.get('width')}x{video_metadata.get('height')}")
        report.append(f"FPS: {video_metadata.get('fps', 0):.1f}")
        report.append(f"Duration: {video_metadata.get('duration', 0):.1f} seconds")
        report.append(f"Total frames: {video_metadata.get('total_frames', 0)}")
        
        # Detection statistics
        report.append("\nDETECTION STATISTICS:")
        report.append("-" * 30)
        report.append(f"Frames processed: {statistics['total_frames']}")
        report.append(f"Frames with pose detected: {statistics['detected_frames']}")
        report.append(f"Detection rate: {statistics['detection_rate']:.1%}")
        report.append(f"Processing speed: {statistics.get('processing_fps', 0):.1f} fps")
        
        # Confidence statistics
        report.append("\nCONFIDENCE STATISTICS:")
        report.append("-" * 30)
        report.append(f"Average confidence: {statistics['average_confidence']:.3f}")
        report.append(f"Min confidence: {statistics['min_confidence']:.3f}")
        report.append(f"Max confidence: {statistics['max_confidence']:.3f}")
        report.append(f"Std deviation: {statistics['std_confidence']:.3f}")
        
        if 'confidence_percentiles' in statistics:
            report.append("\nConfidence percentiles:")
            for percentile, value in statistics['confidence_percentiles'].items():
                report.append(f"  {percentile}: {value:.3f}")
        
        # Quality assessment
        report.append("\nQUALITY ASSESSMENT:")
        report.append("-" * 30)
        detection_rate = statistics['detection_rate']
        avg_confidence = statistics['average_confidence']
        
        if detection_rate > 0.9 and avg_confidence > 0.8:
            quality = "EXCELLENT"
        elif detection_rate > 0.8 and avg_confidence > 0.7:
            quality = "GOOD"
        elif detection_rate > 0.7 and avg_confidence > 0.6:
            quality = "FAIR"
        else:
            quality = "POOR"
            
        report.append(f"Overall quality: {quality}")
        report.append(f"Average landmarks per frame: {statistics.get('average_landmarks_per_frame', 0):.1f}")
        
        # Recommendations
        report.append("\nRECOMMENDATIONS:")
        report.append("-" * 30)
        
        if detection_rate < 0.8:
            report.append("- Consider improving video quality or lighting")
        if avg_confidence < 0.7:
            report.append("- Some landmarks have low confidence, results may be unreliable")
        if statistics.get('average_landmarks_per_frame', 0) < 25:
            report.append("- Many landmarks are missing, consider adjusting detection parameters")
            
        if quality in ["EXCELLENT", "GOOD"]:
            report.append("- Data quality is suitable for research analysis")
        
        report.append("\n" + "=" * 60)
        
        # Write report
        with open(output_path, 'w') as f:
            f.write('\n'.join(report))
        
        print(f"Generated summary report: {output_path}")
        
        return output_path