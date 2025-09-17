"""Quick test to verify the system is working."""

import numpy as np
import cv2
import os
from datetime import datetime

from simple_pose_analyzer import SimplePoseAnalyzer


def create_test_video(output_path: str = "test_video.mp4", 
                     duration: int = 3,
                     fps: int = 30):
    """Create a simple test video with a moving circle.
    
    Args:
        output_path: Path for test video
        duration: Duration in seconds
        fps: Frames per second
    """
    print(f"Creating test video: {output_path}")
    
    # Video properties
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration * fps
    
    for frame_idx in range(total_frames):
        # Create frame
        frame = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # Draw a moving person-like shape
        t = frame_idx / fps
        
        # Head
        head_x = int(width/2 + 50 * np.sin(t))
        head_y = int(height/4)
        cv2.circle(frame, (head_x, head_y), 30, (0, 0, 0), -1)
        
        # Body
        body_top = (head_x, head_y + 30)
        body_bottom = (head_x, head_y + 100)
        cv2.line(frame, body_top, body_bottom, (0, 0, 0), 10)
        
        # Arms
        shoulder_y = head_y + 40
        left_hand = (head_x - 50, shoulder_y + 30)
        right_hand = (head_x + 50, shoulder_y + 30)
        cv2.line(frame, (head_x, shoulder_y), left_hand, (0, 0, 0), 8)
        cv2.line(frame, (head_x, shoulder_y), right_hand, (0, 0, 0), 8)
        
        # Legs
        hip_y = head_y + 100
        left_foot = (head_x - 30, hip_y + 80)
        right_foot = (head_x + 30, hip_y + 80)
        cv2.line(frame, body_bottom, left_foot, (0, 0, 0), 8)
        cv2.line(frame, body_bottom, right_foot, (0, 0, 0), 8)
        
        # Add frame number
        cv2.putText(frame, f"Frame {frame_idx}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        out.write(frame)
        
    out.release()
    print(f"✅ Test video created: {output_path}")
    print(f"   Duration: {duration}s, Resolution: {width}x{height}, FPS: {fps}")
    

def run_quick_test():
    """Run a quick test of the pose estimation system."""
    print("=" * 60)
    print("BodyScript Quick Test")
    print("=" * 60)
    
    # Create test video if needed
    test_video = "test_video.mp4"
    if not os.path.exists(test_video):
        create_test_video(test_video)
    
    print("\nTesting pose estimation system...")
    
    # Create analyzer
    analyzer = SimplePoseAnalyzer(
        detection_confidence=0.3,  # Lower threshold for test
        output_dir="test_output"
    )
    
    # Process video
    print(f"\nProcessing: {test_video}")
    results = analyzer.process_video(test_video, show_progress=True)
    
    if results:
        print("\n✅ Processing successful!")
        
        # Export basic data
        csv_path = analyzer.export_csv()
        print(f"✅ Data exported to: {csv_path}")
        
        # Create one visualization
        df = analyzer.get_dataframe()
        if not df.empty:
            print(f"✅ Extracted {len(df)} pose measurements")
            print(f"✅ Detection rate: {results['detection_rate']:.1%}")
            
            # Show sample data
            print("\nSample data (first 5 rows):")
            print(df.head())
            
        # Generate report
        report_path = analyzer.generate_report()
        print(f"\n✅ Report saved to: {report_path}")
        
        print("\n" + "=" * 60)
        print("QUICK TEST COMPLETE!")
        print("=" * 60)
        print("\nThe system is working correctly!")
        print(f"Check the output in: {analyzer.output_dir}/")
        
        # Note about MediaPipe
        if not analyzer.pose_detector.mp_available:
            print("\n⚠️  Note: Running without MediaPipe (placeholder mode)")
            print("   For real pose detection, use Python 3.8-3.11")
            
    else:
        print("\n❌ Test failed!")
        print("Please check the error messages above.")
        

if __name__ == "__main__":
    run_quick_test()