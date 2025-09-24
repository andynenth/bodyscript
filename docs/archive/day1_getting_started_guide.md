# Day 1 Getting Started Guide
## From Zero to Working Pose Detection in 4 Hours

---

## 🎯 Day 1 Goal
By the end of today, you'll have:
- ✅ Working pose detection from your webcam
- ✅ Successfully processed your first video file
- ✅ Extracted pose data to CSV
- ✅ Clear understanding of next steps

---

## 📋 Hour-by-Hour Plan

### Hour 1: Environment Setup (9:00 AM - 10:00 AM)

#### 1.1 Create Project Structure (15 min)
```bash
# Open terminal and run these commands
cd ~/python/
mkdir bodyscript_project
cd bodyscript_project

# Create initial folders
mkdir core examples data output
```

#### 1.2 Set Up Virtual Environment (15 min)
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

#### 1.3 Install Core Dependencies (15 min)
```bash
# Install only what we need for Day 1
pip install mediapipe==0.10.7 opencv-python==4.8.1 pandas==2.1.3 numpy==1.24.3

# Verify installation
python -c "import mediapipe as mp; print(f'MediaPipe version: {mp.__version__}')"
```

#### 1.4 Create Test Script (15 min)
Create file `test_installation.py`:
```python
"""Test if all dependencies are installed correctly"""
import sys

try:
    import cv2
    print(f"✅ OpenCV installed: {cv2.__version__}")
except ImportError:
    print("❌ OpenCV not installed")

try:
    import mediapipe as mp
    print(f"✅ MediaPipe installed: {mp.__version__}")
except ImportError:
    print("❌ MediaPipe not installed")

try:
    import pandas as pd
    print(f"✅ Pandas installed: {pd.__version__}")
except ImportError:
    print("❌ Pandas not installed")

try:
    import numpy as np
    print(f"✅ NumPy installed: {np.__version__}")
except ImportError:
    print("❌ NumPy not installed")

print("\n🎉 All dependencies installed successfully!" if all([
    'cv2' in sys.modules,
    'mediapipe' in sys.modules,
    'pandas' in sys.modules,
    'numpy' in sys.modules
]) else "\n⚠️  Some dependencies are missing!")
```

Run it:
```bash
python test_installation.py
```

---

### Hour 2: First Pose Detection (10:00 AM - 11:00 AM)

#### 2.1 Webcam Test Script (30 min)
Create `webcam_pose_test.py`:
```python
"""Your first pose detection with webcam!"""
import cv2
import mediapipe as mp

print("Starting pose detection... Press ESC to quit")

# Initialize MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Start webcam
cap = cv2.VideoCapture(0)
frame_count = 0

while cap.isOpened():
    success, image = cap.read()
    if not success:
        print("Failed to read from webcam")
        continue
    
    # Flip image for selfie view
    image = cv2.flip(image, 1)
    
    # Convert to RGB (MediaPipe requirement)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect pose
    results = pose.process(image_rgb)
    
    # Draw the pose
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image, 
            results.pose_landmarks, 
            mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0,0,255), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0,255,0), thickness=2)
        )
        
        # Show detection status
        cv2.putText(image, "Pose Detected!", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else:
        cv2.putText(image, "No Pose Found", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Show frame count
    frame_count += 1
    cv2.putText(image, f"Frame: {frame_count}", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Display the image
    cv2.imshow('Pose Detection Test', image)
    
    # Check for ESC key
    if cv2.waitKey(5) & 0xFF == 27:
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
print(f"\n✅ Processed {frame_count} frames successfully!")
```

Run it:
```bash
python webcam_pose_test.py
```

**What to look for:**
- Green lines connecting body parts (skeleton)
- Red dots at joint locations
- "Pose Detected!" message when you're visible
- Smooth tracking as you move

#### 2.2 Understanding Landmarks (30 min)
Create `explore_landmarks.py`:
```python
"""Explore the 33 pose landmarks"""
import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose

# Print all landmark names and indices
print("MediaPipe Pose Landmarks (33 total):\n")
for i, landmark in enumerate(mp_pose.PoseLandmark):
    print(f"{i:2d}: {landmark.name}")

print("\n\nLet's explore landmark data...")

# Quick webcam test to see actual values
cap = cv2.VideoCapture(0)
pose = mp_pose.Pose()

print("\nCapturing one frame... Stand in front of camera!")
for _ in range(30):  # Skip first 30 frames for camera to adjust
    cap.read()

success, image = cap.read()
if success:
    results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    if results.pose_landmarks:
        print("\nSample landmark data (first 5 landmarks):")
        print("ID | Name            | X     | Y     | Z      | Visibility")
        print("-" * 65)
        
        for i in range(5):
            landmark = results.pose_landmarks.landmark[i]
            name = mp_pose.PoseLandmark(i).name
            print(f"{i:2d} | {name:15s} | {landmark.x:.3f} | {landmark.y:.3f} | "
                  f"{landmark.z:.4f} | {landmark.visibility:.3f}")
    else:
        print("\nNo pose detected. Make sure you're visible to camera!")

cap.release()
print("\n✅ Now you understand the landmark structure!")
```

---

### Hour 3: Process First Video (11:00 AM - 12:00 PM)

#### 3.1 Download Test Video (10 min)
```bash
# Create data folder if not exists
mkdir -p data/test_videos

# Option 1: Use your phone to record a 10-30 second video of yourself
# Option 2: Download a sample video (if you have wget):
# wget -O data/test_videos/sample.mp4 "https://example.com/sample_video.mp4"

# Or use any MP4 video you have
# Copy it to: data/test_videos/test1.mp4
```

#### 3.2 Basic Video Processor (30 min)
Create `process_first_video.py`:
```python
"""Process your first video and extract pose data"""
import cv2
import mediapipe as mp
import pandas as pd
import os
from datetime import datetime

# Configuration
VIDEO_PATH = "data/test_videos/test1.mp4"  # Change this to your video
OUTPUT_DIR = "output"

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Processing video: {VIDEO_PATH}")

# Initialize MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Open video
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"❌ Error: Cannot open video file: {VIDEO_PATH}")
    exit(1)

# Get video info
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f"Video info: {width}x{height} @ {fps:.1f} fps, {total_frames} frames")

# Process video
pose_data = []
frame_count = 0
detected_frames = 0

print("Processing frames...")
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
    
    # Convert to RGB
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    
    # Extract landmarks if detected
    if results.pose_landmarks:
        detected_frames += 1
        landmarks = results.pose_landmarks.landmark
        
        # Save data for each landmark
        for idx, landmark in enumerate(landmarks):
            pose_data.append({
                'frame_id': frame_count,
                'timestamp': frame_count / fps,
                'landmark_id': idx,
                'x': landmark.x,
                'y': landmark.y,
                'z': landmark.z,
                'visibility': landmark.visibility
            })
    
    frame_count += 1
    
    # Progress update every 30 frames
    if frame_count % 30 == 0:
        print(f"  Processed {frame_count}/{total_frames} frames...")

# Save to CSV
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = os.path.join(OUTPUT_DIR, f"pose_data_{timestamp}.csv")

df = pd.DataFrame(pose_data)
df.to_csv(csv_path, index=False)

# Print summary
print(f"\n✅ Processing complete!")
print(f"  - Total frames: {frame_count}")
print(f"  - Frames with pose detected: {detected_frames}")
print(f"  - Detection rate: {detected_frames/frame_count*100:.1f}%")
print(f"  - Data points saved: {len(pose_data)}")
print(f"  - Output file: {csv_path}")
print(f"  - File size: {os.path.getsize(csv_path) / 1024:.1f} KB")

# Cleanup
cap.release()
pose.close()

# Quick data preview
print("\nFirst few rows of data:")
print(df.head())
```

#### 3.3 Visualize Results (20 min)
Create `visualize_results.py`:
```python
"""Quick visualization of your pose data"""
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

# Find most recent CSV file
output_files = glob.glob("output/pose_data_*.csv")
if not output_files:
    print("No output files found! Run process_first_video.py first.")
    exit(1)

latest_file = max(output_files, key=os.path.getctime)
print(f"Loading: {latest_file}")

# Load data
df = pd.read_csv(latest_file)

# Basic statistics
print("\nData Statistics:")
print(f"- Total measurements: {len(df):,}")
print(f"- Unique frames: {df['frame_id'].nunique()}")
print(f"- Landmarks per frame: {df['landmark_id'].nunique()}")
print(f"- Time span: {df['timestamp'].min():.1f}s to {df['timestamp'].max():.1f}s")

# Plot confidence over time
plt.figure(figsize=(10, 6))

# Average visibility per frame
avg_visibility = df.groupby('frame_id')['visibility'].mean()
plt.subplot(2, 1, 1)
plt.plot(avg_visibility.index, avg_visibility.values)
plt.title('Average Landmark Visibility Over Time')
plt.xlabel('Frame')
plt.ylabel('Visibility (0-1)')
plt.grid(True)

# Plot nose trajectory (landmark 0)
nose_data = df[df['landmark_id'] == 0]
plt.subplot(2, 1, 2)
plt.plot(nose_data['x'], nose_data['y'], 'b-', alpha=0.5)
plt.scatter(nose_data['x'].iloc[0], nose_data['y'].iloc[0], 
            color='green', s=100, label='Start')
plt.scatter(nose_data['x'].iloc[-1], nose_data['y'].iloc[-1], 
            color='red', s=100, label='End')
plt.title('Nose Movement Trajectory')
plt.xlabel('X coordinate')
plt.ylabel('Y coordinate')
plt.legend()
plt.gca().invert_yaxis()  # Invert Y to match image coordinates
plt.grid(True)

plt.tight_layout()
plt.savefig('output/pose_analysis.png')
plt.show()

print("\n✅ Visualization saved to output/pose_analysis.png")
```

---

### Hour 4: Create Core Module Structure (12:00 PM - 1:00 PM)

#### 4.1 Create SimplePoseAnalyzer Class (45 min)
Create `simple_pose_analyzer.py`:
```python
"""Simple pose analyzer - your first reusable module"""
import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import os

class SimplePoseAnalyzer:
    """Simple pose detection and analysis tool"""
    
    def __init__(self, detection_confidence: float = 0.5):
        """Initialize the analyzer"""
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=detection_confidence
        )
        self.results_data = []
        
    def process_video(self, video_path: str, show_progress: bool = True) -> Dict:
        """Process a video and extract pose data"""
        # Reset data
        self.results_data = []
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Process frames
        frame_count = 0
        detected_frames = 0
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            
            # Detect pose
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)
            
            # Extract data
            if results.pose_landmarks:
                detected_frames += 1
                self._extract_frame_data(results, frame_count, fps)
            
            frame_count += 1
            
            # Progress
            if show_progress and frame_count % 30 == 0:
                print(f"Processed {frame_count}/{total_frames} frames...")
        
        cap.release()
        
        # Return summary
        return {
            'total_frames': frame_count,
            'detected_frames': detected_frames,
            'detection_rate': detected_frames / frame_count if frame_count > 0 else 0,
            'fps': fps,
            'data_points': len(self.results_data)
        }
    
    def _extract_frame_data(self, results, frame_id: int, fps: float):
        """Extract pose data from a single frame"""
        timestamp = frame_id / fps
        landmarks = results.pose_landmarks.landmark
        
        for idx, landmark in enumerate(landmarks):
            self.results_data.append({
                'frame_id': frame_id,
                'timestamp': timestamp,
                'landmark_id': idx,
                'landmark_name': self._get_landmark_name(idx),
                'x': landmark.x,
                'y': landmark.y,
                'z': landmark.z,
                'visibility': landmark.visibility
            })
    
    def _get_landmark_name(self, idx: int) -> str:
        """Get human-readable landmark name"""
        try:
            return self.mp_pose.PoseLandmark(idx).name
        except:
            return f"landmark_{idx}"
    
    def export_csv(self, output_path: str):
        """Export results to CSV"""
        if not self.results_data:
            print("No data to export!")
            return
        
        df = pd.DataFrame(self.results_data)
        df.to_csv(output_path, index=False)
        print(f"Exported {len(df)} measurements to {output_path}")
    
    def get_dataframe(self) -> pd.DataFrame:
        """Get results as pandas DataFrame"""
        return pd.DataFrame(self.results_data)
    
    def get_statistics(self) -> Dict:
        """Calculate basic statistics"""
        if not self.results_data:
            return {}
        
        df = pd.DataFrame(self.results_data)
        
        return {
            'total_measurements': len(df),
            'unique_frames': df['frame_id'].nunique(),
            'avg_visibility': df['visibility'].mean(),
            'min_visibility': df['visibility'].min(),
            'max_visibility': df['visibility'].max(),
            'time_range': (df['timestamp'].min(), df['timestamp'].max())
        }

# Example usage
if __name__ == "__main__":
    # Create analyzer
    analyzer = SimplePoseAnalyzer(detection_confidence=0.5)
    
    # Process video
    video_path = "data/test_videos/test1.mp4"
    results = analyzer.process_video(video_path)
    
    # Print results
    print(f"\nProcessing Results:")
    print(f"- Detection rate: {results['detection_rate']:.1%}")
    print(f"- Data points collected: {results['data_points']:,}")
    
    # Export data
    analyzer.export_csv("output/pose_data_simple.csv")
    
    # Get statistics
    stats = analyzer.get_statistics()
    print(f"\nStatistics:")
    print(f"- Average visibility: {stats['avg_visibility']:.3f}")
    print(f"- Time range: {stats['time_range'][0]:.1f}s - {stats['time_range'][1]:.1f}s")
```

#### 4.2 Test Your Module (15 min)
Create `test_analyzer.py`:
```python
"""Test the SimplePoseAnalyzer"""
from simple_pose_analyzer import SimplePoseAnalyzer

# Create analyzer with lower confidence for testing
analyzer = SimplePoseAnalyzer(detection_confidence=0.3)

# Test with your video
video_path = "data/test_videos/test1.mp4"  # Update this path

print("Testing SimplePoseAnalyzer...")
try:
    # Process video
    results = analyzer.process_video(video_path, show_progress=True)
    
    # Show results
    print(f"\n✅ Success! Processed {results['total_frames']} frames")
    print(f"Detection rate: {results['detection_rate']:.1%}")
    
    # Export to CSV
    analyzer.export_csv("output/test_analyzer_output.csv")
    
    # Get some data
    df = analyzer.get_dataframe()
    print(f"\nData shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Show sample data
    print("\nSample data (first 5 rows):")
    print(df.head())
    
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## 🎯 End of Day 1 Checklist

### What You Should Have Accomplished:
- [x] Working Python environment with MediaPipe
- [x] Successful webcam pose detection
- [x] Processed at least one video file
- [x] Extracted pose data to CSV format
- [x] Basic understanding of 33 pose landmarks
- [x] Created your first reusable analyzer class
- [x] Generated simple visualizations

### Files You Should Have Created:
- [x] `test_installation.py` - Dependency checker
- [x] `webcam_pose_test.py` - Live pose detection
- [x] `explore_landmarks.py` - Understanding landmarks
- [x] `process_first_video.py` - Basic video processing
- [x] `visualize_results.py` - Data visualization
- [x] `simple_pose_analyzer.py` - Reusable analyzer class
- [x] `test_analyzer.py` - Module testing

### Data You Should Have Generated:
- [x] At least one CSV file with pose data
- [x] Basic visualization plot
- [x] Understanding of detection rates

---

## 🚀 What's Next? (Day 2 Preview)

Tomorrow you'll build on today's foundation:

1. **Improve the VideoLoader**
   - Handle different video formats
   - Add batch processing
   - Implement frame skipping for efficiency

2. **Enhance Pose Detection**
   - Add confidence filtering
   - Implement smoothing
   - Handle multiple people

3. **Create Skeleton Overlay Videos**
   - Draw pose on original video
   - Export processed videos
   - Add visual analytics

4. **Start Building Core Architecture**
   - Separate modules for each component
   - Add configuration management
   - Implement proper error handling

---

## 💡 Troubleshooting

### Common Issues:

**"No module named mediapipe"**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install mediapipe==0.10.7
```

**"Camera not found" or black screen**
```python
# Try different camera indices
cap = cv2.VideoCapture(1)  # or 2, 3, etc.
```

**Low detection rate**
```python
# Lower the confidence threshold
pose = mp_pose.Pose(min_detection_confidence=0.3)
```

**Video file not found**
```python
# Use absolute path
video_path = os.path.abspath("data/test_videos/test1.mp4")
print(f"Looking for video at: {video_path}")
```

---

## 🎉 Congratulations!

You've completed Day 1! You now have:
- A working pose detection system
- Real data from your own videos  
- A foundation to build upon
- Clear path forward

Take a break, review what you've learned, and get ready for Day 2!

---

**Remember**: The goal is progress, not perfection. Every line of code you write is a step forward!