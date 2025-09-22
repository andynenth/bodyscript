"""
Automated Reporting Module - Generate comprehensive research reports
Creates HTML/PDF reports with analysis results, visualizations, and statistics
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import base64
from io import BytesIO
import matplotlib.pyplot as plt


class ResearchReporter:
    """
    Generates comprehensive research reports from pose analysis results.
    """

    def __init__(self, output_dir: str = 'reports'):
        """
        Initialize the reporting system.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_html_report(self,
                           video_info: Dict,
                           pose_data: pd.DataFrame,
                           quality_metrics: Optional[Dict] = None,
                           movement_analysis: Optional[Dict] = None,
                           figures: Optional[Dict] = None) -> str:
        """
        Generate comprehensive HTML report.

        Args:
            video_info: Video metadata
            pose_data: Processed pose data
            quality_metrics: Quality assessment results
            movement_analysis: Movement pattern analysis
            figures: Dictionary of matplotlib figures

        Returns:
            Path to generated HTML report
        """
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_name = f"pose_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        # Start building HTML
        html_content = self._generate_html_header()

        # Add title and metadata
        html_content += f"""
        <div class="header">
            <h1>Pose Analysis Report</h1>
            <p class="timestamp">Generated: {timestamp}</p>
        </div>

        <div class="section">
            <h2>📹 Video Information</h2>
            <table class="info-table">
                <tr><td><strong>File Name:</strong></td><td>{video_info.get('filename', 'N/A')}</td></tr>
                <tr><td><strong>Duration:</strong></td><td>{video_info.get('duration', 0):.2f} seconds</td></tr>
                <tr><td><strong>Frame Rate:</strong></td><td>{video_info.get('fps', 0):.1f} fps</td></tr>
                <tr><td><strong>Resolution:</strong></td><td>{video_info.get('width', 0)}x{video_info.get('height', 0)}</td></tr>
                <tr><td><strong>Total Frames:</strong></td><td>{video_info.get('total_frames', 0)}</td></tr>
                <tr><td><strong>Processing Mode:</strong></td><td>{video_info.get('mode', 'RESEARCH')}</td></tr>
            </table>
        </div>
        """

        # Add quality metrics
        if quality_metrics:
            html_content += self._generate_quality_section(quality_metrics)

        # Add movement analysis
        if movement_analysis:
            html_content += self._generate_movement_section(movement_analysis)

        # Add statistics
        html_content += self._generate_statistics_section(pose_data)

        # Add visualizations
        if figures:
            html_content += self._generate_visualizations_section(figures)

        # Add data summary
        html_content += self._generate_data_summary_section(pose_data)

        # Add footer
        html_content += self._generate_html_footer()

        # Save report
        output_path = self.output_dir / report_name
        with open(output_path, 'w') as f:
            f.write(html_content)

        print(f"✓ HTML report generated: {output_path}")
        return str(output_path)

    def _generate_html_header(self) -> str:
        """Generate HTML header with styling."""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Pose Analysis Report</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }

                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    overflow: hidden;
                }

                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px;
                    text-align: center;
                }

                .header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }

                .timestamp {
                    opacity: 0.9;
                    font-size: 0.9em;
                }

                .section {
                    padding: 30px 40px;
                    border-bottom: 1px solid #eee;
                }

                .section:last-child {
                    border-bottom: none;
                }

                h2 {
                    color: #667eea;
                    margin-bottom: 20px;
                    font-size: 1.8em;
                }

                h3 {
                    color: #555;
                    margin-top: 20px;
                    margin-bottom: 15px;
                }

                .info-table {
                    width: 100%;
                    border-collapse: collapse;
                }

                .info-table td {
                    padding: 10px;
                    border-bottom: 1px solid #f0f0f0;
                }

                .info-table td:first-child {
                    width: 40%;
                    color: #666;
                }

                .metric-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }

                .metric-card {
                    background: #f8f9fa;
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                    transition: transform 0.3s;
                }

                .metric-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                }

                .metric-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                }

                .metric-label {
                    color: #666;
                    margin-top: 5px;
                    font-size: 0.9em;
                }

                .quality-indicator {
                    display: inline-block;
                    padding: 5px 15px;
                    border-radius: 20px;
                    color: white;
                    font-weight: bold;
                    margin-left: 10px;
                }

                .quality-good { background: #28a745; }
                .quality-fair { background: #ffc107; }
                .quality-poor { background: #dc3545; }

                .pattern-card {
                    background: #e3f2fd;
                    border-left: 4px solid #2196f3;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                }

                .visualization-container {
                    margin: 20px 0;
                    text-align: center;
                }

                .visualization-container img {
                    max-width: 100%;
                    border-radius: 10px;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                }

                .data-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }

                .data-table th {
                    background: #667eea;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }

                .data-table td {
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }

                .data-table tr:hover {
                    background: #f8f9fa;
                }

                .footer {
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 0.9em;
                }

                .badge {
                    display: inline-block;
                    padding: 3px 10px;
                    background: #667eea;
                    color: white;
                    border-radius: 15px;
                    font-size: 0.85em;
                    margin: 2px;
                }

                .progress-bar {
                    width: 100%;
                    height: 20px;
                    background: #f0f0f0;
                    border-radius: 10px;
                    overflow: hidden;
                    margin: 10px 0;
                }

                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    transition: width 0.3s;
                }
            </style>
        </head>
        <body>
            <div class="container">
        """

    def _generate_quality_section(self, metrics: Dict) -> str:
        """Generate quality metrics section."""
        # Determine overall quality level
        overall_score = metrics.get('overall_score', 0)
        if overall_score >= 0.8:
            quality_class = "quality-good"
            quality_text = "EXCELLENT"
        elif overall_score >= 0.6:
            quality_class = "quality-fair"
            quality_text = "GOOD"
        else:
            quality_class = "quality-poor"
            quality_text = "NEEDS IMPROVEMENT"

        html = f"""
        <div class="section">
            <h2>📊 Quality Assessment
                <span class="quality-indicator {quality_class}">{quality_text}</span>
            </h2>
            <div class="metric-grid">
        """

        # Add metric cards
        metric_items = [
            ('detection_rate', 'Detection Rate', '{:.1%}'),
            ('avg_confidence', 'Avg Confidence', '{:.3f}'),
            ('temporal_consistency', 'Temporal Consistency', '{:.3f}'),
            ('frame_coverage', 'Frame Coverage', '{:.1%}'),
            ('overall_score', 'Overall Score', '{:.3f}')
        ]

        for key, label, format_str in metric_items:
            if key in metrics:
                value = metrics[key]
                formatted_value = format_str.format(value)
                html += f"""
                <div class="metric-card">
                    <div class="metric-value">{formatted_value}</div>
                    <div class="metric-label">{label}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {value*100}%"></div>
                    </div>
                </div>
                """

        html += """
            </div>
        </div>
        """
        return html

    def _generate_movement_section(self, analysis: Dict) -> str:
        """Generate movement analysis section."""
        html = """
        <div class="section">
            <h2>🏃 Movement Analysis</h2>
        """

        # Joint angles
        if 'joint_angles' in analysis and 'means' in analysis['joint_angles']:
            html += "<h3>Joint Angles (Average)</h3><div class='metric-grid'>"
            for joint, angle in analysis['joint_angles']['means'].items():
                html += f"""
                <div class="metric-card">
                    <div class="metric-value">{angle:.1f}°</div>
                    <div class="metric-label">{joint.replace('_', ' ').title()}</div>
                </div>
                """
            html += "</div>"

        # Movement patterns
        if 'movement_patterns' in analysis:
            html += "<h3>Detected Movement Patterns</h3>"
            for pattern_name, pattern_info in analysis['movement_patterns'].items():
                html += f"""
                <div class="pattern-card">
                    <strong>{pattern_name.replace('_', ' ').title()}</strong>
                """

                if isinstance(pattern_info, dict):
                    for key, value in pattern_info.items():
                        if key != 'detected':
                            html += f"<br>• {key.replace('_', ' ').title()}: {value}"

                html += "</div>"

        # Symmetry scores
        if 'symmetry' in analysis:
            html += "<h3>Movement Symmetry</h3><div class='metric-grid'>"
            for body_part, score in analysis['symmetry'].items():
                color = '#28a745' if score > 0.8 else '#ffc107' if score > 0.6 else '#dc3545'
                html += f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: {color}">{score:.2f}</div>
                    <div class="metric-label">{body_part.title()}</div>
                </div>
                """
            html += "</div>"

        html += "</div>"
        return html

    def _generate_statistics_section(self, df: pd.DataFrame) -> str:
        """Generate statistics section."""
        html = """
        <div class="section">
            <h2>📈 Statistical Summary</h2>
        """

        # Calculate statistics
        stats = {
            'Total Frames': df['frame_id'].nunique() if 'frame_id' in df else 0,
            'Total Landmarks': df['landmark_id'].nunique() if 'landmark_id' in df else 0,
            'Data Points': len(df),
            'Missing Values': df[['x', 'y']].isna().sum().sum() if all(c in df for c in ['x', 'y']) else 0
        }

        html += "<div class='metric-grid'>"
        for label, value in stats.items():
            html += f"""
            <div class="metric-card">
                <div class="metric-value">{value:,}</div>
                <div class="metric-label">{label}</div>
            </div>
            """
        html += "</div>"

        # Add coordinate ranges
        if all(c in df for c in ['x', 'y', 'z']):
            html += "<h3>Coordinate Ranges</h3>"
            html += "<table class='info-table'>"
            for coord in ['x', 'y', 'z']:
                min_val = df[coord].min()
                max_val = df[coord].max()
                mean_val = df[coord].mean()
                std_val = df[coord].std()
                html += f"""
                <tr>
                    <td><strong>{coord.upper()} Coordinate:</strong></td>
                    <td>Min: {min_val:.3f}, Max: {max_val:.3f}, Mean: {mean_val:.3f}, Std: {std_val:.3f}</td>
                </tr>
                """
            html += "</table>"

        html += "</div>"
        return html

    def _generate_visualizations_section(self, figures: Dict) -> str:
        """Generate visualizations section with embedded images."""
        html = """
        <div class="section">
            <h2>📊 Visualizations</h2>
        """

        for fig_name, fig in figures.items():
            if fig is not None:
                # Convert figure to base64
                img_base64 = self._fig_to_base64(fig)

                # Add to HTML
                html += f"""
                <div class="visualization-container">
                    <h3>{fig_name.replace('_', ' ').title()}</h3>
                    <img src="data:image/png;base64,{img_base64}" alt="{fig_name}">
                </div>
                """

        html += "</div>"
        return html

    def _generate_data_summary_section(self, df: pd.DataFrame) -> str:
        """Generate data summary section."""
        html = """
        <div class="section">
            <h2>📋 Data Summary</h2>
        """

        # Sample of processed data
        if not df.empty:
            sample_size = min(10, len(df))
            sample_df = df.head(sample_size)

            html += f"<p>Showing first {sample_size} rows of {len(df)} total data points</p>"
            html += "<table class='data-table'>"

            # Headers
            html += "<tr>"
            for col in sample_df.columns[:8]:  # Limit columns for readability
                html += f"<th>{col}</th>"
            html += "</tr>"

            # Data rows
            for _, row in sample_df.iterrows():
                html += "<tr>"
                for col in sample_df.columns[:8]:
                    value = row[col]
                    if isinstance(value, float):
                        html += f"<td>{value:.3f}</td>"
                    else:
                        html += f"<td>{value}</td>"
                html += "</tr>"

            html += "</table>"

        html += "</div>"
        return html

    def _generate_html_footer(self) -> str:
        """Generate HTML footer."""
        return """
                <div class="footer">
                    <p>Generated by BodyScript Research System v2.0</p>
                    <p>© 2025 - Comprehensive Pose Analysis Platform</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        return img_base64

    def generate_csv_summary(self,
                            pose_data: pd.DataFrame,
                            angles_data: Optional[pd.DataFrame] = None,
                            output_name: Optional[str] = None) -> str:
        """
        Generate CSV files with analysis results.

        Args:
            pose_data: Processed pose data
            angles_data: Joint angles data
            output_name: Base name for output files

        Returns:
            Path to CSV files
        """
        if output_name is None:
            output_name = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Save pose data
        pose_path = self.output_dir / f"{output_name}_pose_data.csv"
        pose_data.to_csv(pose_path, index=False)
        print(f"✓ Pose data saved to {pose_path}")

        # Save angles data if available
        if angles_data is not None:
            angles_path = self.output_dir / f"{output_name}_angles.csv"
            angles_data.to_csv(angles_path, index=False)
            print(f"✓ Angle data saved to {angles_path}")

        return str(pose_path)

    def generate_executive_summary(self,
                                 video_info: Dict,
                                 quality_metrics: Dict,
                                 movement_analysis: Dict) -> str:
        """
        Generate a concise executive summary.

        Args:
            video_info: Video metadata
            quality_metrics: Quality assessment
            movement_analysis: Movement patterns

        Returns:
            Executive summary text
        """
        summary = f"""
EXECUTIVE SUMMARY
==================

VIDEO ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

FILE INFORMATION
----------------
• File: {video_info.get('filename', 'N/A')}
• Duration: {video_info.get('duration', 0):.2f} seconds
• Frames: {video_info.get('total_frames', 0)}
• Resolution: {video_info.get('width', 0)}x{video_info.get('height', 0)}

QUALITY ASSESSMENT
------------------
• Overall Score: {quality_metrics.get('overall_score', 0):.3f}
• Detection Rate: {quality_metrics.get('detection_rate', 0):.1%}
• Confidence: {quality_metrics.get('avg_confidence', 0):.3f}
• Research Quality: {'YES' if quality_metrics.get('is_research_quality', False) else 'NO'}

MOVEMENT ANALYSIS
-----------------
"""
        # Add detected patterns
        if 'movement_patterns' in movement_analysis:
            patterns = list(movement_analysis['movement_patterns'].keys())
            summary += f"• Detected Patterns: {', '.join(patterns) if patterns else 'None'}\n"

        # Add symmetry score
        if 'symmetry' in movement_analysis:
            overall_symmetry = movement_analysis['symmetry'].get('overall', 0)
            summary += f"• Movement Symmetry: {overall_symmetry:.3f}\n"

        # Add key findings
        summary += """
KEY FINDINGS
------------
"""
        if quality_metrics.get('detection_rate', 0) > 0.9:
            summary += "✓ Excellent pose detection throughout video\n"
        if quality_metrics.get('temporal_consistency', 0) > 0.8:
            summary += "✓ Highly consistent temporal tracking\n"
        if 'walking' in movement_analysis.get('movement_patterns', {}):
            walking = movement_analysis['movement_patterns']['walking']
            summary += f"✓ Walking pattern detected ({walking.get('step_count', 0)} steps)\n"

        summary += """
RECOMMENDATIONS
---------------
"""
        if quality_metrics.get('detection_rate', 0) < 0.8:
            summary += "• Consider improving video quality or lighting\n"
        if quality_metrics.get('avg_confidence', 0) < 0.6:
            summary += "• Ensure subject is clearly visible\n"

        # Save summary
        summary_path = self.output_dir / f"executive_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_path, 'w') as f:
            f.write(summary)

        print(f"✓ Executive summary saved to {summary_path}")
        return summary


def test_reporting():
    """Test the reporting module."""
    print("\n=== Testing Reporting Module ===\n")

    # Create sample data
    video_info = {
        'filename': 'test_video.mp4',
        'duration': 10.0,
        'fps': 30.0,
        'width': 1920,
        'height': 1080,
        'total_frames': 300,
        'mode': 'RESEARCH'
    }

    # Sample pose data
    pose_data = pd.DataFrame({
        'frame_id': np.repeat(range(10), 33),
        'landmark_id': np.tile(range(33), 10),
        'x': np.random.random(330),
        'y': np.random.random(330),
        'z': np.random.random(330),
        'visibility': np.random.uniform(0.5, 1.0, 330)
    })

    # Sample quality metrics
    quality_metrics = {
        'detection_rate': 0.92,
        'avg_confidence': 0.78,
        'temporal_consistency': 0.85,
        'frame_coverage': 0.95,
        'overall_score': 0.83,
        'is_research_quality': True
    }

    # Sample movement analysis
    movement_analysis = {
        'joint_angles': {
            'means': {
                'left_elbow': 95.2,
                'right_elbow': 93.7,
                'left_knee': 115.3,
                'right_knee': 117.1
            }
        },
        'movement_patterns': {
            'walking': {
                'detected': True,
                'frequency': 1.2,
                'step_count': 24
            }
        },
        'symmetry': {
            'shoulders': 0.85,
            'elbows': 0.78,
            'overall': 0.81
        }
    }

    # Initialize reporter
    reporter = ResearchReporter(output_dir='test_reports')

    # Generate HTML report
    html_path = reporter.generate_html_report(
        video_info=video_info,
        pose_data=pose_data,
        quality_metrics=quality_metrics,
        movement_analysis=movement_analysis
    )

    # Generate CSV summary
    csv_path = reporter.generate_csv_summary(pose_data)

    # Generate executive summary
    summary = reporter.generate_executive_summary(
        video_info=video_info,
        quality_metrics=quality_metrics,
        movement_analysis=movement_analysis
    )

    print("\n✓ Test reports generated successfully")
    print(f"  - HTML Report: {html_path}")
    print(f"  - CSV Data: {csv_path}")
    print("\nExecutive Summary Preview:")
    print("=" * 50)
    print(summary[:500] + "...")


if __name__ == "__main__":
    test_reporting()