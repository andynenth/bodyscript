"""Test pose detection with webcam in real-time."""

import cv2
import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import PoseDetector, Config


def test_webcam_pose():
    """Test pose detection with webcam."""
    print("Starting webcam pose detection...")
    print("Press ESC to quit")
    print("=" * 60)
    
    # Initialize pose detector
    detector = PoseDetector(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    # Start webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Cannot open webcam")
        print("Try changing the camera index (0, 1, 2, etc.)")
        return
        
    frame_count = 0
    detected_count = 0
    
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Failed to read from webcam")
            continue
            
        # Flip image for selfie view
        image = cv2.flip(image, 1)
        h, w = image.shape[:2]
        
        # Detect pose
        result = detector.process_single_frame(image, frame_count)
        
        # Draw the pose
        if result.detected and result.landmarks:
            detected_count += 1
            
            # Draw connections
            for connection in Config.POSE_CONNECTIONS:
                start_idx, end_idx = connection
                
                if start_idx < len(result.landmarks) and end_idx < len(result.landmarks):
                    start_lm = result.landmarks[start_idx]
                    end_lm = result.landmarks[end_idx]
                    
                    if (start_lm.visibility > Config.MIN_CONFIDENCE_THRESHOLD and
                        end_lm.visibility > Config.MIN_CONFIDENCE_THRESHOLD):
                        
                        start_point = (int(start_lm.x * w), int(start_lm.y * h))
                        end_point = (int(end_lm.x * w), int(end_lm.y * h))
                        
                        cv2.line(image, start_point, end_point, (0, 255, 0), 2)
                        
            # Draw landmarks
            for landmark in result.landmarks:
                if landmark.visibility > Config.MIN_CONFIDENCE_THRESHOLD:
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    cv2.circle(image, (x, y), 5, (0, 0, 255), -1)
                    
            # Show detection status
            cv2.putText(image, "Pose Detected!", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(image, "No Pose Found", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                       
        # Show frame info
        frame_count += 1
        info_text = f"Frame: {frame_count} | Detected: {detected_count} ({detected_count/frame_count*100:.1f}%)"
        cv2.putText(image, info_text, (10, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                   
        # Display the image
        cv2.imshow('Pose Detection Test', image)
        
        # Check for ESC key
        if cv2.waitKey(5) & 0xFF == 27:
            break
            
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n✅ Processed {frame_count} frames")
    print(f"✅ Detected pose in {detected_count} frames ({detected_count/frame_count*100:.1f}%)")
    
    # Note about MediaPipe
    if not detector.mp_available:
        print("\n⚠️  Note: MediaPipe not available - using placeholder detection")
        print("   For real pose detection, use Python 3.8-3.11 with MediaPipe")


if __name__ == "__main__":
    test_webcam_pose()