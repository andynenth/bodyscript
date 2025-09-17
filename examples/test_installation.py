"""Test if all dependencies are installed correctly."""

import sys
import warnings


def test_dependencies():
    """Test all required dependencies."""
    print("Testing BodyScript dependencies...")
    print("=" * 60)
    
    all_good = True
    
    # Test OpenCV
    try:
        import cv2
        print(f"✅ OpenCV installed: {cv2.__version__}")
    except ImportError:
        print("❌ OpenCV not installed")
        all_good = False
        
    # Test NumPy
    try:
        import numpy as np
        print(f"✅ NumPy installed: {np.__version__}")
    except ImportError:
        print("❌ NumPy not installed")
        all_good = False
        
    # Test Pandas
    try:
        import pandas as pd
        print(f"✅ Pandas installed: {pd.__version__}")
    except ImportError:
        print("❌ Pandas not installed")
        all_good = False
        
    # Test Matplotlib
    try:
        import matplotlib
        print(f"✅ Matplotlib installed: {matplotlib.__version__}")
    except ImportError:
        print("❌ Matplotlib not installed")
        all_good = False
        
    # Test tqdm
    try:
        import tqdm
        print(f"✅ tqdm installed: {tqdm.__version__}")
    except ImportError:
        print("❌ tqdm not installed")
        all_good = False
        
    # Test MediaPipe (special case)
    try:
        import mediapipe as mp
        print(f"✅ MediaPipe installed: {mp.__version__}")
    except ImportError:
        print("⚠️  MediaPipe not installed (not available for Python 3.13)")
        print("   Using placeholder implementation for development")
        
    print("=" * 60)
    
    # Python version check
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major == 3 and python_version.minor >= 13:
        print("\n⚠️  Note: You're using Python 3.13+")
        print("   MediaPipe is not available for this version.")
        print("   The system will use placeholder pose detection.")
        print("   For production use, please use Python 3.8-3.11.")
        
    # Test core modules
    print("\nTesting core modules...")
    try:
        # Add parent directory to path
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from core import VideoLoader, PoseDetector, DataExporter, Config
        print("✅ Core modules imported successfully")
        
        from utils.visualization import PoseVisualizer
        print("✅ Visualization module imported successfully")
        
        from simple_pose_analyzer import SimplePoseAnalyzer
        print("✅ SimplePoseAnalyzer imported successfully")
        
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        all_good = False
        
    print("=" * 60)
    
    if all_good:
        print("\n🎉 All dependencies installed successfully!")
        print("You're ready to start using BodyScript!")
    else:
        print("\n⚠️  Some dependencies are missing!")
        print("Please install missing dependencies with:")
        print("  pip install opencv-python pandas numpy matplotlib tqdm")
        
    return all_good


if __name__ == "__main__":
    test_dependencies()