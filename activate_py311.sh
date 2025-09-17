#!/bin/bash
# Convenience script to activate Python 3.11 environment with MediaPipe

echo "Activating Python 3.11 environment with MediaPipe..."
source venv_py311/bin/activate
echo "✅ Environment activated!"
echo "Python version: $(python --version)"
echo "MediaPipe available: $(python -c 'import mediapipe; print("Yes, version", mediapipe.__version__)' 2>/dev/null || echo "No")"
echo ""
echo "Ready to use real pose detection!"
echo "Try: python quick_test.py"