"""Example of batch processing multiple videos."""

import sys
import os
import glob
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simple_pose_analyzer import SimplePoseAnalyzer


def batch_process_videos(video_folder: str, output_base_dir: str = "batch_output"):
    """Process multiple videos in a folder.
    
    Args:
        video_folder: Folder containing video files
        output_base_dir: Base directory for outputs
    """
    # Find all video files
    video_patterns = ['*.mp4', '*.avi', '*.mov', '*.wmv']
    video_files = []
    
    for pattern in video_patterns:
        video_files.extend(glob.glob(os.path.join(video_folder, pattern)))
        
    if not video_files:
        print(f"No video files found in: {video_folder}")
        return
        
    print(f"Found {len(video_files)} video(s) to process")
    print("=" * 60)
    
    # Create timestamp for this batch
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_output_dir = os.path.join(output_base_dir, f"batch_{batch_timestamp}")
    
    # Summary statistics
    summary_data = []
    
    # Process each video
    for idx, video_path in enumerate(video_files, 1):
        video_name = os.path.basename(video_path)
        print(f"\n[{idx}/{len(video_files)}] Processing: {video_name}")
        print("-" * 60)
        
        # Create output directory for this video
        video_output_dir = os.path.join(batch_output_dir, 
                                       os.path.splitext(video_name)[0])
        
        # Create analyzer
        analyzer = SimplePoseAnalyzer(
            detection_confidence=0.5,
            output_dir=video_output_dir
        )
        
        try:
            # Process video
            results = analyzer.process_video(video_path, show_progress=True)
            
            if results:
                # Export results
                csv_path = analyzer.export_csv()
                json_path = analyzer.export_json()
                report_path = analyzer.generate_report()
                
                # Create visualizations
                viz_paths = analyzer.create_visualizations()
                
                # Get statistics
                stats = analyzer.get_statistics()
                
                # Add to summary
                summary_data.append({
                    'video': video_name,
                    'status': 'Success',
                    'total_frames': results['total_frames'],
                    'detected_frames': results['detected_frames'],
                    'detection_rate': f"{results['detection_rate']:.1%}",
                    'avg_confidence': f"{stats.get('average_confidence', 0):.3f}",
                    'csv_file': os.path.basename(csv_path),
                    'output_dir': video_output_dir
                })
                
                print(f"✅ Successfully processed: {video_name}")
                
            else:
                summary_data.append({
                    'video': video_name,
                    'status': 'Failed',
                    'error': 'Processing failed'
                })
                print(f"❌ Failed to process: {video_name}")
                
        except Exception as e:
            summary_data.append({
                'video': video_name,
                'status': 'Error',
                'error': str(e)
            })
            print(f"❌ Error processing {video_name}: {e}")
            
    # Create batch summary
    print("\n" + "=" * 60)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 60)
    
    # Save summary report
    summary_path = os.path.join(batch_output_dir, "batch_summary.txt")
    with open(summary_path, 'w') as f:
        f.write(f"Batch Processing Summary\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'=' * 60}\n\n")
        
        # Summary statistics
        successful = sum(1 for item in summary_data if item['status'] == 'Success')
        f.write(f"Total videos: {len(video_files)}\n")
        f.write(f"Successful: {successful}\n")
        f.write(f"Failed: {len(video_files) - successful}\n\n")
        
        # Detailed results
        f.write("Detailed Results:\n")
        f.write("-" * 60 + "\n")
        
        for item in summary_data:
            f.write(f"\nVideo: {item['video']}\n")
            f.write(f"Status: {item['status']}\n")
            
            if item['status'] == 'Success':
                f.write(f"  Total frames: {item['total_frames']}\n")
                f.write(f"  Detected frames: {item['detected_frames']}\n")
                f.write(f"  Detection rate: {item['detection_rate']}\n")
                f.write(f"  Avg confidence: {item['avg_confidence']}\n")
                f.write(f"  Output: {item['output_dir']}\n")
            else:
                f.write(f"  Error: {item.get('error', 'Unknown')}\n")
                
    print(f"\nBatch summary saved to: {summary_path}")
    print(f"All outputs saved to: {batch_output_dir}/")
    
    # Print summary
    print(f"\nProcessed {successful}/{len(video_files)} videos successfully")
    
    if successful > 0:
        print("\nSuccessful videos:")
        for item in summary_data:
            if item['status'] == 'Success':
                print(f"  ✅ {item['video']} - Detection rate: {item['detection_rate']}")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        video_folder = sys.argv[1]
    else:
        # Default to data/test_videos if it exists
        video_folder = "data/test_videos"
        if not os.path.exists(video_folder):
            print("Usage: python batch_process_videos.py <video_folder>")
            print("\nExample:")
            print("  python batch_process_videos.py /path/to/videos/")
            return
            
    if not os.path.isdir(video_folder):
        print(f"Error: Not a directory: {video_folder}")
        return
        
    batch_process_videos(video_folder)


if __name__ == "__main__":
    main()