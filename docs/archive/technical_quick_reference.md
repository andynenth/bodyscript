# BodyScript Technical Quick Reference
## Essential Code Snippets & Technical Details

---

## 🚀 Quick Start Code

### Minimal Webcam Test (Day 1)
```python
import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)  # 0 for webcam, or video file path

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break
    
    # Process the image
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    
    # Draw landmarks
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
    
    cv2.imshow('MediaPipe Pose', image)
    if cv2.waitKey(5) & 0xFF == 27:  # Press ESC to exit
        break

cap.release()
cv2.destroyAllWindows()
```

---

## 📊 MediaPipe Pose Landmarks Reference

### Body Pose Landmarks (33 points)
```python
# MediaPipe pose landmark indices
NOSE = 0
LEFT_EYE_INNER = 1
LEFT_EYE = 2
LEFT_EYE_OUTER = 3
RIGHT_EYE_INNER = 4
RIGHT_EYE = 5
RIGHT_EYE_OUTER = 6
LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_MOUTH = 9
RIGHT_MOUTH = 10
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_PINKY = 17
RIGHT_PINKY = 18
LEFT_INDEX = 19
RIGHT_INDEX = 20
LEFT_THUMB = 21
RIGHT_THUMB = 22
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_HEEL = 29
RIGHT_HEEL = 30
LEFT_FOOT_INDEX = 31
RIGHT_FOOT_INDEX = 32
```

### Accessing Landmarks
```python
if results.pose_landmarks:
    landmarks = results.pose_landmarks.landmark
    
    # Get specific landmark
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    print(f"Nose position: x={nose.x}, y={nose.y}, z={nose.z}, visibility={nose.visibility}")
    
    # Iterate through all landmarks
    for idx, landmark in enumerate(landmarks):
        print(f"Landmark {idx}: x={landmark.x:.3f}, y={landmark.y:.3f}, z={landmark.z:.3f}")
```

---

## 🎥 Video Processing Code Templates

### Basic Video Loader Class
```python
import cv2
import numpy as np
from typing import Iterator, Optional, Dict

class VideoLoader:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = None
        self.metadata = {}
        
    def load_video(self) -> bool:
        """Load video and extract metadata"""
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            return False
            
        self.metadata = {
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
            'total_frames': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration': self.cap.get(cv2.CAP_PROP_FRAME_COUNT) / self.cap.get(cv2.CAP_PROP_FPS)
        }
        return True
        
    def extract_frames(self) -> Iterator[np.ndarray]:
        """Yield frames one by one"""
        if not self.cap:
            self.load_video()
            
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame
            
    def get_metadata(self) -> Dict:
        """Return video metadata"""
        return self.metadata
        
    def __del__(self):
        if self.cap:
            self.cap.release()
```

### Batch Frame Processing
```python
def process_video_batch(video_path: str, batch_size: int = 30):
    """Process video in batches for efficiency"""
    cap = cv2.VideoCapture(video_path)
    
    batch = []
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        batch.append(frame)
        frame_count += 1
        
        if len(batch) >= batch_size:
            # Process batch
            yield batch, frame_count - len(batch)
            batch = []
    
    # Process remaining frames
    if batch:
        yield batch, frame_count - len(batch)
    
    cap.release()
```

---

## 💾 Data Export Templates

### CSV Export Function
```python
import pandas as pd
from typing import List, Dict

def export_pose_to_csv(pose_data: List[Dict], output_path: str):
    """Export pose data to CSV format"""
    # Create DataFrame
    df = pd.DataFrame(pose_data)
    
    # Ensure consistent column order
    columns = ['frame_id', 'timestamp', 'landmark_id', 'landmark_name', 
               'x', 'y', 'z', 'visibility', 'confidence']
    
    # Reorder columns if they exist
    existing_cols = [col for col in columns if col in df.columns]
    df = df[existing_cols]
    
    # Save to CSV
    df.to_csv(output_path, index=False, float_format='%.6f')
    print(f"Saved {len(df)} pose measurements to {output_path}")
```

### Structured Data Collection
```python
def extract_pose_data(results, frame_id: int, fps: float) -> List[Dict]:
    """Extract pose data from MediaPipe results"""
    pose_data = []
    
    if not results.pose_landmarks:
        return pose_data
    
    timestamp = frame_id / fps
    landmarks = results.pose_landmarks.landmark
    
    # Landmark names (abbreviated list)
    landmark_names = {
        0: "nose", 11: "left_shoulder", 12: "right_shoulder",
        13: "left_elbow", 14: "right_elbow", 15: "left_wrist", 
        16: "right_wrist", 23: "left_hip", 24: "right_hip",
        25: "left_knee", 26: "right_knee", 27: "left_ankle",
        28: "right_ankle"
    }
    
    for idx, landmark in enumerate(landmarks):
        pose_data.append({
            'frame_id': frame_id,
            'timestamp': timestamp,
            'landmark_id': idx,
            'landmark_name': landmark_names.get(idx, f"landmark_{idx}"),
            'x': landmark.x,
            'y': landmark.y,
            'z': landmark.z,
            'visibility': landmark.visibility,
            'confidence': landmark.visibility  # MediaPipe uses visibility as confidence
        })
    
    return pose_data
```

---

## 📊 Visualization Code

### Draw Skeleton on Frame
```python
def draw_skeleton(image, landmarks, connections, confidence_threshold=0.5):
    """Draw pose skeleton on image"""
    h, w = image.shape[:2]
    
    # Draw connections
    for connection in connections:
        start_idx = connection[0]
        end_idx = connection[1]
        
        if (landmarks[start_idx].visibility > confidence_threshold and
            landmarks[end_idx].visibility > confidence_threshold):
            
            start_point = (int(landmarks[start_idx].x * w), 
                          int(landmarks[start_idx].y * h))
            end_point = (int(landmarks[end_idx].x * w), 
                        int(landmarks[end_idx].y * h))
            
            cv2.line(image, start_point, end_point, (0, 255, 0), 2)
    
    # Draw landmarks
    for landmark in landmarks:
        if landmark.visibility > confidence_threshold:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)
    
    return image
```

### Create Overlay Video
```python
def create_overlay_video(input_video: str, pose_data: pd.DataFrame, output_video: str):
    """Create video with pose overlay"""
    cap = cv2.VideoCapture(input_video)
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    frame_id = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Get pose data for this frame
        frame_data = pose_data[pose_data['frame_id'] == frame_id]
        
        # Draw skeleton if data exists
        if not frame_data.empty:
            # Convert DataFrame to landmarks format
            # ... (drawing logic here)
            pass
        
        out.write(frame)
        frame_id += 1
    
    cap.release()
    out.release()
```

---

## 📈 Analysis Functions

### Calculate Joint Angles
```python
import numpy as np

def calculate_angle(p1, p2, p3):
    """Calculate angle between three points"""
    # Create vectors
    v1 = np.array([p1.x - p2.x, p1.y - p2.y, p1.z - p2.z])
    v2 = np.array([p3.x - p2.x, p3.y - p2.y, p3.z - p2.z])
    
    # Calculate angle
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
    
    return np.degrees(angle)

def extract_key_angles(landmarks):
    """Extract biomechanically relevant angles"""
    angles = {}
    
    # Right elbow angle (shoulder-elbow-wrist)
    angles['right_elbow'] = calculate_angle(
        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER],
        landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW],
        landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    )
    
    # Right knee angle (hip-knee-ankle)
    angles['right_knee'] = calculate_angle(
        landmarks[mp_pose.PoseLandmark.RIGHT_HIP],
        landmarks[mp_pose.PoseLandmark.RIGHT_KNEE],
        landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]
    )
    
    return angles
```

### Basic Statistics
```python
def calculate_detection_stats(pose_data: pd.DataFrame, total_frames: int) -> Dict:
    """Calculate detection statistics"""
    detected_frames = pose_data['frame_id'].nunique()
    
    stats = {
        'total_frames': total_frames,
        'detected_frames': detected_frames,
        'detection_rate': detected_frames / total_frames,
        'average_confidence': pose_data['confidence'].mean(),
        'min_confidence': pose_data['confidence'].min(),
        'max_confidence': pose_data['confidence'].max(),
        'landmarks_per_frame': len(pose_data) / detected_frames if detected_frames > 0 else 0
    }
    
    return stats
```

---

## 🛠️ Utility Functions

### Progress Tracking
```python
from tqdm import tqdm

def process_with_progress(video_path: str):
    """Process video with progress bar"""
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    with tqdm(total=total_frames, desc="Processing frames") as pbar:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame here
            # ...
            
            pbar.update(1)
    
    cap.release()
```

### Error Handling
```python
class PoseEstimationError(Exception):
    """Custom exception for pose estimation errors"""
    pass

def validate_video_file(video_path: str) -> bool:
    """Validate video file before processing"""
    import os
    
    # Check file exists
    if not os.path.exists(video_path):
        raise PoseEstimationError(f"Video file not found: {video_path}")
    
    # Check file size
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
    if file_size > 500:
        raise PoseEstimationError(f"Video file too large: {file_size:.1f}MB (max 500MB)")
    
    # Check format
    valid_formats = ['.mp4', '.avi', '.mov', '.wmv']
    ext = os.path.splitext(video_path)[1].lower()
    if ext not in valid_formats:
        raise PoseEstimationError(f"Unsupported video format: {ext}")
    
    return True
```

---

## 🔧 Configuration Template

### config.py
```python
class Config:
    """Configuration settings for pose estimation"""
    
    # Model settings
    MODEL_COMPLEXITY = 1  # 0=lite, 1=full, 2=heavy
    MIN_DETECTION_CONFIDENCE = 0.5
    MIN_TRACKING_CONFIDENCE = 0.5
    
    # Processing settings
    BATCH_SIZE = 30
    SKIP_FRAMES = 1  # Process every Nth frame
    MAX_VIDEO_DURATION = 600  # seconds (10 minutes)
    
    # Output settings
    OUTPUT_FPS = 30
    OVERLAY_COLOR = (0, 255, 0)  # Green
    LANDMARK_COLOR = (0, 0, 255)  # Red
    LINE_THICKNESS = 2
    
    # Quality thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.3
    SMOOTHING_WINDOW = 5
    
    # File limits
    MAX_FILE_SIZE_MB = 500
    SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.wmv']
```

---

## 📝 Common Issues & Solutions

### Issue: Low Detection Rate
```python
# Solution: Adjust confidence thresholds
pose = mp_pose.Pose(
    min_detection_confidence=0.3,  # Lower threshold
    min_tracking_confidence=0.3,
    model_complexity=2  # Use more complex model
)
```

### Issue: Memory Error with Long Videos
```python
# Solution: Process in chunks
def process_large_video(video_path, chunk_size=1000):
    cap = cv2.VideoCapture(video_path)
    chunk_data = []
    
    for frame_id in range(int(cap.get(cv2.CAP_PROP_FRAME_COUNT))):
        ret, frame = cap.read()
        if not ret:
            break
            
        # Process frame
        data = process_frame(frame, frame_id)
        chunk_data.extend(data)
        
        # Save chunk when it gets large
        if len(chunk_data) > chunk_size:
            save_chunk(chunk_data)
            chunk_data = []
    
    # Save remaining data
    if chunk_data:
        save_chunk(chunk_data)
```

### Issue: Noisy Landmark Data
```python
# Solution: Apply smoothing
def smooth_landmarks(df, window_size=5):
    """Apply rolling average to reduce noise"""
    numeric_cols = ['x', 'y', 'z']
    
    for col in numeric_cols:
        df[f'{col}_smooth'] = df.groupby('landmark_id')[col].transform(
            lambda x: x.rolling(window_size, center=True, min_periods=1).mean()
        )
    
    return df
```

---

**Last Updated**: [Date]