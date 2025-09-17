"""
Holistic Pose Detection Module - Full body, hands, and face tracking
Implements MediaPipe Holistic for comprehensive 543-landmark detection
"""

import mediapipe as mp
import numpy as np
import cv2
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass
import pandas as pd
from tqdm import tqdm
import time
import sys
import os

# Add parent directory to path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.pose_detector import PoseDetectorInterface, PoseResults


@dataclass
class HolisticResults:
    """Results from holistic detection including body, hands, and face."""
    frame_id: int
    timestamp: float
    pose_landmarks: Optional[Any] = None  # 33 landmarks
    pose_world_landmarks: Optional[Any] = None  # 33 world landmarks
    left_hand_landmarks: Optional[Any] = None  # 21 landmarks
    right_hand_landmarks: Optional[Any] = None  # 21 landmarks
    face_landmarks: Optional[Any] = None  # 468 landmarks

    def get_total_landmarks_count(self) -> int:
        """Calculate total number of detected landmarks."""
        count = 0
        if self.pose_landmarks:
            count += 33
        if self.left_hand_landmarks:
            count += 21
        if self.right_hand_landmarks:
            count += 21
        if self.face_landmarks:
            count += 468
        return count

    def to_dataframe(self) -> pd.DataFrame:
        """Convert holistic results to pandas DataFrame."""
        rows = []

        # Process pose landmarks (33 points)
        if self.pose_landmarks:
            for idx, landmark in enumerate(self.pose_landmarks.landmark):
                rows.append({
                    'frame_id': self.frame_id,
                    'timestamp': self.timestamp,
                    'landmark_type': 'pose',
                    'landmark_id': idx,
                    'landmark_name': POSE_LANDMARK_NAMES.get(idx, f'pose_{idx}'),
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z if hasattr(landmark, 'z') else 0,
                    'visibility': landmark.visibility if hasattr(landmark, 'visibility') else 1.0,
                    'presence': landmark.presence if hasattr(landmark, 'presence') else 1.0
                })

        # Process left hand landmarks (21 points)
        if self.left_hand_landmarks:
            for idx, landmark in enumerate(self.left_hand_landmarks.landmark):
                rows.append({
                    'frame_id': self.frame_id,
                    'timestamp': self.timestamp,
                    'landmark_type': 'left_hand',
                    'landmark_id': idx + 33,  # Offset by pose landmarks
                    'landmark_name': f'left_hand_{HAND_LANDMARK_NAMES.get(idx, str(idx))}',
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z if hasattr(landmark, 'z') else 0,
                    'visibility': 1.0,
                    'presence': landmark.presence if hasattr(landmark, 'presence') else 1.0
                })

        # Process right hand landmarks (21 points)
        if self.right_hand_landmarks:
            for idx, landmark in enumerate(self.right_hand_landmarks.landmark):
                rows.append({
                    'frame_id': self.frame_id,
                    'timestamp': self.timestamp,
                    'landmark_type': 'right_hand',
                    'landmark_id': idx + 54,  # Offset by pose + left hand
                    'landmark_name': f'right_hand_{HAND_LANDMARK_NAMES.get(idx, str(idx))}',
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z if hasattr(landmark, 'z') else 0,
                    'visibility': 1.0,
                    'presence': landmark.presence if hasattr(landmark, 'presence') else 1.0
                })

        # Process face landmarks (468 points) - sample every 10th for performance
        if self.face_landmarks:
            for idx, landmark in enumerate(self.face_landmarks.landmark):
                # Sample face landmarks for manageable data size
                if idx % 10 == 0 or idx in IMPORTANT_FACE_LANDMARKS:
                    rows.append({
                        'frame_id': self.frame_id,
                        'timestamp': self.timestamp,
                        'landmark_type': 'face',
                        'landmark_id': idx + 75,  # Offset by pose + hands
                        'landmark_name': f'face_{idx}',
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z if hasattr(landmark, 'z') else 0,
                        'visibility': 1.0,
                        'presence': landmark.presence if hasattr(landmark, 'presence') else 1.0
                    })

        return pd.DataFrame(rows) if rows else pd.DataFrame()


# Landmark name mappings
POSE_LANDMARK_NAMES = {
    0: 'nose', 1: 'left_eye_inner', 2: 'left_eye', 3: 'left_eye_outer',
    4: 'right_eye_inner', 5: 'right_eye', 6: 'right_eye_outer',
    7: 'left_ear', 8: 'right_ear', 9: 'mouth_left', 10: 'mouth_right',
    11: 'left_shoulder', 12: 'right_shoulder', 13: 'left_elbow', 14: 'right_elbow',
    15: 'left_wrist', 16: 'right_wrist', 17: 'left_pinky', 18: 'right_pinky',
    19: 'left_index', 20: 'right_index', 21: 'left_thumb', 22: 'right_thumb',
    23: 'left_hip', 24: 'right_hip', 25: 'left_knee', 26: 'right_knee',
    27: 'left_ankle', 28: 'right_ankle', 29: 'left_heel', 30: 'right_heel',
    31: 'left_foot_index', 32: 'right_foot_index'
}

HAND_LANDMARK_NAMES = {
    0: 'wrist', 1: 'thumb_cmc', 2: 'thumb_mcp', 3: 'thumb_ip', 4: 'thumb_tip',
    5: 'index_mcp', 6: 'index_pip', 7: 'index_dip', 8: 'index_tip',
    9: 'middle_mcp', 10: 'middle_pip', 11: 'middle_dip', 12: 'middle_tip',
    13: 'ring_mcp', 14: 'ring_pip', 15: 'ring_dip', 16: 'ring_tip',
    17: 'pinky_mcp', 18: 'pinky_pip', 19: 'pinky_dip', 20: 'pinky_tip'
}

# Important face landmarks to always include
IMPORTANT_FACE_LANDMARKS = {
    # Eye landmarks
    33, 133, 157, 158, 159, 160, 161, 173,
    263, 362, 386, 387, 388, 389, 390, 398,
    # Mouth landmarks
    13, 14, 78, 80, 81, 82, 308, 310, 311, 312,
    # Nose landmarks
    1, 2, 4, 5, 6, 19, 20, 125, 141, 235, 236
}


class HolisticPoseDetector(PoseDetectorInterface):
    """
    Enhanced pose detector using MediaPipe Holistic for comprehensive tracking.
    Detects body pose (33 landmarks), hands (21x2 landmarks), and face (468 landmarks).
    """

    def __init__(self, mode: str = 'RESEARCH', **config):
        """Initialize the holistic detector with specified configuration."""
        super().__init__(mode, **config)

        # Initialize MediaPipe Holistic
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Configure holistic model
        self.holistic = self.mp_holistic.Holistic(
            static_image_mode=config.get('static_image_mode', False),
            model_complexity=config.get('model_complexity', 2),  # Higher complexity for research
            smooth_landmarks=config.get('smooth_landmarks', True),
            enable_segmentation=config.get('enable_segmentation', False),
            smooth_segmentation=config.get('smooth_segmentation', False),
            refine_face_landmarks=config.get('refine_face_landmarks', True),
            min_detection_confidence=config.get('min_detection_confidence', 0.5),
            min_tracking_confidence=config.get('min_tracking_confidence', 0.5)
        )

        # Statistics tracking
        self.stats = {
            'frames_processed': 0,
            'pose_detections': 0,
            'left_hand_detections': 0,
            'right_hand_detections': 0,
            'face_detections': 0,
            'total_landmarks_detected': 0,
            'processing_times': []
        }

    def detect_single_frame(self, frame: np.ndarray) -> HolisticResults:
        """
        Process a single frame with holistic detection.

        Args:
            frame: Input frame as numpy array (BGR format)

        Returns:
            HolisticResults containing all detected landmarks
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process with holistic model
        results = self.holistic.process(rgb_frame)

        # Create holistic results
        holistic_results = HolisticResults(
            frame_id=self.stats['frames_processed'],
            timestamp=self.stats['frames_processed'] / 30.0,  # Assume 30 fps
            pose_landmarks=results.pose_landmarks,
            pose_world_landmarks=results.pose_world_landmarks,
            left_hand_landmarks=results.left_hand_landmarks,
            right_hand_landmarks=results.right_hand_landmarks,
            face_landmarks=results.face_landmarks
        )

        # Update statistics
        self.stats['frames_processed'] += 1
        if results.pose_landmarks:
            self.stats['pose_detections'] += 1
        if results.left_hand_landmarks:
            self.stats['left_hand_detections'] += 1
        if results.right_hand_landmarks:
            self.stats['right_hand_detections'] += 1
        if results.face_landmarks:
            self.stats['face_detections'] += 1
        self.stats['total_landmarks_detected'] += holistic_results.get_total_landmarks_count()

        return holistic_results

    def detect_poses(self, frames: List[np.ndarray], progress_bar: bool = True) -> List[HolisticResults]:
        """
        Process multiple frames with holistic detection.

        Args:
            frames: List of frames to process
            progress_bar: Whether to show progress bar

        Returns:
            List of HolisticResults for each frame
        """
        results = []
        iterator = tqdm(frames, desc="Holistic detection") if progress_bar else frames

        for frame_idx, frame in enumerate(iterator):
            start_time = time.time()

            # Detect holistic landmarks
            frame_results = self.detect_single_frame(frame)
            frame_results.frame_id = frame_idx
            frame_results.timestamp = frame_idx / 30.0  # Assume 30 fps

            results.append(frame_results)

            # Track processing time
            processing_time = time.time() - start_time
            self.stats['processing_times'].append(processing_time)

            # Update progress bar with statistics
            if progress_bar and frame_idx % 10 == 0:
                avg_time = np.mean(self.stats['processing_times'][-100:])
                detection_rate = self.stats['pose_detections'] / max(1, self.stats['frames_processed'])
                iterator.set_postfix({
                    'fps': f"{1/avg_time:.1f}",
                    'detection_rate': f"{detection_rate:.2%}",
                    'landmarks': self.stats['total_landmarks_detected'] // max(1, self.stats['frames_processed'])
                })

        return results

    def filter_confidence(self, results: List[HolisticResults], threshold: float = 0.5) -> List[HolisticResults]:
        """
        Filter results based on confidence threshold.

        Args:
            results: List of detection results
            threshold: Minimum confidence threshold

        Returns:
            Filtered results
        """
        filtered_results = []

        for result in results:
            # Check pose confidence
            keep_result = False

            if result.pose_landmarks:
                # Calculate average visibility for pose
                visibilities = [lm.visibility for lm in result.pose_landmarks.landmark
                               if hasattr(lm, 'visibility')]
                if visibilities and np.mean(visibilities) >= threshold:
                    keep_result = True

            # For hands and face, presence is more relevant than visibility
            if result.left_hand_landmarks or result.right_hand_landmarks:
                keep_result = True  # Hands detected means good confidence

            if result.face_landmarks:
                keep_result = True  # Face detected means good confidence

            if keep_result:
                filtered_results.append(result)
            else:
                # Create empty result to maintain frame alignment
                filtered_results.append(HolisticResults(
                    frame_id=result.frame_id,
                    timestamp=result.timestamp
                ))

        return filtered_results

    def draw_landmarks(self, frame: np.ndarray, results: HolisticResults,
                      draw_pose: bool = True, draw_hands: bool = True,
                      draw_face: bool = False) -> np.ndarray:
        """
        Draw detected landmarks on the frame.

        Args:
            frame: Input frame
            results: Detection results
            draw_pose: Whether to draw pose landmarks
            draw_hands: Whether to draw hand landmarks
            draw_face: Whether to draw face landmarks (disabled by default for performance)

        Returns:
            Frame with drawn landmarks
        """
        annotated_frame = frame.copy()

        # Draw pose landmarks
        if draw_pose and results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                results.pose_landmarks,
                self.mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
            )

        # Draw hand landmarks
        if draw_hands:
            if results.left_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    results.left_hand_landmarks,
                    self.mp_holistic.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )

            if results.right_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    results.right_hand_landmarks,
                    self.mp_holistic.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )

        # Draw face landmarks (optional - can be performance intensive)
        if draw_face and results.face_landmarks:
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                results.face_landmarks,
                self.mp_holistic.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
            )

        # Add statistics overlay
        detection_info = []
        if results.pose_landmarks:
            detection_info.append("Body")
        if results.left_hand_landmarks:
            detection_info.append("L-Hand")
        if results.right_hand_landmarks:
            detection_info.append("R-Hand")
        if results.face_landmarks:
            detection_info.append("Face")

        if detection_info:
            text = f"Detected: {', '.join(detection_info)} ({results.get_total_landmarks_count()} pts)"
            cv2.putText(annotated_frame, text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        return annotated_frame

    def get_statistics(self) -> Dict:
        """
        Get comprehensive detection statistics.

        Returns:
            Dictionary containing detection statistics
        """
        stats = self.stats.copy()

        # Calculate rates
        if stats['frames_processed'] > 0:
            stats['pose_detection_rate'] = stats['pose_detections'] / stats['frames_processed']
            stats['left_hand_detection_rate'] = stats['left_hand_detections'] / stats['frames_processed']
            stats['right_hand_detection_rate'] = stats['right_hand_detections'] / stats['frames_processed']
            stats['face_detection_rate'] = stats['face_detections'] / stats['frames_processed']
            stats['avg_landmarks_per_frame'] = stats['total_landmarks_detected'] / stats['frames_processed']

        # Calculate timing stats
        if stats['processing_times']:
            stats['avg_processing_time'] = np.mean(stats['processing_times'])
            stats['max_processing_time'] = np.max(stats['processing_times'])
            stats['min_processing_time'] = np.min(stats['processing_times'])
            stats['processing_fps'] = 1.0 / stats['avg_processing_time'] if stats['avg_processing_time'] > 0 else 0

        return stats

    def __del__(self):
        """Clean up resources."""
        if hasattr(self, 'holistic'):
            self.holistic.close()


def test_holistic_detector():
    """Test the holistic detector with a sample video or webcam."""
    print("\n=== Testing Holistic Pose Detector ===\n")

    # Initialize detector
    detector = HolisticPoseDetector(mode='RESEARCH')

    # Try to use webcam for testing
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Webcam not available. Please test with a video file.")
        return

    print("Press 'q' to quit the test.")
    print("Detecting: Body (33 pts) + Hands (42 pts) + Face (468 pts) = 543 total landmarks\n")

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Detect holistic landmarks
        results = detector.detect_single_frame(frame)

        # Draw landmarks
        annotated_frame = detector.draw_landmarks(frame, results, draw_face=False)

        # Show statistics
        stats_text = f"Frame: {frame_count} | Total Landmarks: {results.get_total_landmarks_count()}"
        cv2.putText(annotated_frame, stats_text, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Display
        cv2.imshow('Holistic Detection Test', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_count += 1

        # Stop after 300 frames for testing
        if frame_count >= 300:
            break

    cap.release()
    cv2.destroyAllWindows()

    # Print final statistics
    stats = detector.get_statistics()
    print(f"\n=== Detection Statistics ===")
    print(f"Frames processed: {stats['frames_processed']}")
    print(f"Pose detection rate: {stats.get('pose_detection_rate', 0):.2%}")
    print(f"Left hand detection rate: {stats.get('left_hand_detection_rate', 0):.2%}")
    print(f"Right hand detection rate: {stats.get('right_hand_detection_rate', 0):.2%}")
    print(f"Face detection rate: {stats.get('face_detection_rate', 0):.2%}")
    print(f"Average landmarks per frame: {stats.get('avg_landmarks_per_frame', 0):.1f}")
    print(f"Processing speed: {stats.get('processing_fps', 0):.1f} fps")


if __name__ == "__main__":
    test_holistic_detector()