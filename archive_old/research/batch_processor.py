"""
Batch Processing Module - Process multiple videos efficiently
Handles parallel processing, progress tracking, and comparative analysis
"""

import os
import cv2
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import json
import time
from datetime import datetime
import multiprocessing as mp
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.video_loader import VideoLoader
from research.holistic_detector import HolisticPoseDetector
from research.quality_control import QualityControl
from research.analytics import BiomechanicalAnalyzer
from research.visualizations import ResearchVisualizer
from research.reporting import ResearchReporter


class BatchProcessor:
    """
    Batch processing system for multiple videos.
    Supports parallel processing, progress tracking, and comparative analysis.
    """

    def __init__(self,
                 output_dir: str = 'batch_output',
                 mode: str = 'RESEARCH',
                 max_workers: Optional[int] = None):
        """
        Initialize batch processor.

        Args:
            output_dir: Directory for batch output
            mode: Processing mode (MVP/RESEARCH/CREATIVE)
            max_workers: Maximum parallel workers (default: CPU count)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.mode = mode
        self.max_workers = max_workers or mp.cpu_count()

        # Create subdirectories
        self.data_dir = self.output_dir / 'data'
        self.reports_dir = self.output_dir / 'reports'
        self.viz_dir = self.output_dir / 'visualizations'

        for dir_path in [self.data_dir, self.reports_dir, self.viz_dir]:
            dir_path.mkdir(exist_ok=True)

        # Batch results storage
        self.batch_results = []

    def process_batch(self,
                     video_paths: List[str],
                     parallel: bool = True,
                     generate_reports: bool = True,
                     comparative_analysis: bool = True) -> Dict:
        """
        Process multiple videos in batch.

        Args:
            video_paths: List of video file paths
            parallel: Whether to process in parallel
            generate_reports: Whether to generate individual reports
            comparative_analysis: Whether to perform comparative analysis

        Returns:
            Dictionary with batch processing results
        """
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING - {len(video_paths)} Videos")
        print(f"{'='*60}")
        print(f"Mode: {self.mode}")
        print(f"Parallel Processing: {'Yes' if parallel else 'No'}")
        print(f"Workers: {self.max_workers if parallel else 1}")
        print(f"Output Directory: {self.output_dir}")
        print(f"{'='*60}\n")

        start_time = time.time()

        # Process videos
        if parallel:
            results = self._process_parallel(video_paths, generate_reports)
        else:
            results = self._process_sequential(video_paths, generate_reports)

        # Perform comparative analysis
        if comparative_analysis and len(results) > 1:
            print("\n📊 Performing Comparative Analysis...")
            comparison = self._comparative_analysis(results)
        else:
            comparison = None

        # Generate batch report
        batch_report = self._generate_batch_report(results, comparison)

        # Calculate processing time
        total_time = time.time() - start_time

        # Summary statistics
        summary = {
            'videos_processed': len(results),
            'successful': sum(1 for r in results if r.get('success', False)),
            'failed': sum(1 for r in results if not r.get('success', False)),
            'total_time': total_time,
            'avg_time_per_video': total_time / len(video_paths) if video_paths else 0,
            'batch_report_path': batch_report,
            'output_directory': str(self.output_dir)
        }

        # Print summary
        self._print_summary(summary, results)

        return {
            'summary': summary,
            'results': results,
            'comparison': comparison,
            'report_path': batch_report
        }

    def _process_parallel(self,
                        video_paths: List[str],
                        generate_reports: bool) -> List[Dict]:
        """Process videos in parallel."""
        results = []

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_video = {
                executor.submit(self._process_single_video, path, idx, generate_reports): (path, idx)
                for idx, path in enumerate(video_paths)
            }

            # Process completed tasks
            with tqdm(total=len(video_paths), desc="Processing videos") as pbar:
                for future in as_completed(future_to_video):
                    video_path, idx = future_to_video[future]
                    try:
                        result = future.result()
                        results.append(result)
                        pbar.update(1)
                        pbar.set_postfix({'current': Path(video_path).name})
                    except Exception as e:
                        print(f"\n❌ Error processing {video_path}: {e}")
                        results.append({
                            'video_path': video_path,
                            'success': False,
                            'error': str(e)
                        })
                        pbar.update(1)

        return sorted(results, key=lambda x: x.get('index', 0))

    def _process_sequential(self,
                          video_paths: List[str],
                          generate_reports: bool) -> List[Dict]:
        """Process videos sequentially."""
        results = []

        for idx, video_path in enumerate(tqdm(video_paths, desc="Processing videos")):
            try:
                result = self._process_single_video(video_path, idx, generate_reports)
                results.append(result)
            except Exception as e:
                print(f"\n❌ Error processing {video_path}: {e}")
                results.append({
                    'video_path': video_path,
                    'success': False,
                    'error': str(e)
                })

        return results

    def _process_single_video(self,
                            video_path: str,
                            index: int,
                            generate_report: bool) -> Dict:
        """
        Process a single video file.

        Args:
            video_path: Path to video file
            index: Video index in batch
            generate_report: Whether to generate report

        Returns:
            Processing results dictionary
        """
        video_name = Path(video_path).stem
        result = {
            'index': index,
            'video_path': video_path,
            'video_name': video_name,
            'success': False
        }

        try:
            # Load video
            loader = VideoLoader()
            video_data = loader.load_video(video_path)
            frames = list(loader.extract_frames(max_frames=300))  # Limit for performance

            # Get video info
            metadata = loader.get_video_metadata()
            result['video_info'] = metadata

            # Detect poses
            if self.mode == 'RESEARCH':
                detector = HolisticPoseDetector(mode=self.mode)
            else:
                # Fall back to basic detector for MVP mode
                from core.pose_detector import BasicPoseDetector
                detector = BasicPoseDetector(mode=self.mode)

            pose_results = detector.detect_poses(frames, progress_bar=False)

            # Convert to DataFrame
            all_data = []
            for frame_result in pose_results:
                if hasattr(frame_result, 'to_dataframe'):
                    frame_df = frame_result.to_dataframe()
                    if not frame_df.empty:
                        all_data.append(frame_df)

            if all_data:
                pose_df = pd.concat(all_data, ignore_index=True)
            else:
                pose_df = pd.DataFrame()

            # Quality control
            qc = QualityControl()
            pose_df_processed, quality_metrics = qc.process_dataframe(pose_df, apply_all=True)

            # Movement analysis
            analyzer = BiomechanicalAnalyzer(fps=metadata.get('fps', 30))
            movement_report = analyzer.generate_movement_report(pose_df_processed)

            # Store processed data
            data_path = self.data_dir / f"{video_name}_pose_data.csv"
            pose_df_processed.to_csv(data_path, index=False)

            # Update result
            result.update({
                'success': True,
                'data_path': str(data_path),
                'frames_processed': len(frames),
                'quality_metrics': quality_metrics.__dict__ if hasattr(quality_metrics, '__dict__') else quality_metrics,
                'movement_analysis': {
                    'patterns': list(movement_report.get('movement_patterns', {}).keys()),
                    'symmetry': movement_report.get('symmetry', {}),
                },
                'statistics': detector.get_statistics() if hasattr(detector, 'get_statistics') else {}
            })

            # Generate individual report if requested
            if generate_report:
                reporter = ResearchReporter(output_dir=str(self.reports_dir))
                report_path = reporter.generate_html_report(
                    video_info=metadata,
                    pose_data=pose_df_processed,
                    quality_metrics=quality_metrics.__dict__ if hasattr(quality_metrics, '__dict__') else quality_metrics,
                    movement_analysis=movement_report
                )
                result['report_path'] = report_path

        except Exception as e:
            result['error'] = str(e)
            result['success'] = False

        return result

    def _comparative_analysis(self, results: List[Dict]) -> Dict:
        """
        Perform comparative analysis across all videos.

        Args:
            results: List of individual video results

        Returns:
            Comparative analysis dictionary
        """
        comparison = {
            'quality_comparison': {},
            'pattern_comparison': {},
            'performance_comparison': {},
            'rankings': {}
        }

        # Extract successful results
        successful_results = [r for r in results if r.get('success', False)]

        if not successful_results:
            return comparison

        # Quality comparison
        quality_metrics = ['detection_rate', 'avg_confidence', 'temporal_consistency', 'overall_score']
        for metric in quality_metrics:
            values = []
            for result in successful_results:
                if 'quality_metrics' in result and metric in result['quality_metrics']:
                    values.append({
                        'video': result['video_name'],
                        'value': result['quality_metrics'][metric]
                    })

            if values:
                comparison['quality_comparison'][metric] = {
                    'values': values,
                    'mean': np.mean([v['value'] for v in values]),
                    'std': np.std([v['value'] for v in values]),
                    'best': max(values, key=lambda x: x['value'])
                }

        # Pattern comparison
        all_patterns = set()
        for result in successful_results:
            if 'movement_analysis' in result and 'patterns' in result['movement_analysis']:
                all_patterns.update(result['movement_analysis']['patterns'])

        pattern_matrix = {}
        for pattern in all_patterns:
            pattern_matrix[pattern] = []
            for result in successful_results:
                has_pattern = pattern in result.get('movement_analysis', {}).get('patterns', [])
                pattern_matrix[pattern].append({
                    'video': result['video_name'],
                    'detected': has_pattern
                })

        comparison['pattern_comparison'] = pattern_matrix

        # Performance comparison
        comparison['performance_comparison'] = {
            'frames_processed': {
                'total': sum(r.get('frames_processed', 0) for r in successful_results),
                'per_video': [
                    {'video': r['video_name'], 'frames': r.get('frames_processed', 0)}
                    for r in successful_results
                ]
            }
        }

        # Generate rankings
        if comparison['quality_comparison'].get('overall_score'):
            scores = comparison['quality_comparison']['overall_score']['values']
            sorted_scores = sorted(scores, key=lambda x: x['value'], reverse=True)
            comparison['rankings']['quality'] = [
                {'rank': i+1, 'video': s['video'], 'score': s['value']}
                for i, s in enumerate(sorted_scores)
            ]

        return comparison

    def _generate_batch_report(self,
                              results: List[Dict],
                              comparison: Optional[Dict]) -> str:
        """Generate comprehensive batch processing report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_name = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        # Build HTML content
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Batch Processing Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
                h1 {{ color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
                h2 {{ color: #667eea; margin-top: 30px; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
                .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
                .summary-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
                .summary-label {{ color: #666; margin-top: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #667eea; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #eee; }}
                .success {{ background: #d4edda; }}
                .failure {{ background: #f8d7da; }}
                .ranking {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Batch Processing Report</h1>
                <p>Generated: {timestamp}</p>

                <h2>📊 Summary</h2>
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-value">{len(results)}</div>
                        <div class="summary-label">Videos Processed</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">{sum(1 for r in results if r.get('success'))}</div>
                        <div class="summary-label">Successful</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">{sum(1 for r in results if not r.get('success'))}</div>
                        <div class="summary-label">Failed</div>
                    </div>
                </div>

                <h2>📹 Individual Results</h2>
                <table>
                    <tr>
                        <th>Video</th>
                        <th>Status</th>
                        <th>Frames</th>
                        <th>Detection Rate</th>
                        <th>Overall Score</th>
                        <th>Patterns</th>
                    </tr>
        """

        for result in results:
            status_class = 'success' if result.get('success') else 'failure'
            status_text = '✓ Success' if result.get('success') else '✗ Failed'

            quality = result.get('quality_metrics', {})
            patterns = result.get('movement_analysis', {}).get('patterns', [])

            html += f"""
                <tr class="{status_class}">
                    <td>{result.get('video_name', 'Unknown')}</td>
                    <td>{status_text}</td>
                    <td>{result.get('frames_processed', 'N/A')}</td>
                    <td>{quality.get('detection_rate', 0):.1%}</td>
                    <td>{quality.get('overall_score', 0):.3f}</td>
                    <td>{', '.join(patterns) if patterns else 'None'}</td>
                </tr>
            """

        html += "</table>"

        # Add comparative analysis if available
        if comparison:
            html += "<h2>📈 Comparative Analysis</h2>"

            # Quality rankings
            if 'rankings' in comparison and 'quality' in comparison['rankings']:
                html += "<h3>Quality Rankings</h3>"
                html += "<div class='ranking'>"
                for item in comparison['rankings']['quality']:
                    html += f"<p>{item['rank']}. {item['video']} - Score: {item['score']:.3f}</p>"
                html += "</div>"

            # Pattern detection matrix
            if 'pattern_comparison' in comparison:
                html += "<h3>Pattern Detection Matrix</h3>"
                html += "<table>"
                html += "<tr><th>Pattern</th><th>Videos Detected In</th><th>Detection Rate</th></tr>"

                for pattern, detections in comparison['pattern_comparison'].items():
                    detected_videos = [d['video'] for d in detections if d['detected']]
                    detection_rate = len(detected_videos) / len(detections) if detections else 0

                    html += f"""
                        <tr>
                            <td>{pattern}</td>
                            <td>{', '.join(detected_videos) if detected_videos else 'None'}</td>
                            <td>{detection_rate:.1%}</td>
                        </tr>
                    """

                html += "</table>"

        html += """
            </div>
        </body>
        </html>
        """

        # Save report
        report_path = self.reports_dir / report_name
        with open(report_path, 'w') as f:
            f.write(html)

        return str(report_path)

    def _print_summary(self, summary: Dict, results: List[Dict]):
        """Print batch processing summary to console."""
        print(f"\n{'='*60}")
        print("BATCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"✓ Videos Processed: {summary['videos_processed']}")
        print(f"✓ Successful: {summary['successful']}")
        print(f"✗ Failed: {summary['failed']}")
        print(f"⏱ Total Time: {summary['total_time']:.2f} seconds")
        print(f"⏱ Avg Time/Video: {summary['avg_time_per_video']:.2f} seconds")
        print(f"📁 Output Directory: {summary['output_directory']}")
        print(f"📄 Batch Report: {summary['batch_report_path']}")

        if summary['failed'] > 0:
            print(f"\n❌ Failed Videos:")
            for result in results:
                if not result.get('success'):
                    print(f"  - {result.get('video_name', 'Unknown')}: {result.get('error', 'Unknown error')}")

        print(f"{'='*60}\n")


def test_batch_processor():
    """Test the batch processor with sample videos."""
    print("\n=== Testing Batch Processor ===\n")

    # Create test video paths (you would use real videos)
    test_videos = [
        "test_video1.mp4",
        "test_video2.mp4",
        "test_video3.mp4"
    ]

    # Note: For actual testing, you need real video files
    # This is just a demonstration of the interface

    # Initialize batch processor
    processor = BatchProcessor(
        output_dir='batch_test_output',
        mode='RESEARCH',
        max_workers=2
    )

    print("Batch processor initialized")
    print(f"Output directory: {processor.output_dir}")
    print(f"Mode: {processor.mode}")
    print(f"Max workers: {processor.max_workers}")

    # Demonstrate the interface (would process real videos)
    print("\nBatch processor ready for processing videos:")
    print(f"  processor.process_batch({test_videos})")

    print("\n✓ Batch processor test complete")


if __name__ == "__main__":
    test_batch_processor()