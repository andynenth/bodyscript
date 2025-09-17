"""Simple example of processing a video file."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_pose_analyzer import SimplePoseAnalyzer


def process_video_example():
    """Example of processing a video with SimplePoseAnalyzer."""
    
    # Get video path from command line or use default
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Try to find a test video
        possible_paths = [
            "data/test_videos/test1.mp4",
            "../data/test_videos/test1.mp4",
            "test_video.mp4",
            "sample.mp4"
        ]
        
        video_path = None
        for path in possible_paths:
            if os.path.exists(path):
                video_path = path
                break
                
        if not video_path:
            print("No video file specified!")
            print(f"Usage: python {sys.argv[0]} <video_path>")
            print("\nExample:")
            print(f"  python {sys.argv[0]} my_video.mp4")
            return
            
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return
        
    print(f"Processing video: {video_path}")
    print("=" * 60)
    
    # Create analyzer with custom confidence
    analyzer = SimplePoseAnalyzer(
        detection_confidence=0.5,  # Adjust this for your needs
        output_dir="output"
    )
    
    # Process the video
    results = analyzer.process_video(video_path, show_progress=True)
    
    if results:
        print("\n" + "=" * 60)
        print("EXPORTING RESULTS")
        print("=" * 60)
        
        # Export to CSV
        csv_path = analyzer.export_csv()
        print(f"✅ CSV data saved to: {csv_path}")
        
        # Export to JSON
        json_path = analyzer.export_json()
        print(f"✅ JSON data saved to: {json_path}")
        
        # Generate text report
        report_path = analyzer.generate_report()
        print(f"✅ Summary report saved to: {report_path}")
        
        # Create visualizations
        print("\nGenerating visualizations...")
        viz_paths = analyzer.create_visualizations()
        for viz_type, path in viz_paths.items():
            print(f"✅ {viz_type.capitalize()} visualization: {path}")
            
        # Create overlay video (optional - can be slow)
        user_input = input("\nCreate skeleton overlay video? (y/n): ")
        if user_input.lower() == 'y':
            overlay_path = analyzer.create_overlay_video(video_path)
            print(f"✅ Overlay video saved to: {overlay_path}")
            
        # Calculate joint angles
        print("\nCalculating joint angles...")
        angles_df = analyzer.analyze_joint_angles()
        if not angles_df.empty:
            angles_path = os.path.join(analyzer.output_dir, "joint_angles.csv")
            angles_df.to_csv(angles_path, index=False)
            print(f"✅ Joint angles saved to: {angles_path}")
            
            # Show sample
            print("\nSample angle data:")
            print(angles_df.head())
            
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE!")
        print("=" * 60)
        print(f"All results saved to: {analyzer.output_dir}/")
        
        # Display some key statistics
        stats = analyzer.get_statistics()
        print("\nKey Statistics:")
        print(f"  Detection rate: {stats.get('detection_rate', 0):.1%}")
        print(f"  Average confidence: {stats.get('average_confidence', 0):.3f}")
        print(f"  Processing speed: {stats.get('processing_fps', 0):.1f} fps")
        
    else:
        print("\n❌ Processing failed!")


if __name__ == "__main__":
    process_video_example()