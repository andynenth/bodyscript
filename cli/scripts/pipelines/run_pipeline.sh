#!/bin/bash
set -e  # Exit on error

echo "🎬 Starting automated pose detection pipeline..."
echo "============================================="

# Step 1: Check if pose data exists
if [ ! -f "creative_output/dance_poses.csv" ]; then
    echo "📹 Running pose detection..."
    ./run_creative.sh video/dance.mp4
    if [ $? -ne 0 ]; then
        echo "❌ Pose detection failed"
        exit 1
    fi
else
    echo "✓ Pose data already exists (creative_output/dance_poses.csv)"
fi

# Step 2: Check if overlay video exists
if [ ! -f "creative_output/dance_skeleton_overlay.mp4" ]; then
    echo "🎥 Creating skeleton overlay..."
    python create_skeleton_video.py
    if [ $? -ne 0 ]; then
        echo "❌ Skeleton overlay creation failed"
        exit 1
    fi
else
    echo "✓ Overlay video already exists (creative_output/dance_skeleton_overlay.mp4)"
fi

# Step 3: Extract validation frames
echo "📸 Extracting first frame for validation..."
mkdir -p frames_validation
python extract_frames.py creative_output/dance_skeleton_overlay.mp4 \
    --output frames_validation \
    --end 1 \
    --prefix validation

if [ $? -ne 0 ]; then
    echo "❌ Frame extraction failed"
    exit 1
fi

# Step 4: Auto-validate detection quality
echo ""
echo "🔍 Running automatic validation..."
echo "-----------------------------------"

python -c "
import pandas as pd
import sys

try:
    # Load pose data
    df = pd.read_csv('creative_output/dance_poses.csv')
    frame_0 = df[df['frame_id'] == 0]

    # Calculate metrics
    landmarks_found = len(frame_0)
    total_landmarks = 33

    if landmarks_found > 0:
        avg_confidence = frame_0['visibility'].mean()
        min_confidence = frame_0['visibility'].min()
        max_confidence = frame_0['visibility'].max()

        # Check feet specifically (common failure point)
        feet_ids = [29, 30, 31, 32]
        feet_data = frame_0[frame_0['landmark_id'].isin(feet_ids)]
        feet_detected = len(feet_data) > 0
        feet_visibility = feet_data['visibility'].mean() if feet_detected else 0

        # Check hands
        hand_ids = [15, 16, 17, 18, 19, 20, 21, 22]
        hand_data = frame_0[frame_0['landmark_id'].isin(hand_ids)]
        hands_detected = len(hand_data) > 0
        hands_visibility = hand_data['visibility'].mean() if hands_detected else 0
    else:
        avg_confidence = 0
        min_confidence = 0
        max_confidence = 0
        feet_detected = False
        feet_visibility = 0
        hands_detected = False
        hands_visibility = 0

    # Display metrics
    print(f'📊 Detection Metrics (Frame 0):')
    print(f'  • Landmarks detected: {landmarks_found}/{total_landmarks}')
    print(f'  • Average confidence: {avg_confidence:.2%}')
    print(f'  • Confidence range: {min_confidence:.2%} - {max_confidence:.2%}')
    print(f'  • Feet detected: {\"✅\" if feet_detected else \"❌\"} (visibility: {feet_visibility:.2%})')
    print(f'  • Hands detected: {\"✅\" if hands_detected else \"❌\"} (visibility: {hands_visibility:.2%})')
    print()

    # Determine quality and action
    if landmarks_found == total_landmarks and avg_confidence > 0.5:
        print('✅ VALIDATION PASSED - Detection quality is GOOD')
        print('   Ready for visual optimization')
        sys.exit(0)  # Success - proceed to optimization
    elif landmarks_found >= 25 and avg_confidence > 0.3:
        print('⚠️  VALIDATION WARNING - Detection quality is MODERATE')
        print('   Some landmarks missing or low confidence')
        print('   Optimization recommended but proceeding...')
        sys.exit(0)  # Proceed with caution
    else:
        print('❌ VALIDATION FAILED - Detection quality is POOR')
        print(f'   Only {landmarks_found}/{total_landmarks} landmarks detected')
        print(f'   Average confidence too low: {avg_confidence:.2%}')
        print('   Need to fix detection parameters first!')
        sys.exit(1)  # Failure - need to fix detection

except Exception as e:
    print(f'❌ Error during validation: {e}')
    sys.exit(1)
"

VALIDATION_RESULT=$?

# Step 5: Based on validation result, take appropriate action
echo ""
echo "============================================="
if [ $VALIDATION_RESULT -eq 0 ]; then
    echo "🎨 Detection validated! Creating optimized version..."
    echo ""

    # Create optimized version with smooth preset
    python create_skeleton_video_optimized.py \
        --video video/dance.mp4 \
        --csv creative_output/dance_poses.csv \
        --output creative_output/dance_skeleton_optimized.mp4 \
        --preset smooth \
        --style "Smooth Animation"

    if [ $? -eq 0 ]; then
        echo ""
        echo "============================================="
        echo "✅ PIPELINE COMPLETE!"
        echo "============================================="
        echo "📁 Output files:"
        echo "   • Original overlay: creative_output/dance_skeleton_overlay.mp4"
        echo "   • Optimized version: creative_output/dance_skeleton_optimized.mp4"
        echo "   • Validation frame: frames_validation/validation_000001.png"
        echo ""
        echo "💡 Next steps:"
        echo "   • View the optimized video to check quality"
        echo "   • Try other presets: --preset glow, trail, or minimal"
        echo "   • Adjust smoothing: --smoothing 10 (more smooth)"
    else
        echo "⚠️  Optimization failed, but basic overlay is available"
    fi
else
    echo "🔧 Detection needs improvement. Running parameter optimization..."
    echo ""

    # Run detection optimization to find better parameters
    python optimize_pose_detection.py video/dance.mp4 --output detection_tests

    echo ""
    echo "============================================="
    echo "⚠️  MANUAL INTERVENTION REQUIRED"
    echo "============================================="
    echo "The optimizer has tested different parameters."
    echo "Review the results above and:"
    echo ""
    echo "1. Update core/config.py with recommended settings:"
    echo "   MODEL_COMPLEXITY = <recommended value>"
    echo "   MIN_DETECTION_CONFIDENCE = <recommended value>"
    echo "   MIN_TRACKING_CONFIDENCE = <recommended value>"
    echo ""
    echo "2. Delete existing output to force re-processing:"
    echo "   rm creative_output/dance_poses.csv"
    echo "   rm creative_output/dance_skeleton_overlay.mp4"
    echo ""
    echo "3. Re-run this pipeline:"
    echo "   ./run_pipeline.sh"
    echo ""
    echo "📁 Test images saved in: detection_tests/"
    echo "   Review these to see which settings worked best"
fi

echo "============================================="
echo "🏁 Pipeline execution finished"
echo "============================================="